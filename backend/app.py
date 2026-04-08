"""
Flask 后端 - 接收前端请求、查库定位、下发 ROS2 任务、生成取药记录
"""
import json
import os
import sqlite3
import threading
import time
from datetime import date, datetime
from flask import Flask, request, jsonify

# Model imports
from models.drug import Drug
from models.order import Order
from models.approval import Approval

# Utility imports
from utils.database import get_db_connection, init_database, json_serializer, DB_PATH
from utils.ros2_bridge import init_ros2, publish_task, publish_expiry_removal, check_ros2_status, ros2_available, task_publisher
from utils.logger import setup_logger

# Configuration
from config.settings import Config

# ROS2 可选：若环境未配置则跳过发布
# ros2_available and task_publisher are now imported from utils.ros2_bridge




# 启动时尝试初始化 ROS2（后台线程）
_ros_thread = threading.Thread(target=init_ros2, daemon=True)
_ros_thread.start()

# Flask
app = Flask(__name__)

# Port configuration for P1 compatibility
# Using port 8001 to avoid conflicts with common services (5000 for Flask dev, 8000 for Python HTTP server)
# and to ensure compatibility with P1 medical assistant system requirements
# Note: Port configuration is now handled by Config class in config.settings


# CORS：允许前端跨域访问
try:
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})
except ImportError:
    @app.after_request
    def add_cors(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

_expiry_sweep_lock = threading.Lock()
_expiry_bg_started = False
_expiry_bg_lock = threading.Lock()
EXPIRY_SWEEP_INTERVAL_SEC = int(os.environ.get('EXPIRY_SWEEP_INTERVAL_SEC', '3600'))


def _ensure_app_meta(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS app_meta (
            k TEXT PRIMARY KEY,
            v TEXT NOT NULL
        )
    ''')


def run_expiry_sweep() -> dict:
    """
    按本地日期推进「剩余天数」并清理过期品可售库存（同一天只执行一次）。
    基准日由 init_db 写入 app_meta.expiry_sweep_date；旧库无该记录时首次访问仅写入当天不扣减。
    关机多日后再启动会按日期差一次性扣减，避免时间丢失。
    返回本次执行摘要（便于日志/调试）。
    """
    if not os.path.exists(DB_PATH):
        return {'skipped': True, 'reason': 'no database'}

    today = date.today()
    today_s = today.isoformat()

    with _expiry_sweep_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            _ensure_app_meta(conn)
            row = conn.execute(
                "SELECT v FROM app_meta WHERE k = 'expiry_sweep_date'"
            ).fetchone()
            last_s = row[0] if row else None

            if last_s == today_s:
                return {'skipped': True, 'reason': 'already_swept_today', 'date': today_s}

            if last_s is None:
                # 未执行过新版 init_db 的旧库：补上基准日，当日不扣减
                conn.execute(
                    "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
                    (today_s,),
                )
                conn.commit()
                return {'skipped': True, 'reason': 'legacy_baseline_no_init_meta', 'date': today_s}

            try:
                last_d = date.fromisoformat(last_s)
            except ValueError:
                conn.execute(
                    "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
                    (today_s,),
                )
                conn.commit()
                return {'skipped': True, 'reason': 'reset_invalid_last_date', 'date': today_s}

            delta = (today - last_d).days
            if delta <= 0:
                return {'skipped': True, 'reason': 'no_new_day', 'date': today_s}

            conn.execute(
                'UPDATE inventory SET expiry_date = expiry_date - ? WHERE expiry_date > 0',
                (delta,),
            )
            cur = conn.execute(
                '''SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id
                   FROM inventory WHERE expiry_date <= 0 AND quantity > 0'''
            )
            expired_to_remove = [dict(r) for r in cur.fetchall()]

            cur = conn.execute(
                'UPDATE inventory SET quantity = 0 WHERE expiry_date <= 0'
            )
            cleared_rows = cur.rowcount

            conn.execute(
                "INSERT OR REPLACE INTO app_meta (k, v) VALUES ('expiry_sweep_date', ?)",
                (today_s,),
            )
            conn.commit()

            ros_n = 0
            for drug in expired_to_remove:
                publish_expiry_removal(drug, int(drug['quantity']))
                ros_n += 1

            return {
                'success': True, 'ok': True,
                'date': today_s,
                'days_applied': delta,
                'expired_rows_cleared_qty': cleared_rows,
                'expiry_ros_published': ros_n,
            }
        finally:
            conn.close()


def _expiry_sweep_loop():
    while True:
        try:
            summary = run_expiry_sweep()
            if summary.get('ok'):
                print(f'[expiry] 清扫完成: {summary}')
            elif not summary.get('skipped'):
                print(f'[expiry] 清扫结果: {summary}')
        except Exception as e:
            print(f'[expiry] 清扫异常: {e}')
        time.sleep(EXPIRY_SWEEP_INTERVAL_SEC)


def _boot_expiry_worker_once():
    """在「会长期驻留的服务进程」里只启动一条定时清扫线程。"""
    global _expiry_bg_started
    with _expiry_bg_lock:
        if _expiry_bg_started:
            return
        _expiry_bg_started = True
    threading.Thread(target=_expiry_sweep_loop, daemon=True).start()




def query_drug(drug_id: int) -> dict | None:
    conn = get_db_connection()
    try:
        cur = conn.execute(
            'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?',
            (drug_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def validate_and_get_drug(drug_id: int, num: int) -> tuple[dict | None, str | None]:
    """校验药品，返回 (drug_dict, error_msg)。无错时 error_msg 为 None"""
    drug = query_drug(drug_id)
    if not drug:
        return None, f'药品不存在: id={drug_id}'
    if drug['expiry_date'] is not None and drug['expiry_date'] <= 0:
        return None, f'药品已过期: {drug["name"]}'
    if drug['quantity'] < num:
        return None, f'库存不足: {drug["name"]} 库存 {drug["quantity"]}，需求 {num}'
    return drug, None




# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'success': True, 'status': 'ok', 'message': 'backend running', 'ros2': ros2_available})


@app.route('/api/drugs', methods=['GET'])
def list_drugs():
    """Get list of drugs with optional name filtering

    Query parameters:
    - name: Optional partial name filter (case-sensitive)

    Returns:
    - New format: {"success": True, "drugs": [...], "count": N, "filters": {"name": <value>}}
    - Old format (backward compatibility): {"ok": True, "data": [...]}
    """
    name_filter = request.args.get('name')

    conn = get_db_connection()
    try:
        if name_filter is not None:
            # Use LIKE for partial matching
            cur = conn.execute(
                'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE name LIKE ?',
                (f'%{name_filter}%',)
            )
        else:
            cur = conn.execute(
                'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory'
            )

        drugs = [dict(row) for row in cur.fetchall()]

        # Return both new format for P1 compatibility and old format for backward compatibility
        response_data = {
            'success': True,  # New format
            'ok': True,       # Old format for backward compatibility
            'drugs': drugs,   # New format
            'data': drugs,    # Old format for backward compatibility
            'count': len(drugs),
            'filters': {'name': name_filter if name_filter is not None else ''}
        }
        return jsonify(response_data)
    finally:
        conn.close()


@app.route('/api/drugs/<int:drug_id>', methods=['GET'])
def get_drug(drug_id):
    """Get a single drug by ID

    Returns:
    - Success: {"success": True, "drug": {...}}
    - Not found: {"error": True, "message": "...", "code": "DRUG_NOT_FOUND"} with 404 status
    """
    conn = get_db_connection()
    try:
        cur = conn.execute(
            'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?',
            (drug_id,)
        )
        row = cur.fetchone()

        if row is None:
            return jsonify({
                'error': True,
                'message': f'Drug not found: id={drug_id}',
                'code': 'DRUG_NOT_FOUND'
            }), 404

        drug = dict(row)
        return jsonify({
            'success': True,
            'drug': drug
        })
    finally:
        conn.close()


@app.route('/api/order', methods=['POST', 'OPTIONS'])
def order():
    """
    批量取药订单
    接收: [ {"id": 1, "num": 2}, {"id": 2, "num": 1} ]
    流程: 校验 -> 扣减库存 -> 写入 order_log -> 发布 ROS2 任务
    """
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'success': False, 'ok': False, 'error': '请求体必须为 JSON'}), 400

    if not isinstance(data, list):
        data = [data]

    order_data = []
    for item in data:
        drug_id = item.get('id')
        num = item.get('num')
        if drug_id is None or num is None:
            return jsonify({'success': False, 'ok': False, 'error': '每项需包含 id 和 num'}), 400
        try:
            order_data.append((int(drug_id), int(num)))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'ok': False, 'error': 'id 和 num 必须为整数'}), 400

    if not order_data:
        return jsonify({'success': False, 'ok': False, 'error': '药单为空'}), 400

    # 预校验全部
    tasks = []
    for drug_id, num in order_data:
        if num <= 0:
            return jsonify({'success': False, 'ok': False, 'error': f'药品 {drug_id} 数量必须大于 0'}), 400
        drug, err = validate_and_get_drug(drug_id, num)
        if err:
            return jsonify({'success': False, 'ok': False, 'error': err}), 400
        tasks.append((drug_id, num, drug))

    # 全部通过：扣减库存 + 写入 order_log + 发布 ROS2（同一事务）
    conn = get_db_connection()
    try:
        task_ids = []
        for drug_id, num, drug in tasks:
            # 原子扣减库存（WHERE quantity>=num 防止超扣，并发安全）
            cur = conn.execute(
                'UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?',
                (num, drug_id, num)
            )
            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({'success': False, 'ok': False, 'error': f'库存不足: {drug["name"]}，请刷新后重试'}), 400

            cur = conn.execute(
                'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
                ('pending', drug_id, num)
            )
            task_ids.append(cur.lastrowid)
        conn.commit()
        for (drug_id, num, drug), task_id in zip(tasks, task_ids):
            publish_task(task_id, drug, num)
        return jsonify({
            'success': True, 'ok': True,
            'task_ids': task_ids,
            'message': f'已下发 {len(task_ids)} 个取药任务，库存已扣减',
        })
    finally:
        conn.close()


@app.route('/api/pickup', methods=['POST'])
def pickup():
    """
    单条取药（兼容旧接口）
    接收: { "id": 1, "num": 2 }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'success': False, 'ok': False, 'error': '请求体必须为 JSON'}), 400

    drug_id = data.get('id')
    num = data.get('num')
    if drug_id is None or num is None:
        return jsonify({'success': False, 'ok': False, 'error': '缺少 id 或 num'}), 400
    try:
        drug_id, num = int(drug_id), int(num)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'ok': False, 'error': 'id 和 num 必须为整数'}), 400
    if num <= 0:
        return jsonify({'success': False, 'ok': False, 'error': 'num 必须大于 0'}), 400

    drug, err = validate_and_get_drug(drug_id, num)
    if err:
        return jsonify({'success': False, 'ok': False, 'error': err}), 400

    conn = get_db_connection()
    try:
        # 原子扣减库存（防止并发）
        cur = conn.execute(
            'UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?',
            (num, drug_id, num)
        )
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({'success': False, 'ok': False, 'error': f'库存不足或已被占用: {drug["name"]}，请刷新后重试'}), 400

        cur = conn.execute(
            'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
            ('pending', drug_id, num)
        )
        task_id = cur.lastrowid
        conn.commit()
        publish_task(task_id, drug, num)
        return jsonify({
            'success': True, 'ok': True,
            'task_id': task_id,
            'drug_id': drug_id,
            'name': drug['name'],
            'quantity': num,
            'shelve_id': drug['shelve_id'],
            'x': drug['shelf_x'],
            'y': drug['shelf_y'],
        })
    finally:
        conn.close()


@app.route('/api/dispense', methods=['POST'])
def dispense():
    """
    配药端点，用于fill_prescription工具调用
    接收: {
        "prescription_id": "处方ID",
        "patient_name": "患者姓名",
        "drugs": [{"name": "药品名称", "dosage": "剂量", "quantity": 数量}]
    }
    返回: 类似/order端点的订单创建结果
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'ok': False, 'error': '请求体必须为 JSON'}), 400

    prescription_id = data.get('prescription_id')
    patient_name = data.get('patient_name')
    drugs = data.get('drugs')

    if not prescription_id or not patient_name or not drugs:
        return jsonify({
            'success': False,
            'ok': False,
            'error': '缺少必要参数: prescription_id, patient_name, drugs'
        }), 400

    if not isinstance(drugs, list):
        return jsonify({
            'success': False,
            'ok': False,
            'error': 'drugs必须为数组'
        }), 400

    # 转换药品名称到药品ID并验证
    order_items = []
    for drug_item in drugs:
        drug_name = drug_item.get('name')
        quantity = drug_item.get('quantity', 1)

        if not drug_name:
            return jsonify({
                'success': False,
                'ok': False,
                'error': '药品缺少name字段'
            }), 400

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return jsonify({
                    'success': False,
                    'ok': False,
                    'error': f'药品数量必须大于0: {drug_name}'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'ok': False,
                'error': f'药品数量必须为整数: {drug_name}'
            }), 400

        # 查找药品ID
        drug_id = find_drug_id_by_name(drug_name)
        if not drug_id:
            return jsonify({
                'success': False,
                'ok': False,
                'error': f'未找到药品: {drug_name}'
            }), 400

        order_items.append((drug_id, quantity, drug_name))

    # 创建订单（逐个药品处理）
    conn = get_db_connection()
    try:
        task_ids = []
        for drug_id, quantity, drug_name in order_items:
            # 验证药品
            drug, err = validate_and_get_drug(drug_id, quantity)
            if err:
                conn.rollback()
                return jsonify({'success': False, 'ok': False, 'error': err}), 400

            # 原子扣减库存
            cur = conn.execute(
                'UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?',
                (quantity, drug_id, quantity)
            )
            if cur.rowcount == 0:
                conn.rollback()
                return jsonify({
                    'success': False,
                    'ok': False,
                    'error': f'库存不足: {drug_name}，请刷新后重试'
                }), 400

            # 写入order_log
            cur = conn.execute(
                'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
                ('pending', drug_id, quantity)
            )
            task_id = cur.lastrowid
            task_ids.append(task_id)

        conn.commit()

        # 发布ROS2任务
        for (drug_id, quantity, drug_name), task_id in zip(order_items, task_ids):
            drug, _ = validate_and_get_drug(drug_id, quantity)
            if drug:
                publish_task(task_id, drug, quantity)

        return jsonify({
            'success': True,
            'ok': True,
            'prescription_id': prescription_id,
            'patient_name': patient_name,
            'task_ids': task_ids,
            'message': f'处方配药成功，创建了{len(task_ids)}个取药任务',
            'mode': 'real_api'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({
            'success': False,
            'ok': False,
            'error': f'配药失败: {str(e)}',
            'mode': 'error'
        })
    finally:
        conn.close()


@app.route('/api/orders', methods=['GET'])
def list_orders():
    """查看取药记录"""
    conn = get_db_connection()
    try:
        cur = conn.execute('''
            SELECT o.task_id, o.status, o.target_drug_id, o.quantity, o.created_at, i.name
            FROM order_log o
            LEFT JOIN inventory i ON o.target_drug_id = i.drug_id
            ORDER BY o.task_id DESC
            LIMIT 50
        ''')
        rows = cur.fetchall()
        orders = []
        for r in rows:
            orders.append({
                'task_id': r[0],
                'status': r[1],
                'target_drug_id': r[2],
                'quantity': r[3],
                'created_at': r[4],
                'drug_name': r[5],
            })
        return jsonify({'success': True, 'ok': True, 'data': orders})
    finally:
        conn.close()


@app.route('/api/approvals', methods=['POST'])
def create_approval():
    """Create a new approval request"""
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": True, "message": "Invalid JSON data provided"}), 400

        # Validate required fields
        required_fields = ['patient_name', 'advice']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": True,
                    "message": f"Missing required field: {field}",
                    "code": "MISSING_FIELD"
                }), 400

        # Import ApprovalManager
        from approval import get_approval_manager

        # Create approval
        manager = get_approval_manager()
        # 处理quantity字段，确保为整数，默认为1
        quantity = data.get('quantity', 1)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                quantity = 1  # 数量必须大于0，否则使用默认值
        except (TypeError, ValueError):
            quantity = 1  # 转换失败时使用默认值

        approval_id = manager.create(
            patient_name=data['patient_name'],
            advice=data['advice'],
            patient_age=data.get('patient_age'),
            patient_weight=data.get('patient_weight'),
            symptoms=data.get('symptoms'),
            drug_name=data.get('drug_name'),
            drug_type=data.get('drug_type'),
            quantity=quantity
        )

        return jsonify({
            "success": True,
            "approval_id": approval_id,
            "message": "Approval created successfully",
            "created_at": datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to create approval: {str(e)}",
            "code": "CREATION_ERROR"
        }), 500


@app.route('/api/approvals/<approval_id>', methods=['GET'])
def get_approval(approval_id):
    """Get approval details by ID"""
    try:
        from approval import get_approval_manager

        manager = get_approval_manager()
        approval = manager.get(approval_id)

        if not approval:
            return jsonify({
                "error": True,
                "message": f"Approval not found: {approval_id}",
                "code": "NOT_FOUND"
            }), 404

        # Convert SQLite Row to dict if needed
        if hasattr(approval, 'keys'):
            approval = dict(approval)

        # Rename 'id' to 'approval_id' for API consistency
        if 'id' in approval:
            approval['approval_id'] = approval.pop('id')

        return jsonify({
            "success": True,
            "approval": approval
        }), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to get approval: {str(e)}",
            "code": "RETRIEVAL_ERROR"
        }), 500


@app.route('/api/approvals/pending', methods=['GET'])
def get_pending_approvals():
    """Get list of pending approvals"""
    try:
        from approval import get_approval_manager

        manager = get_approval_manager()
        limit = request.args.get('limit', default=100, type=int)
        pending = manager.list_pending(limit=limit)

        # Convert SQLite Rows to dicts
        approvals = []
        for item in pending:
            if hasattr(item, 'keys'):
                approvals.append(dict(item))
            else:
                approvals.append(item)

        # Rename 'id' to 'approval_id' for API consistency
        for approval in approvals:
            if 'id' in approval:
                approval['approval_id'] = approval.pop('id')

        return jsonify({
            "success": True,
            "approvals": approvals,
            "count": len(approvals),
            "limit": limit
        }), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to get pending approvals: {str(e)}",
            "code": "RETRIEVAL_ERROR"
        }), 500


@app.route('/api/approvals/<approval_id>/approve', methods=['POST'])
def approve_approval(approval_id):
    """Approve an approval request"""
    try:
        data = request.get_json()
        if not data or 'doctor_id' not in data:
            return jsonify({
                "error": True,
                "message": "Missing doctor_id in request",
                "code": "MISSING_DOCTOR_ID"
            }), 400

        from approval import get_approval_manager

        manager = get_approval_manager()
        notes = data.get('notes')
        success = manager.approve(approval_id, data['doctor_id'], notes=notes)

        if not success:
            return jsonify({
                "error": True,
                "message": f"Cannot approve approval {approval_id}. It may not exist or not be pending.",
                "code": "APPROVAL_FAILED"
            }), 400

        # 审批成功后自动创建订单
        order_created = False
        order_message = ""
        task_id = None
        try:
            # 获取审批单详情
            approval = manager.get(approval_id)
            if approval and approval.get('drug_name'):
                drug_name = approval['drug_name']
                quantity = approval.get('quantity', 1)

                # 使用多级匹配策略查找药品ID
                drug_id = find_drug_id_by_name(drug_name)

                if drug_id:
                    # 验证药品
                    drug, err = validate_and_get_drug(drug_id, quantity)
                    if not err:
                        conn = get_db_connection()
                        # 原子扣减库存
                        cur = conn.execute(
                            'UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?',
                            (quantity, drug_id, quantity)
                        )
                        if cur.rowcount > 0:
                            # 写入order_log
                            cur = conn.execute(
                                'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
                                ('pending', drug_id, quantity)
                            )
                            task_id = cur.lastrowid
                            conn.commit()
                            # 发布ROS2任务
                            publish_task(task_id, drug, quantity)
                            order_created = True
                            order_message = f"订单创建成功，任务ID: {task_id}，数量: {quantity}"
                        else:
                            order_message = f"库存不足，需要{quantity}个，库存不足"
                    else:
                        order_message = f"药品验证失败: {err}"
                else:
                    order_message = f"未找到药品: {drug_name}"
            else:
                order_message = "审批单未指定药品名称"
        except Exception as e:
            order_message = f"订单创建过程中出错: {str(e)}"
            # 不影响审批成功，仅记录错误

        # 返回审批成功，同时包含订单创建状态
        response_data = {
            "success": True,
            "message": "Approval approved successfully",
            "approval_id": approval_id,
            "doctor_id": data['doctor_id'],
            "approved_at": datetime.now().isoformat(),
            "order_created": order_created,
            "order_message": order_message
        }
        if notes:
            response_data['notes'] = notes
        if task_id:
            response_data["task_id"] = task_id
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to approve approval: {str(e)}",
            "code": "APPROVAL_ERROR"
        }), 500


@app.route('/api/approvals/<approval_id>/reject', methods=['POST'])
def reject_approval(approval_id):
    """Reject an approval request"""
    try:
        data = request.get_json()
        if not data or 'doctor_id' not in data:
            return jsonify({
                "error": True,
                "message": "Missing doctor_id in request",
                "code": "MISSING_DOCTOR_ID"
            }), 400

        if 'reason' not in data:
            return jsonify({
                "error": True,
                "message": "Missing rejection reason",
                "code": "MISSING_REASON"
            }), 400

        from approval import get_approval_manager

        manager = get_approval_manager()
        success = manager.reject(approval_id, data['doctor_id'], data['reason'])

        if not success:
            return jsonify({
                "error": True,
                "message": f"Cannot reject approval {approval_id}. It may not exist or not be pending.",
                "code": "REJECTION_FAILED"
            }), 400

        return jsonify({
            "success": True,
            "message": "Approval rejected successfully",
            "approval_id": approval_id,
            "doctor_id": data['doctor_id'],
            "reason": data['reason'],
            "rejected_at": datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to reject approval: {str(e)}",
            "code": "REJECTION_ERROR"
        }), 500


def find_drug_id_by_name(drug_name: str) -> int | None:
    """
    根据药品名称查找药品ID，使用多级匹配策略：
    1. 精确匹配（完全相等）
    2. 去除空白和标点后匹配
    3. 模糊匹配（LIKE %drug_name%）
    返回ID或None
    """
    import re

    # 规范化药品名称：去除前后空白，转换为小写（中文不受影响）
    normalized = drug_name.strip()
    if not normalized:
        return None

    # 创建规范化版本：去除所有空白和标点符号
    cleaned = re.sub(r'[\s\W_]+', '', normalized)

    conn = get_db_connection()
    try:
        # 1. 精确匹配
        cur = conn.execute(
            'SELECT drug_id FROM inventory WHERE name = ?',
            (normalized,)
        )
        row = cur.fetchone()
        if row:
            return row['drug_id']

        # 2. 规范化匹配（如果cleaned与原值不同且非空）
        if cleaned and cleaned != normalized:
            # 先获取所有药品名称进行客户端规范化匹配
            cur = conn.execute('SELECT drug_id, name FROM inventory')
            rows = cur.fetchall()
            for r in rows:
                db_name = r['name']
                db_cleaned = re.sub(r'[\s\W_]+', '', db_name)
                if cleaned == db_cleaned:
                    return r['drug_id']

        # 3. 模糊匹配（保持原逻辑作为后备）
        cur = conn.execute(
            'SELECT drug_id FROM inventory WHERE name LIKE ?',
            (f'%{normalized}%',)
        )
        row = cur.fetchone()
        return row['drug_id'] if row else None

    finally:
        conn.close()


# Werkzeug 开启自动重载时，仅子进程会带 WERKZEUG_RUN_MAIN=true；在此启动可避免父进程再挂一套线程导致重复扣减。
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    _boot_expiry_worker_once()


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print('请先运行: python3 init_db.py')
        exit(1)
    _debug = True
    _use_reloader = _debug
    # debug + 自动重载时由子进程 import 时启动；当前若是「只起监控不重载」的父进程则不应在此启动
    if not (_debug and _use_reloader):
        _boot_expiry_worker_once()

    app.run(host=Config.HOST, port=Config.PORT, debug=_debug, use_reloader=_use_reloader)

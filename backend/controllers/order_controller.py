"""
Order Controller
Handles drug ordering, pickup, dispensing, and order history
"""

from flask import Blueprint, jsonify, request
from utils.database import get_db_connection
from utils.ros2_bridge import publish_task
from utils.drug_helpers import validate_and_get_drug, find_drug_id_by_name

# Create blueprint for order routes
order_bp = Blueprint('order', __name__, url_prefix='/api')


def create_order_for_drug(conn, drug_id: int, quantity: int, drug: dict, publish_now: bool = True) -> tuple[int | None, str]:
    """Create an order for a single drug (inventory deduction + order log + optional task publishing)

    Args:
        conn: Database connection (must be in transaction)
        drug_id: Drug ID to order
        quantity: Quantity to order
        drug: Drug dictionary from validate_and_get_drug
        publish_now: Whether to publish ROS2 task immediately (default True)

    Returns:
        Tuple of (task_id, error_message). task_id is None if failed.
    """
    try:
        # Atomic inventory deduction (WHERE quantity>=quantity prevents over-deduction, concurrency safe)
        cur = conn.execute(
            'UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?',
            (quantity, drug_id, quantity)
        )
        if cur.rowcount == 0:
            return None, f'库存不足: {drug["name"]}，请刷新后重试'

        # Write to order_log
        cur = conn.execute(
            'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
            ('pending', drug_id, quantity)
        )
        task_id = cur.lastrowid

        # Publish ROS2 task if requested
        if publish_now:
            publish_task(task_id, drug, quantity)

        return task_id, ""
    except Exception as e:
        return None, f'创建订单失败: {str(e)}'


@order_bp.route('/order', methods=['POST', 'OPTIONS'])
def order():
    """
    Batch drug order
    Receives: [ {"id": 1, "num": 2}, {"id": 2, "num": 1} ]
    Process: validate -> deduct inventory -> write to order_log -> publish ROS2 task
    """
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'ok': False, 'error': '请求体必须为 JSON', 'code': 'INVALID_JSON'}), 400

    if not isinstance(data, list):
        data = [data]

    order_data = []
    for item in data:
        drug_id = item.get('id')
        num = item.get('num')
        if drug_id is None or num is None:
            return jsonify({'success': False, 'ok': False, 'error': '每项需包含 id 和 num', 'code': 'MISSING_FIELDS'}), 400
        try:
            order_data.append((int(drug_id), int(num)))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'ok': False, 'error': 'id 和 num 必须为整数', 'code': 'INVALID_TYPE'}), 400

    if not order_data:
        return jsonify({'success': False, 'ok': False, 'error': '药单为空', 'code': 'EMPTY_ORDER'}), 400

    # Pre-validate all items
    tasks = []
    for drug_id, num in order_data:
        if num <= 0:
            return jsonify({'success': False, 'ok': False, 'error': f'药品 {drug_id} 数量必须大于 0', 'code': 'INVALID_QUANTITY'}), 400
        drug, err = validate_and_get_drug(drug_id, num)
        if err:
            return jsonify({'success': False, 'ok': False, 'error': err, 'code': 'DRUG_VALIDATION_FAILED'}), 400
        tasks.append((drug_id, num, drug))

    # All passed: deduct inventory + write to order_log + publish ROS2 (same transaction)
    conn = None
    try:
        conn = get_db_connection()
        task_ids = []
        for drug_id, num, drug in tasks:
            # Use helper function with publish_now=False (we'll publish after commit)
            task_id, err = create_order_for_drug(conn, drug_id, num, drug, publish_now=False)
            if task_id is None:
                conn.rollback()
                return jsonify({'success': False, 'ok': False, 'error': err, 'code': 'INSUFFICIENT_INVENTORY'}), 400
            task_ids.append(task_id)
        conn.commit()
        # Publish all tasks after successful commit
        for (drug_id, num, drug), task_id in zip(tasks, task_ids):
            publish_task(task_id, drug, num)
        return jsonify({
            'success': True, 'ok': True,
            'task_ids': task_ids,
            'message': f'已下发 {len(task_ids)} 个取药任务，库存已扣减',
        })
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in order function: {e}")
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'ok': False,
            'error': 'Database error while processing order',
            'code': 'DB_ERROR'
        }), 500
    finally:
        if conn:
            conn.close()


@order_bp.route('/pickup', methods=['POST'])
def pickup():
    """
    Single drug pickup (compatibility with old interface)
    Receives: { "id": 1, "num": 2 }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'ok': False, 'error': '请求体必须为 JSON', 'code': 'INVALID_JSON'}), 400

    drug_id = data.get('id')
    num = data.get('num')
    if drug_id is None or num is None:
        return jsonify({'success': False, 'ok': False, 'error': '缺少 id 或 num', 'code': 'MISSING_FIELDS'}), 400
    try:
        drug_id, num = int(drug_id), int(num)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'ok': False, 'error': 'id 和 num 必须为整数', 'code': 'INVALID_TYPE'}), 400
    if num <= 0:
        return jsonify({'success': False, 'ok': False, 'error': 'num 必须大于 0', 'code': 'INVALID_QUANTITY'}), 400

    drug, err = validate_and_get_drug(drug_id, num)
    if err:
        return jsonify({'success': False, 'ok': False, 'error': err, 'code': 'DRUG_VALIDATION_FAILED'}), 400

    conn = None
    try:
        conn = get_db_connection()
        # Use helper function with publish_now=True (default)
        task_id, err = create_order_for_drug(conn, drug_id, num, drug, publish_now=True)
        if task_id is None:
            conn.rollback()
            return jsonify({'success': False, 'ok': False, 'error': err, 'code': 'INSUFFICIENT_INVENTORY'}), 400
        conn.commit()
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
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in pickup function: {e}")
        if conn:
            conn.rollback()
        return jsonify({
            'success': False,
            'ok': False,
            'error': 'Database error while processing pickup',
            'code': 'DB_ERROR'
        }), 500
    finally:
        if conn:
            conn.close()


@order_bp.route('/dispense', methods=['POST'])
def dispense():
    """
    Dispensing endpoint for fill_prescription tool
    Receives: {
        "prescription_id": "Prescription ID",
        "patient_name": "Patient name",
        "drugs": [{"name": "Drug name", "dosage": "Dosage", "quantity": quantity}]
    }
    Returns: Similar to /order endpoint order creation result
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'ok': False, 'error': '请求体必须为 JSON', 'code': 'INVALID_JSON'}), 400

    prescription_id = data.get('prescription_id')
    patient_name = data.get('patient_name')
    drugs = data.get('drugs')

    if not prescription_id or not patient_name or not drugs:
        return jsonify({
            'success': False,
            'ok': False,
            'error': '缺少必要参数: prescription_id, patient_name, drugs',
            'code': 'MISSING_REQUIRED_FIELDS'
        }), 400

    if not isinstance(drugs, list):
        return jsonify({
            'success': False,
            'ok': False,
            'error': 'drugs必须为数组',
            'code': 'INVALID_TYPE'
        }), 400

    # Convert drug names to drug IDs and validate
    order_items = []
    for drug_item in drugs:
        drug_name = drug_item.get('name')
        quantity = drug_item.get('quantity', 1)

        if not drug_name:
            return jsonify({
                'success': False,
                'ok': False,
                'error': '药品缺少name字段',
                'code': 'MISSING_FIELD'
            }), 400

        try:
            quantity = int(quantity)
            if quantity <= 0:
                return jsonify({
                    'success': False,
                    'ok': False,
                    'error': f'药品数量必须大于0: {drug_name}',
                    'code': 'INVALID_QUANTITY'
                }), 400
        except (TypeError, ValueError):
            return jsonify({
                'success': False,
                'ok': False,
                'error': f'药品数量必须为整数: {drug_name}',
                'code': 'INVALID_TYPE'
            }), 400

        # Find drug ID
        drug_id = find_drug_id_by_name(drug_name)
        if not drug_id:
            return jsonify({
                'success': False,
                'ok': False,
                'error': f'未找到药品: {drug_name}',
                'code': 'DRUG_NOT_FOUND'
            }), 400

        order_items.append((drug_id, quantity, drug_name))

    # Create order (process each drug individually)
    conn = None
    try:
        conn = get_db_connection()
        task_ids = []
        for drug_id, quantity, drug_name in order_items:
            # Validate drug
            drug, err = validate_and_get_drug(drug_id, quantity)
            if err:
                conn.rollback()
                return jsonify({'success': False, 'ok': False, 'error': err, 'code': 'DRUG_VALIDATION_FAILED'}), 400

            # Use helper function with publish_now=False (we'll publish after commit)
            task_id, err = create_order_for_drug(conn, drug_id, quantity, drug, publish_now=False)
            if task_id is None:
                conn.rollback()
                return jsonify({
                    'success': False,
                    'ok': False,
                    'error': f'库存不足: {drug_name}，请刷新后重试',
                    'code': 'INSUFFICIENT_INVENTORY'
                }), 400
            task_ids.append(task_id)

        conn.commit()

        # Publish ROS2 tasks after successful commit
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
            'code': 'DISPENSE_ERROR',
            'mode': 'error'
        })
    finally:
        if conn:
            conn.close()


@order_bp.route('/orders', methods=['GET'])
def list_orders():
    """View drug pickup records"""
    conn = None
    try:
        conn = get_db_connection()
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
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in list_orders: {e}")
        return jsonify({
            'success': False,
            'ok': False,
            'error': 'Database error while fetching orders',
            'code': 'DB_ERROR'
        }), 500
    finally:
        if conn:
            conn.close()
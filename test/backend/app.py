"""
Flask 后端 - 接收前端请求、查库定位、下发 ROS2 任务、生成取药记录
"""
import json
import os
import sqlite3
import threading
from flask import Flask, request, jsonify

# ROS2 可选：若环境未配置则跳过发布
ros2_available = False
task_publisher = None


def init_ros2():
    """在后台线程中初始化 ROS2 并持续 spin"""
    global ros2_available, task_publisher
    try:
        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import String

        class TaskPublisher(Node):
            def __init__(self):
                super().__init__('backend_task_publisher')
                self.pub = self.create_publisher(String, '/task_request', 10)

        rclpy.init()
        node = TaskPublisher()
        task_publisher = node
        ros2_available = True
        print('[ROS2] 已连接，任务将发布到 /task_request')

        executor = rclpy.executors.SingleThreadedExecutor()
        executor.add_node(node)
        while rclpy.ok():
            executor.spin_once(timeout_sec=0.1)
    except Exception as e:
        print(f'[ROS2] 未启用: {e}，任务将仅记录到数据库')


# 启动时尝试初始化 ROS2（后台线程）
_ros_thread = threading.Thread(target=init_ros2, daemon=True)
_ros_thread.start()

# Flask
app = Flask(__name__)

# CORS：允许前端跨域访问
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    @app.after_request
    def add_cors(resp):
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

DB_PATH = os.path.join(os.path.dirname(__file__), 'pharmacy.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_drug(drug_id: int) -> dict | None:
    conn = get_db()
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


def publish_task(task_id: int, drug: dict, quantity: int):
    """向 ROS2 /task_request 发布取药任务"""
    global task_publisher
    if not ros2_available or task_publisher is None:
        return
    try:
        from std_msgs.msg import String
        msg = String()
        msg.data = json.dumps({
            'task_id': task_id,
            'type': 'pickup',
            'drug_id': drug['drug_id'],
            'name': drug['name'],
            'shelve_id': drug['shelve_id'],
            'x': drug['shelf_x'],
            'y': drug['shelf_y'],
            'quantity': quantity,
        })
        task_publisher.pub.publish(msg)
        print(f'[ROS2] 已发布任务 task_id={task_id} -> ({drug["shelf_x"]},{drug["shelf_y"]})')
    except Exception as e:
        print(f'[ROS2] 发布失败: {e}')


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'backend running', 'ros2': ros2_available})


@app.route('/api/drugs', methods=['GET'])
def list_drugs():
    conn = get_db()
    try:
        cur = conn.execute(
            'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory'
        )
        drugs = [dict(row) for row in cur.fetchall()]
        return jsonify({'ok': True, 'data': drugs})
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
        return jsonify({'ok': False, 'error': '请求体必须为 JSON'}), 400

    if not isinstance(data, list):
        data = [data]

    order_data = []
    for item in data:
        drug_id = item.get('id')
        num = item.get('num')
        if drug_id is None or num is None:
            return jsonify({'ok': False, 'error': '每项需包含 id 和 num'}), 400
        try:
            order_data.append((int(drug_id), int(num)))
        except (TypeError, ValueError):
            return jsonify({'ok': False, 'error': 'id 和 num 必须为整数'}), 400

    if not order_data:
        return jsonify({'ok': False, 'error': '药单为空'}), 400

    # 预校验全部
    tasks = []
    for drug_id, num in order_data:
        if num <= 0:
            return jsonify({'ok': False, 'error': f'药品 {drug_id} 数量必须大于 0'}), 400
        drug, err = validate_and_get_drug(drug_id, num)
        if err:
            return jsonify({'ok': False, 'error': err}), 400
        tasks.append((drug_id, num, drug))

    # 全部通过：扣减库存 + 写入 order_log + 发布 ROS2（同一事务）
    conn = get_db()
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
                return jsonify({'ok': False, 'error': f'库存不足: {drug["name"]}，请刷新后重试'}), 400

            cur = conn.execute(
                'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
                ('pending', drug_id, num)
            )
            task_ids.append(cur.lastrowid)
        conn.commit()
        for (drug_id, num, drug), task_id in zip(tasks, task_ids):
            publish_task(task_id, drug, num)
        return jsonify({
            'ok': True,
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
        return jsonify({'ok': False, 'error': '请求体必须为 JSON'}), 400

    drug_id = data.get('id')
    num = data.get('num')
    if drug_id is None or num is None:
        return jsonify({'ok': False, 'error': '缺少 id 或 num'}), 400
    try:
        drug_id, num = int(drug_id), int(num)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'id 和 num 必须为整数'}), 400
    if num <= 0:
        return jsonify({'ok': False, 'error': 'num 必须大于 0'}), 400

    drug, err = validate_and_get_drug(drug_id, num)
    if err:
        return jsonify({'ok': False, 'error': err}), 400

    conn = get_db()
    try:
        # 原子扣减库存（防止并发）
        cur = conn.execute(
            'UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?',
            (num, drug_id, num)
        )
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({'ok': False, 'error': f'库存不足或已被占用: {drug["name"]}，请刷新后重试'}), 400

        cur = conn.execute(
            'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
            ('pending', drug_id, num)
        )
        task_id = cur.lastrowid
        conn.commit()
        publish_task(task_id, drug, num)
        return jsonify({
            'ok': True,
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


@app.route('/api/orders', methods=['GET'])
def list_orders():
    """查看取药记录"""
    conn = get_db()
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
        return jsonify({'ok': True, 'data': orders})
    finally:
        conn.close()


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print('请先运行: python3 init_db2.py')
        exit(1)
    app.run(host='0.0.0.0', port=5000, debug=True)

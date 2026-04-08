import threading
import time

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

def publish_task(task_id: int, drug: dict, quantity: int):
    """向 ROS2 /task_request 发布取药任务"""
    global task_publisher
    if not ros2_available or task_publisher is None:
        return

    try:
        from std_msgs.msg import String
        import json

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

def publish_expiry_removal(drug: dict, remove_quantity: int):
    """向 ROS2 /task_request 发布过期药品清柜任务（定期清扫发现仍有库存的过期品时调用）"""
    global task_publisher
    if not ros2_available or task_publisher is None:
        return

    try:
        from std_msgs.msg import String
        import json

        msg = String()
        msg.data = json.dumps({
            'task_id': None,
            'type': 'expiry_removal',
            'drug_id': drug['drug_id'],
            'name': drug['name'],
            'shelve_id': drug['shelve_id'],
            'x': drug['shelf_x'],
            'y': drug['shelf_y'],
            'quantity': remove_quantity,
            'reason': 'expired',
        }, ensure_ascii=False)
        task_publisher.pub.publish(msg)
        print(
            f'[ROS2] 已发布过期清柜 type=expiry_removal drug_id={drug["drug_id"]} '
            f'qty={remove_quantity} -> ({drug["shelf_x"]},{drug["shelf_y"]})'
        )
    except Exception as e:
        print(f'[ROS2] 过期清柜发布失败: {e}')

def check_ros2_status():
    """检查ROS2状态"""
    return {
        'available': ros2_available,
        'publisher_initialized': task_publisher is not None
    }
import threading
import time
import signal
from typing import Dict, Any, Optional

# Thread-safe global variables with locks
ros2_available = False
task_publisher = None
ros2_lock = threading.Lock()
shutdown_requested = False

def init_ros2() -> None:
    """Initialize ROS2 in background thread and continuously spin"""
    global ros2_available, task_publisher, shutdown_requested

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        global shutdown_requested
        shutdown_requested = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

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

        # Thread-safe update of global variables
        with ros2_lock:
            task_publisher = node
            ros2_available = True

        print('[ROS2] Connected, tasks will be published to /task_request')

        executor = rclpy.executors.SingleThreadedExecutor()
        executor.add_node(node)

        # Add proper shutdown handling
        while rclpy.ok() and not shutdown_requested:
            executor.spin_once(timeout_sec=0.1)

        # Cleanup on shutdown
        if shutdown_requested:
            print('[ROS2] Shutdown requested, cleaning up...')
            node.destroy_node()
            rclpy.shutdown()
            with ros2_lock:
                ros2_available = False
                task_publisher = None
    except Exception as e:
        print(f'[ROS2] Not enabled: {e}, tasks will only be logged to database')

def publish_task(task_id: int, drug: Dict[str, Any], quantity: int) -> None:
    """Publish medication pickup task to ROS2 /task_request"""
    global task_publisher
    with ros2_lock:
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

        # Thread-safe access to publisher
        with ros2_lock:
            if task_publisher is not None:
                task_publisher.pub.publish(msg)
                print(f'[ROS2] Published task task_id={task_id} -> ({drug["shelf_x"]},{drug["shelf_y"]})')
    except Exception as e:
        print(f'[ROS2] Publish failed: {e}')

def publish_expiry_removal(drug: Dict[str, Any], remove_quantity: int) -> None:
    """Publish expired drug removal task to ROS2 /task_request (called when expired stock is found during periodic cleanup)"""
    global task_publisher
    with ros2_lock:
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

        # Thread-safe access to publisher
        with ros2_lock:
            if task_publisher is not None:
                task_publisher.pub.publish(msg)
                print(
                    f'[ROS2] Published expiry removal type=expiry_removal drug_id={drug["drug_id"]} '
                    f'qty={remove_quantity} -> ({drug["shelf_x"]},{drug["shelf_y"]})'
                )
    except Exception as e:
        print(f'[ROS2] Expiry removal publish failed: {e}')

def check_ros2_status() -> Dict[str, Any]:
    """Check ROS2 status"""
    with ros2_lock:
        return {
            'available': ros2_available,
            'publisher_initialized': task_publisher is not None
        }
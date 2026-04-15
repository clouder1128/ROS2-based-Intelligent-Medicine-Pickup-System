"""
ROS2桥接适配器 - 向后兼容层
使用新的ROS2集成模块，保持现有API不变
"""

import threading
import time
import signal
from typing import Dict, Any, Optional

# Thread-safe global variables with locks
ros2_available = False
task_publisher_instance = None
ros2_lock = threading.Lock()
shutdown_requested = False

# 尝试导入新模块
try:
    from ..ros_integration.node_manager import RosNodeManager
    from ..ros_integration.task_publisher import TaskPublisher
    from ..ros_integration.config import Config
    NEW_MODULES_AVAILABLE = True
except ImportError as e:
    NEW_MODULES_AVAILABLE = False
    print(f"[ROS2 Bridge] New modules not available: {e}, using legacy fallback")


def init_ros2() -> None:
    """初始化ROS2（向后兼容）
    使用新的节点管理器，保持现有接口
    """
    global ros2_available, task_publisher_instance, shutdown_requested

    if not NEW_MODULES_AVAILABLE:
        print("[ROS2 Bridge] New modules not available, cannot initialize")
        return

    # 设置信号处理（仅在主线程）
    def signal_handler(signum, frame):
        global shutdown_requested
        shutdown_requested = True

    if threading.current_thread() == threading.main_thread():
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 获取节点管理器单例（会自动初始化ROS2）
        node_manager = RosNodeManager.get_instance()

        # 启动节点管理器
        node_manager.start()

        # 创建任务发布器
        publisher = TaskPublisher()

        # 线程安全更新全局变量
        with ros2_lock:
            task_publisher_instance = publisher
            ros2_available = True

        print("[ROS2 Bridge] Initialized with new integration modules")
        print(f"[ROS2 Bridge] Integration mode: {Config().INTEGRATION_MODE}")

        # 等待ROS2节点运行
        time.sleep(1)  # 给节点启动时间

        # 简单循环等待关闭信号
        while not shutdown_requested:
            time.sleep(0.5)

        # 关闭时清理
        if shutdown_requested:
            print("[ROS2 Bridge] Shutdown requested, cleaning up...")
            node_manager.shutdown()
            with ros2_lock:
                ros2_available = False
                task_publisher_instance = None

    except Exception as e:
        print(f"[ROS2 Bridge] Failed to initialize: {e}")
        with ros2_lock:
            ros2_available = False
            task_publisher_instance = None


def publish_task(task_id: int, drug: Dict[str, Any], quantity: int) -> None:
    """发布取药任务（向后兼容）
    使用新的TaskPublisher，保持相同接口
    """
    global task_publisher_instance, ros2_available

    with ros2_lock:
        if not ros2_available or task_publisher_instance is None:
            # 尝试延迟初始化
            try:
                if NEW_MODULES_AVAILABLE:
                    publisher = TaskPublisher()
                    task_publisher_instance = publisher
                    ros2_available = True
                else:
                    print("[ROS2 Bridge] Cannot publish: new modules not available")
                    return
            except Exception as e:
                print(f"[ROS2 Bridge] Failed to initialize publisher: {e}")
                return

    try:
        # 使用新的TaskPublisher发布任务
        success = task_publisher_instance.publish_task(task_id, drug, quantity)

        if success:
            print(f'[ROS2 Bridge] Published task task_id={task_id} -> ({drug["shelf_x"]},{drug["shelf_y"]})')
        else:
            print(f'[ROS2 Bridge] Failed to publish task {task_id} (see TaskPublisher logs)')

    except Exception as e:
        print(f"[ROS2 Bridge] Publish failed: {e}")


def publish_expiry_removal(drug: Dict[str, Any], remove_quantity: int) -> None:
    """发布过期药品清理任务（向后兼容）"""
    global task_publisher_instance, ros2_available

    with ros2_lock:
        if not ros2_available or task_publisher_instance is None:
            # 尝试延迟初始化
            try:
                if NEW_MODULES_AVAILABLE:
                    publisher = TaskPublisher()
                    task_publisher_instance = publisher
                    ros2_available = True
                else:
                    print("[ROS2 Bridge] Cannot publish expiry removal: new modules not available")
                    return
            except Exception as e:
                print(f"[ROS2 Bridge] Failed to initialize publisher: {e}")
                return

    try:
        # 使用新的TaskPublisher发布过期清理任务
        success = task_publisher_instance.publish_expiry_removal(drug, remove_quantity)

        if success:
            print(f'[ROS2 Bridge] Published expiry removal drug_id={drug["drug_id"]} qty={remove_quantity}')
        else:
            print(f'[ROS2 Bridge] Failed to publish expiry removal (see TaskPublisher logs)')

    except Exception as e:
        print(f"[ROS2 Bridge] Expiry removal publish failed: {e}")


def check_ros2_status() -> Dict[str, Any]:
    """检查ROS2状态（向后兼容）"""
    if not NEW_MODULES_AVAILABLE:
        with ros2_lock:
            return {
                "available": ros2_available,
                "publisher_initialized": task_publisher_instance is not None,
                "integration": "legacy_fallback"
            }

    try:
        from ..ros_integration.node_manager import RosNodeManager
        node_manager = RosNodeManager.get_instance()

        with ros2_lock:
            return {
                "available": ros2_available,
                "publisher_initialized": task_publisher_instance is not None,
                "integration": "new",
                "node_running": node_manager.is_running(),
                "connection_ok": node_manager.check_connection()
            }
    except Exception as e:
        with ros2_lock:
            return {
                "available": ros2_available,
                "publisher_initialized": task_publisher_instance is not None,
                "integration": "error",
                "error": str(e)
            }

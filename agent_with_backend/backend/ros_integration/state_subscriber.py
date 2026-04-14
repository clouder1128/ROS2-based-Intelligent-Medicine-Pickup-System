"""
状态订阅器 - 订阅Unity仿真状态消息
将ROS2状态消息转换为backend格式，更新数据库
"""

import threading
import time
from typing import Dict, Any, Optional
from backend.ros_integration.config import Config, TopicConfig
from backend.ros_integration.node_manager import RosNodeManager
from backend.ros_integration.message_adapter import MessageAdapter
from backend.ros_integration.error_handler import ErrorHandler

# 条件导入ROS2模块
try:
    import rclpy
    from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    rclpy = None

class StateSubscriber:
    """
    状态订阅器 - 订阅任务状态、车辆状态、药柜状态
    """

    def __init__(self):
        """初始化状态订阅器"""
        self._config = Config()
        self._node_manager = RosNodeManager.get_instance()
        self._message_adapter = MessageAdapter()
        self._error_handler = ErrorHandler()

        # 订阅器实例
        self._task_state_subscriber = None
        self._car_state_subscriber = None
        self._cabinet_state_subscriber = None

        # 回调函数
        self._task_state_callback = None
        self._car_state_callback = None
        self._cabinet_state_callback = None

        self._initialized = False

        self._init_subscribers()

    def _init_subscribers(self):
        """初始化ROS2订阅器"""
        if not ROS2_AVAILABLE:
            print("[StateSubscriber] ROS2 not available, using fallback mode")
            return

        try:
            node = self._node_manager.get_node()
            if node is None:
                print("[StateSubscriber] ROS2 node not available")
                return

            # 配置QoS
            qos_profile = QoSProfile(
                depth=TopicConfig.QOS_DEPTH,
                reliability=QoSReliabilityPolicy.RELIABLE,
                durability=QoSDurabilityPolicy.VOLATILE
            )

            # 导入消息类型
            try:
                from task_msgs.msg import TaskState
                from task_msgs.msg import CarState
                from task_msgs.msg import CabinetState

                # 创建任务状态订阅器
                self._task_state_subscriber = node.create_subscription(
                    TaskState,
                    TopicConfig.TASK_STATE_TOPIC,
                    self._task_state_callback_wrapper,
                    qos_profile
                )

                # 创建车辆状态订阅器
                self._car_state_subscriber = node.create_subscription(
                    CarState,
                    TopicConfig.CAR_STATE_TOPIC,
                    self._car_state_callback_wrapper,
                    qos_profile
                )

                # 创建药柜状态订阅器
                self._cabinet_state_subscriber = node.create_subscription(
                    CabinetState,
                    TopicConfig.CABINET_STATE_TOPIC,
                    self._cabinet_state_callback_wrapper,
                    qos_profile
                )

                self._initialized = True
                print("[StateSubscriber] Initialized with all topic subscribers")

            except ImportError as e:
                print(f"[StateSubscriber] Message types not available: {e}")

        except Exception as e:
            print(f"[StateSubscriber] Failed to initialize subscribers: {e}")

    def set_task_state_callback(self, callback):
        """设置任务状态回调函数"""
        self._task_state_callback = callback

    def set_car_state_callback(self, callback):
        """设置车辆状态回调函数"""
        self._car_state_callback = callback

    def set_cabinet_state_callback(self, callback):
        """设置药柜状态回调函数"""
        self._cabinet_state_callback = callback

    def _task_state_callback_wrapper(self, msg):
        """任务状态回调包装器"""
        if self._task_state_callback is not None:
            try:
                # 转换消息格式
                backend_state = self._message_adapter.unity_to_backend(msg)
                self._task_state_callback(backend_state)
            except Exception as e:
                print(f"[StateSubscriber] Error in task state callback: {e}")
                self._error_handler.handle_publish_error(e, task_id=None, retry_strategy="none")

    def _car_state_callback_wrapper(self, msg):
        """车辆状态回调包装器"""
        if self._car_state_callback is not None:
            try:
                # 这里可以添加车辆状态转换逻辑
                print(f"[StateSubscriber] Received car state: {msg}")
            except Exception as e:
                print(f"[StateSubscriber] Error in car state callback: {e}")

    def _cabinet_state_callback_wrapper(self, msg):
        """药柜状态回调包装器"""
        if self._cabinet_state_callback is not None:
            try:
                # 这里可以添加药柜状态转换逻辑
                print(f"[StateSubscriber] Received cabinet state: {msg}")
            except Exception as e:
                print(f"[StateSubscriber] Error in cabinet state callback: {e}")

    def is_initialized(self):
        """检查订阅器是否初始化"""
        return self._initialized

    def start(self):
        """启动订阅器（实际不需要，由ROS2执行器处理）"""
        if not self._initialized:
            print("[StateSubscriber] Not initialized, cannot start")
            return False
        print("[StateSubscriber] Started (running in ROS2 executor)")
        return True
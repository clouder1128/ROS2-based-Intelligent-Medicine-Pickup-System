"""
任务发布器 - 发布取药任务和过期清理任务到ROS2话题
保持与现有ros2_bridge.py接口兼容
"""

import threading
import time
import json
from typing import Dict, Any, Optional
from .config import Config, TopicConfig
from .message_adapter import MessageAdapter
from .node_manager import RosNodeManager
from .error_handler import ErrorHandler, GracefulDegradation

# 条件导入ROS2模块
try:
    import rclpy
    from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    rclpy = None

# 条件导入消息类型
try:
    from task_msgs.msg import Task
    TASK_MSGS_AVAILABLE = True
except ImportError:
    TASK_MSGS_AVAILABLE = False
    Task = None

try:
    from std_msgs.msg import String
    STD_MSGS_AVAILABLE = True
except ImportError:
    STD_MSGS_AVAILABLE = False
    String = None

class TaskPublisher:
    """
    任务发布器 - 负责发布任务到ROS2话题
    支持新旧话题并行发布（兼容模式）
    """

    def __init__(self):
        """初始化任务发布器"""
        self._config = Config()
        self._node_manager = RosNodeManager.get_instance()
        self._message_adapter = MessageAdapter()
        self._error_handler = ErrorHandler()
        self._degradation = GracefulDegradation()

        # 初始化发布器
        self._new_publisher = None
        self._legacy_publisher = None
        self._initialized = False

        self._init_publishers()

    def _init_publishers(self):
        """初始化ROS2发布器"""
        if not ROS2_AVAILABLE:
            print("[TaskPublisher] ROS2 not available, using fallback mode")
            return

        try:
            node = self._node_manager.get_node()
            if node is None:
                print("[TaskPublisher] ROS2 node not available")
                return

            # 配置QoS
            qos_profile = QoSProfile(
                depth=TopicConfig.QOS_DEPTH,
                reliability=QoSReliabilityPolicy.RELIABLE,
                durability=QoSDurabilityPolicy.VOLATILE
            )

            mode = self._config.INTEGRATION_MODE

            # 根据集成模式创建发布器
            if mode == "new" and TASK_MSGS_AVAILABLE:
                # 仅新话题
                self._new_publisher = node.create_publisher(
                    Task,
                    TopicConfig.TASK_TOPIC_NEW,
                    qos_profile
                )
                print("[TaskPublisher] Created new topic publisher only")

            elif mode == "legacy" and STD_MSGS_AVAILABLE:
                # 仅旧话题
                self._legacy_publisher = node.create_publisher(
                    String,
                    TopicConfig.TASK_TOPIC_LEGACY,
                    qos_profile
                )
                print("[TaskPublisher] Created legacy topic publisher only")

            elif mode == "parallel":
                # 并行模式：两个话题都创建（如果依赖可用）
                if TASK_MSGS_AVAILABLE:
                    self._new_publisher = node.create_publisher(
                        Task,
                        TopicConfig.TASK_TOPIC_NEW,
                        qos_profile
                    )
                if STD_MSGS_AVAILABLE:
                    self._legacy_publisher = node.create_publisher(
                        String,
                        TopicConfig.TASK_TOPIC_LEGACY,
                        qos_profile
                    )
                print("[TaskPublisher] Created both new and legacy publishers")
            else:
                print(f"[TaskPublisher] Invalid mode or missing dependencies: {mode}")
                return

            self._initialized = True
            print(f"[TaskPublisher] Initialized with mode: {mode}")

        except Exception as e:
            print(f"[TaskPublisher] Failed to initialize publishers: {e}")
            self._error_handler.handle_publish_error(e, task_id=None, retry_strategy="none")

    def publish_task(self, task_id: int, drug: Dict[str, Any], quantity: int) -> bool:
        """
        发布取药任务（兼容现有接口）

        Args:
            task_id: 任务ID
            drug: 药品信息字典
            quantity: 取药数量

        Returns:
            bool: 发布是否成功
        """
        # 检查降级模式
        if not self._degradation.can_publish():
            print(f"[TaskPublisher] Cannot publish in degradation mode: {self._degradation.get_mode_name()}")
            self._degradation.record_failure()
            return False

        if not self._initialized:
            print("[TaskPublisher] Not initialized, cannot publish")
            self._degradation.record_failure()
            return False

        # 根据模式检查对应的发布器是否可用
        mode = self._config.INTEGRATION_MODE
        if mode == "new" and self._new_publisher is None:
            print("[TaskPublisher] New publisher not available in new mode")
            return False
        elif mode == "legacy" and self._legacy_publisher is None:
            print("[TaskPublisher] Legacy publisher not available in legacy mode")
            return False
        elif mode == "parallel" and self._new_publisher is None and self._legacy_publisher is None:
            print("[TaskPublisher] No publishers available in parallel mode")
            return False

        try:
            mode = self._config.INTEGRATION_MODE
            success = False

            # 根据模式发布消息
            if mode == "new" and self._new_publisher is not None:
                # 仅新话题
                task_msg = self._message_adapter.backend_to_unity(task_id, drug, quantity)
                self._new_publisher.publish(task_msg)
                print(f"[TaskPublisher] Published task {task_id} to {TopicConfig.TASK_TOPIC_NEW}")
                success = True

            elif mode == "legacy" and self._legacy_publisher is not None:
                # 仅旧话题
                legacy_msg = self._create_legacy_message(task_id, drug, quantity)
                self._legacy_publisher.publish(legacy_msg)
                print(f"[TaskPublisher] Published task {task_id} to {TopicConfig.TASK_TOPIC_LEGACY}")
                success = True

            elif mode == "parallel":
                # 并行模式：两个话题都发布（如果可用）
                if self._new_publisher is not None:
                    task_msg = self._message_adapter.backend_to_unity(task_id, drug, quantity)
                    self._new_publisher.publish(task_msg)
                    print(f"[TaskPublisher] Published task {task_id} to {TopicConfig.TASK_TOPIC_NEW}")
                    success = True
                if self._legacy_publisher is not None:
                    legacy_msg = self._create_legacy_message(task_id, drug, quantity)
                    self._legacy_publisher.publish(legacy_msg)
                    print(f"[TaskPublisher] Also published task {task_id} to {TopicConfig.TASK_TOPIC_LEGACY}")
                    success = True

            # 记录成功
            if success:
                self._degradation.record_success()
                return True
            else:
                print(f"[TaskPublisher] Failed to publish in mode {mode}: no publishers available")
                self._degradation.record_failure()
                return False

        except Exception as e:
            print(f"[TaskPublisher] Failed to publish task {task_id}: {e}")

            # 处理错误
            error_result = self._error_handler.handle_publish_error(e, task_id, retry_strategy="exponential")

            # 记录失败
            self._degradation.record_failure()

            # 根据错误处理结果决定是否重试
            if error_result.get("retry_scheduled", False):
                print(f"[TaskPublisher] Task {task_id} scheduled for retry in {error_result.get('retry_delay_sec')}s")
                # 这里可以集成到消息队列重试机制

            return False

    def publish_expiry_removal(self, drug: Dict[str, Any], remove_quantity: int) -> bool:
        """
        发布过期药品清理任务（兼容现有接口）

        Args:
            drug: 药品信息字典
            remove_quantity: 清理数量

        Returns:
            bool: 发布是否成功
        """
        # 检查降级模式
        if not self._degradation.can_publish():
            print(f"[TaskPublisher] Cannot publish expiry removal in degradation mode")
            return False

        if not self._initialized:
            print("[TaskPublisher] Not initialized, cannot publish expiry removal")
            return False

        # 根据模式检查对应的发布器是否可用
        mode = self._config.INTEGRATION_MODE
        if mode == "new" and self._new_publisher is None:
            print("[TaskPublisher] New publisher not available in new mode for expiry removal")
            return False
        elif mode == "legacy" and self._legacy_publisher is None:
            print("[TaskPublisher] Legacy publisher not available in legacy mode for expiry removal")
            return False
        elif mode == "parallel" and self._new_publisher is None and self._legacy_publisher is None:
            print("[TaskPublisher] No publishers available in parallel mode for expiry removal")
            return False

        try:
            mode = self._config.INTEGRATION_MODE
            success = False

            # 根据模式发布消息
            if mode == "new" and self._new_publisher is not None:
                # 仅新话题
                task_msg = self._message_adapter.expiry_to_unity(drug, remove_quantity)
                self._new_publisher.publish(task_msg)
                print(f"[TaskPublisher] Published expiry removal for drug {drug.get('drug_id')}")
                success = True

            elif mode == "legacy" and self._legacy_publisher is not None:
                # 仅旧话题
                legacy_msg = self._create_legacy_expiry_message(drug, remove_quantity)
                self._legacy_publisher.publish(legacy_msg)
                print(f"[TaskPublisher] Published expiry removal to legacy topic for drug {drug.get('drug_id')}")
                success = True

            elif mode == "parallel":
                # 并行模式：两个话题都发布（如果可用）
                if self._new_publisher is not None:
                    task_msg = self._message_adapter.expiry_to_unity(drug, remove_quantity)
                    self._new_publisher.publish(task_msg)
                    print(f"[TaskPublisher] Published expiry removal for drug {drug.get('drug_id')}")
                    success = True
                if self._legacy_publisher is not None:
                    legacy_msg = self._create_legacy_expiry_message(drug, remove_quantity)
                    self._legacy_publisher.publish(legacy_msg)
                    print(f"[TaskPublisher] Also published expiry removal to legacy topic")
                    success = True

            if success:
                return True
            else:
                print(f"[TaskPublisher] Failed to publish expiry removal in mode {mode}: no publishers available")
                return False

        except Exception as e:
            print(f"[TaskPublisher] Failed to publish expiry removal: {e}")
            self._error_handler.handle_publish_error(e, task_id=None, retry_strategy="exponential")
            return False

    def _create_legacy_message(self, task_id: int, drug: Dict[str, Any], quantity: int):
        """创建旧格式消息（JSON字符串）"""
        if not STD_MSGS_AVAILABLE:
            return None

        legacy_data = {
            "task_id": task_id,
            "type": "pickup",  # 添加类型字段以满足测试期望
            "drug_id": drug.get("drug_id"),
            "name": drug.get("name"),
            "shelve_id": drug.get("shelve_id"),
            "x": drug.get("shelf_x"),  # 注意：测试期望"x"而不是"shelf_x"
            "y": drug.get("shelf_y"),  # 注意：测试期望"y"而不是"shelf_y"
            "quantity": quantity
        }

        msg = String()
        msg.data = json.dumps(legacy_data)
        return msg

    def _create_legacy_expiry_message(self, drug: Dict[str, Any], remove_quantity: int):
        """创建旧格式过期清理消息"""
        if not STD_MSGS_AVAILABLE:
            return None

        legacy_data = {
            "task_id": None,  # 添加task_id字段以保持格式一致
            "type": "expiry_removal",
            "drug_id": drug.get("drug_id"),
            "name": drug.get("name", ""),  # 添加name字段
            "shelve_id": drug.get("shelve_id"),
            "x": drug.get("shelf_x"),  # 使用"x"而不是"shelf_x"
            "y": drug.get("shelf_y"),  # 使用"y"而不是"shelf_y"
            "quantity": remove_quantity,  # 使用"quantity"而不是"remove_quantity"
            "reason": "expired"  # 添加reason字段
        }

        msg = String()
        msg.data = json.dumps(legacy_data)
        return msg
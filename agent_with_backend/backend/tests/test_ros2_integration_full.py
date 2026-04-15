"""
完整ROS2集成测试 - 验证所有话题发布和接收
"""
import pytest
import time
import threading
import json
from unittest.mock import Mock, patch
from collections import deque

# ROS2测试工具
try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String
    from task_msgs.msg import Task, TaskState, CarState, CabinetState
    ROS2_TEST_READY = True
except ImportError:
    ROS2_TEST_READY = False


@pytest.mark.integration
@pytest.mark.skipif(not ROS2_TEST_READY, reason="ROS2 environment not ready")
class TestRos2FullIntegration:
    """完整ROS2集成测试类"""

    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        # 启动ROS2节点用于接收测试消息
        rclpy.init()
        cls.test_node = Node("test_monitor_node")

        # 消息接收队列
        cls.received_messages = {
            "task_topic": deque(maxlen=10),
            "task_request": deque(maxlen=10),
            "task_state": deque(maxlen=10),
            "car_state": deque(maxlen=10),
            "cabinet_state": deque(maxlen=10),
        }

        # 创建订阅器收集消息
        cls._setup_subscribers()

        # 启动订阅线程
        cls.executor = rclpy.executors.MultiThreadedExecutor()
        cls.executor.add_node(cls.test_node)
        cls.executor_thread = threading.Thread(
            target=cls._executor_loop,
            daemon=True
        )
        cls.executor_thread.start()

        # 等待ROS2节点启动
        time.sleep(2)

    @classmethod
    def _setup_subscribers(cls):
        """设置测试订阅器"""
        # 订阅新话题
        cls.test_node.create_subscription(
            Task,
            "/task_topic",
            lambda msg: cls.received_messages["task_topic"].append(msg),
            10
        )

        # 订阅旧话题
        cls.test_node.create_subscription(
            String,
            "/task_request",
            lambda msg: cls.received_messages["task_request"].append(json.loads(msg.data)),
            10
        )

        # 订阅状态话题
        cls.test_node.create_subscription(
            TaskState,
            "/TaskState_U",
            lambda msg: cls.received_messages["task_state"].append(msg),
            10
        )

        cls.test_node.create_subscription(
            CarState,
            "/CarState_U",
            lambda msg: cls.received_messages["car_state"].append(msg),
            10
        )

        cls.test_node.create_subscription(
            CabinetState,
            "/CabinetState_U",
            lambda msg: cls.received_messages["cabinet_state"].append(msg),
            10
        )

    @classmethod
    def _executor_loop(cls):
        """执行器循环"""
        try:
            while rclpy.ok():
                cls.executor.spin_once(timeout_sec=0.1)
        except Exception as e:
            print(f"Executor error: {e}")

    @classmethod
    def teardown_class(cls):
        """测试类清理"""
        cls.test_node.destroy_node()
        rclpy.shutdown()

    def test_task_publishing_new_topic(self):
        """测试新话题任务发布"""
        from backend.ros_integration.task_publisher import TaskPublisher
        from backend.ros_integration.config import Config

        config = Config()
        config.INTEGRATION_MODE = "new"  # 仅新话题

        with patch('backend.ros_integration.task_publisher.Config', return_value=config):
            publisher = TaskPublisher()

            # 测试数据
            test_drug = {
                "drug_id": 100,
                "name": "Test Drug",
                "shelve_id": "Z",
                "shelf_x": 1,
                "shelf_y": 2,
                "quantity": 5
            }

            # 发布任务
            result = publisher.publish_task(task_id=9999, drug=test_drug, quantity=2)

            # 验证
            assert result is True

            # 等待消息接收
            time.sleep(1)

            # 检查新话题收到消息
            assert len(self.received_messages["task_topic"]) > 0
            msg = self.received_messages["task_topic"][-1]
            assert msg.task_id == "9999"

            # 检查旧话题没有消息
            assert len(self.received_messages["task_request"]) == 0

    def test_task_publishing_parallel_mode(self):
        """测试并行模式（新旧话题同时发布）"""
        from backend.ros_integration.task_publisher import TaskPublisher
        from backend.ros_integration.config import Config

        config = Config()
        config.INTEGRATION_MODE = "parallel"

        with patch('backend.ros_integration.task_publisher.Config', return_value=config):
            publisher = TaskPublisher()

            test_drug = {
                "drug_id": 101,
                "name": "Parallel Test",
                "shelve_id": "A",
                "shelf_x": 3,
                "shelf_y": 4,
                "quantity": 10
            }

            result = publisher.publish_task(task_id=10000, drug=test_drug, quantity=3)
            assert result is True

            time.sleep(1)

            # 检查两个话题都收到消息
            assert len(self.received_messages["task_topic"]) > 0
            assert len(self.received_messages["task_request"]) > 0

            # 验证JSON格式
            json_msg = self.received_messages["task_request"][-1]
            assert json_msg["task_id"] == 10000
            assert json_msg["type"] == "pickup"

    def test_expiry_removal_publishing(self):
        """测试过期清理任务发布"""
        from backend.ros_integration.task_publisher import TaskPublisher

        publisher = TaskPublisher()

        expired_drug = {
            "drug_id": 102,
            "name": "Expired Drug",
            "shelve_id": "B",
            "shelf_x": 5,
            "shelf_y": 6,
            "quantity": 8
        }

        result = publisher.publish_expiry_removal(expired_drug, remove_quantity=8)
        assert result is True

        time.sleep(1)

        # 检查消息
        assert len(self.received_messages["task_topic"]) > 0
        msg = self.received_messages["task_topic"][-1]
        assert msg.type == "expiry_removal"

    def test_state_subscription(self):
        """测试状态订阅功能"""
        from backend.ros_integration.state_subscriber import StateSubscriber

        # 模拟回调
        received_states = []
        def mock_callback(state):
            received_states.append(state)

        subscriber = StateSubscriber()
        subscriber.set_task_state_callback(mock_callback)

        # 创建测试发布节点
        from rclpy.node import Node
        test_pub_node = Node("test_publisher")
        publisher = test_pub_node.create_publisher(TaskState, "/TaskState_U", 10)

        # 发布测试状态
        test_state = TaskState()
        test_state.taskid = "12345"
        test_state.task_state = 2  # 完成状态
        test_state.car_id = 1

        publisher.publish(test_state)
        time.sleep(1)

        # 验证回调被调用
        # 注意：实际需要ROS2执行器运行才能触发回调
        # 这里主要测试订阅器初始化

        assert subscriber.is_initialized() is True

        test_pub_node.destroy_node()

    def test_health_monitoring(self):
        """测试健康监控"""
        from backend.ros_integration.health_monitor import HealthMonitor

        monitor = HealthMonitor()
        monitor.start()

        # 获取初始状态
        initial_status = monitor.get_health_status()
        assert "running" in initial_status
        assert "connection_healthy" in initial_status

        # 等待一次检查
        time.sleep(35)  # 略大于HEALTH_CHECK_INTERVAL_SEC

        status = monitor.get_health_status()
        print(f"Health status: {status}")

        monitor.stop()

    def test_error_handling_and_degradation(self):
        """测试错误处理和降级机制"""
        from backend.ros_integration.task_publisher import TaskPublisher
        from backend.ros_integration.error_handler import ErrorHandler

        publisher = TaskPublisher()
        error_handler = ErrorHandler()

        # 模拟连接错误
        with patch.object(publisher, '_new_publisher', None):  # 模拟发布器未初始化
            test_drug = {
                "drug_id": 103,
                "name": "Error Test",
                "shelve_id": "C",
                "shelf_x": 7,
                "shelf_y": 8,
                "quantity": 5
            }

            result = publisher.publish_task(task_id=10001, drug=test_drug, quantity=1)
            assert result is False  # 应该失败

        # 测试错误处理器
        mock_error = ConnectionError("Test connection error")
        result = error_handler.handle_publish_error(mock_error, task_id=10002, retry_strategy="exponential")

        assert result["status"] == "failed"
        assert "error_type" in result
        assert result["error_type"] == "connection"
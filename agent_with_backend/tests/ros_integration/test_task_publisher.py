"""TaskPublisher 任务发布器单元测试

依赖 conftest.py 注入的 ROS2 / task_msgs / std_msgs mock。
通过 reset_singletons fixture 保证测试隔离。
"""

import pytest
from unittest.mock import MagicMock, patch
from ros_integration.task_publisher import TaskPublisher
from ros_integration.config import Config


class TestInitPublishers:
    def test_default_new_mode(self):
        """new 模式下创建新格式 publisher"""
        # 需要先保证 rclpy 可用
        import ros_integration.task_publisher as tp
        tp.ROS2_AVAILABLE = True
        tp.TASK_MSGS_AVAILABLE = True

        pub = TaskPublisher()
        assert pub._new_publisher is not None
        assert pub._legacy_publisher is None
        assert pub._initialized is True

    def test_legacy_mode(self, monkeypatch):
        monkeypatch.setenv("ROS_INTEGRATION_MODE", "legacy")
        import ros_integration.task_publisher as tp
        # 重新加载 Config
        import importlib
        import ros_integration.config
        importlib.reload(ros_integration.config)

        tp.ROS2_AVAILABLE = True
        tp.STD_MSGS_AVAILABLE = True

        pub = TaskPublisher()
        assert pub._legacy_publisher is not None
        assert pub._new_publisher is None

    def test_parallel_mode(self, monkeypatch):
        monkeypatch.setenv("ROS_INTEGRATION_MODE", "parallel")
        import importlib
        import ros_integration.config
        importlib.reload(ros_integration.config)
        import ros_integration.task_publisher as tp
        tp.ROS2_AVAILABLE = True
        tp.TASK_MSGS_AVAILABLE = True
        tp.STD_MSGS_AVAILABLE = True

        pub = TaskPublisher()
        assert pub._new_publisher is not None
        assert pub._legacy_publisher is not None


class TestPublishTask:
    def test_publish_task_new_success(self):
        pub = TaskPublisher()
        pub._initialized = True
        pub._new_publisher = MagicMock()
        pub._config.INTEGRATION_MODE = "new"
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}

        result = pub.publish_task(100, drug, 2)
        assert result is True
        assert pub._new_publisher.publish.called

    def test_publish_task_new_success_called_with_msg(self):
        pub = TaskPublisher()
        pub._initialized = True
        pub._new_publisher = MagicMock()
        pub._config.INTEGRATION_MODE = "new"
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}

        pub.publish_task(100, drug, 2)
        # new 模式下，backend_to_unity 返回的 Task 消息被 publish
        call_args = pub._new_publisher.publish.call_args
        assert call_args is not None
        msg = call_args[0][0]
        assert msg.task_id == "100"

    def test_publish_task_legacy_success(self, monkeypatch):
        monkeypatch.setenv("ROS_INTEGRATION_MODE", "legacy")
        import importlib
        import ros_integration.config
        importlib.reload(ros_integration.config)

        pub = TaskPublisher()
        pub._initialized = True
        pub._legacy_publisher = MagicMock()
        pub._config.INTEGRATION_MODE = "legacy"
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}

        result = pub.publish_task(200, drug, 3)
        assert result is True
        assert pub._legacy_publisher.publish.called

    def test_publish_fails_when_not_initialized(self):
        pub = TaskPublisher()
        pub._initialized = False
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}
        result = pub.publish_task(1, drug, 1)
        assert result is False

    def test_publish_fails_when_degraded(self):
        pub = TaskPublisher()
        pub._initialized = True
        pub._degradation._current_mode = pub._degradation.DegradationMode.LOG_ONLY
        drug = {"drug_id": 1, "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}
        result = pub.publish_task(1, drug, 1)
        assert result is False


class TestPublishExpiryRemoval:
    def test_expiry_removal_success_new(self):
        pub = TaskPublisher()
        pub._initialized = True
        pub._new_publisher = MagicMock()
        pub._config.INTEGRATION_MODE = "new"
        drug = {"drug_id": 1, "shelve_id": 1, "shelf_x": 2, "shelf_y": 3}

        result = pub.publish_expiry_removal(drug, 5)
        assert result is True
        assert pub._new_publisher.publish.called

    def test_expiry_removal_fails_when_not_initialized(self):
        pub = TaskPublisher()
        pub._initialized = False
        drug = {"drug_id": 1, "shelve_id": 1, "shelf_x": 2, "shelf_y": 3}
        result = pub.publish_expiry_removal(drug, 5)
        assert result is False


class TestPublishReturnToQueue:
    def test_return_to_queue_success_new(self):
        pub = TaskPublisher()
        pub._initialized = True
        pub._new_publisher = MagicMock()
        pub._config.INTEGRATION_MODE = "new"

        result = pub.publish_return_to_queue("car_01")
        assert result is True
        assert pub._new_publisher.publish.called

    def test_return_to_queue_fails_when_not_initialized(self):
        pub = TaskPublisher()
        pub._initialized = False
        result = pub.publish_return_to_queue("car_01")
        assert result is False


class TestDegradationInteraction:
    def test_success_records_degradation_success(self):
        pub = TaskPublisher()
        pub._initialized = True
        pub._new_publisher = MagicMock()
        pub._config.INTEGRATION_MODE = "new"
        # 降低 failure_count 到非零
        pub._degradation._failure_count = 3
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}

        pub.publish_task(1, drug, 1)
        # 成功后 failure_count 减少
        assert pub._degradation._failure_count == 2

    def test_failure_records_degradation_failure(self):
        pub = TaskPublisher()
        pub._initialized = True
        pub._new_publisher = MagicMock()
        pub._new_publisher.publish.side_effect = RuntimeError("publish failed")
        pub._config.INTEGRATION_MODE = "new"
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}
        old_failures = pub._degradation._failure_count

        result = pub.publish_task(1, drug, 1)
        assert result is False
        assert pub._degradation._failure_count > old_failures

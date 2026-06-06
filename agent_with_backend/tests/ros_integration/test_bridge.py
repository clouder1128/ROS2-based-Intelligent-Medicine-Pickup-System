"""bridge.py 向后兼容层单元测试

测试 publish_task / publish_expiry_removal / publish_return_to_queue / check_ros2_status。
注意：init_ros2 包含长循环（while not shutdown_requested），不在单元测试中直接调用。
"""

from unittest.mock import MagicMock, patch
import pytest

# 导入 bridge 模块（依赖 conftest 中注入的 mock）
from ros_integration import bridge


class TestPublishTask:
    def test_publish_task_lazy_initializes_publisher(self):
        """首次调用 publish_task 应延迟初始化 TaskPublisher"""
        bridge.ros2_available = False
        bridge.task_publisher_instance = None
        bridge.NEW_MODULES_AVAILABLE = True

        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}

        # patch TaskPublisher 使其不真正初始化
        with patch("ros_integration.bridge.TaskPublisher") as MockTP:
            mock_instance = MagicMock()
            mock_instance.publish_task.return_value = True
            MockTP.return_value = mock_instance

            bridge.publish_task(100, drug, 2)

            assert MockTP.called
            assert bridge.ros2_available is True
            assert bridge.task_publisher_instance is mock_instance

    def test_publish_task_calls_publish(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_task.return_value = True

        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}
        bridge.publish_task(100, drug, 2)

        bridge.task_publisher_instance.publish_task.assert_called_once_with(100, drug, 2)

    def test_publish_task_handles_exception(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_task.side_effect = Exception("fail")

        drug = {"drug_id": 1, "shelve_id": 1, "shelf_x": 2, "shelf_y": 3, "quantity": 50}
        # 不应抛出异常
        bridge.publish_task(100, drug, 2)


class TestPublishExpiryRemoval:
    def test_publish_expiry_removal_calls_publish(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_expiry_removal.return_value = True

        drug = {"drug_id": 1, "shelve_id": 1, "shelf_x": 2, "shelf_y": 3}
        bridge.publish_expiry_removal(drug, 5)

        bridge.task_publisher_instance.publish_expiry_removal.assert_called_once_with(drug, 5)

    def test_publish_expiry_removal_lazy_init(self):
        bridge.ros2_available = False
        bridge.task_publisher_instance = None
        bridge.NEW_MODULES_AVAILABLE = True

        drug = {"drug_id": 1, "shelve_id": 1, "shelf_x": 2, "shelf_y": 3}

        with patch("ros_integration.bridge.TaskPublisher") as MockTP:
            mock_instance = MagicMock()
            mock_instance.publish_expiry_removal.return_value = True
            MockTP.return_value = mock_instance

            bridge.publish_expiry_removal(drug, 5)
            assert MockTP.called


class TestPublishReturnToQueue:
    def test_publish_return_to_queue_calls_publish(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_return_to_queue.return_value = True

        bridge.publish_return_to_queue("car_01")

        bridge.task_publisher_instance.publish_return_to_queue.assert_called_once_with("car_01")


class TestCheckRos2Status:
    def test_check_ros2_status_returns_dict(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.NEW_MODULES_AVAILABLE = True

        status = bridge.check_ros2_status()
        assert isinstance(status, dict)
        assert "available" in status
        assert "publisher_initialized" in status
        assert "integration" in status

    def test_check_ros2_status_legacy_fallback(self):
        bridge.ros2_available = False
        bridge.task_publisher_instance = None
        bridge.NEW_MODULES_AVAILABLE = False

        status = bridge.check_ros2_status()
        assert status["integration"] == "legacy_fallback"
        assert status["available"] is False

    def test_check_ros2_status_with_node_running(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.NEW_MODULES_AVAILABLE = True

        status = bridge.check_ros2_status()
        assert status["integration"] == "new"
        assert status["available"] is True

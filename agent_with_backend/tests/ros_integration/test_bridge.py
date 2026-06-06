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

    def test_publish_task_unavailable_and_failed_result(self):
        bridge.ros2_available = False
        bridge.task_publisher_instance = None
        bridge.NEW_MODULES_AVAILABLE = False
        bridge.publish_task(1, {"shelf_x": 1, "shelf_y": 1}, 1)

        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_task.return_value = False
        bridge.publish_task(
            1, {"name": "A", "shelf_x": 1, "shelf_y": 1}, 1
        )


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

    def test_publish_expiry_failure_and_exception(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_expiry_removal.return_value = False
        bridge.publish_expiry_removal({"drug_id": 1}, 1)
        bridge.task_publisher_instance.publish_expiry_removal.side_effect = RuntimeError(
            "fail"
        )
        bridge.publish_expiry_removal({"drug_id": 1}, 1)


class TestPublishReturnToQueue:
    def test_publish_return_to_queue_calls_publish(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_return_to_queue.return_value = True

        bridge.publish_return_to_queue("car_01")

        bridge.task_publisher_instance.publish_return_to_queue.assert_called_once_with("car_01")

    def test_return_failure_exception_and_unavailable(self):
        bridge.ros2_available = True
        bridge.task_publisher_instance = MagicMock()
        bridge.task_publisher_instance.publish_return_to_queue.return_value = False
        bridge.publish_return_to_queue("car")
        bridge.task_publisher_instance.publish_return_to_queue.side_effect = RuntimeError(
            "fail"
        )
        bridge.publish_return_to_queue("car")

        bridge.ros2_available = False
        bridge.task_publisher_instance = None
        bridge.NEW_MODULES_AVAILABLE = False
        bridge.publish_return_to_queue("car")


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

    def test_check_ros2_status_error(self):
        bridge.NEW_MODULES_AVAILABLE = True
        with patch(
            "ros_integration.node_manager.RosNodeManager.get_instance",
            side_effect=RuntimeError("broken"),
        ):
            status = bridge.check_ros2_status()
        assert status["integration"] == "error"

"""任务发布器测试"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from backend.ros_integration.task_publisher import TaskPublisher
from backend.ros_integration.message_adapter import MessageAdapter
from backend.ros_integration.config import Config

@pytest.fixture
def mock_ros2_available():
    """Mock ROS2 availability"""
    with patch('backend.ros_integration.task_publisher.ROS2_AVAILABLE', True), \
         patch('backend.ros_integration.task_publisher.TASK_MSGS_AVAILABLE', True), \
         patch('backend.ros_integration.task_publisher.STD_MSGS_AVAILABLE', True):
        yield

def test_task_publisher_initialization(mock_ros2_available):
    """测试任务发布器初始化"""
    with patch('backend.ros_integration.task_publisher.RosNodeManager') as mock_manager:
        mock_node = Mock()
        mock_manager.get_instance.return_value.get_node.return_value = mock_node

        publisher = TaskPublisher()

        # 检查重要属性存在
        assert publisher._config is not None
        assert publisher._message_adapter is not None
        assert publisher._error_handler is not None
        assert publisher._degradation is not None
        assert publisher._node_manager is not None

def test_task_publisher_publish_task(mock_ros2_available):
    """测试发布取药任务"""
    with patch('backend.ros_integration.task_publisher.RosNodeManager') as mock_manager:
        mock_node = Mock()
        mock_publisher = Mock()
        mock_node.create_publisher.return_value = mock_publisher
        mock_manager.get_instance.return_value.get_node.return_value = mock_node

        publisher = TaskPublisher()

        # 确保发布器已初始化
        publisher._initialized = True
        publisher._new_publisher = mock_publisher

        # 模拟消息适配器
        mock_task_msg = Mock()
        mock_adapter = Mock()
        mock_adapter.backend_to_unity.return_value = mock_task_msg
        publisher._message_adapter = mock_adapter

        # 模拟降级模式允许发布
        mock_degradation = Mock()
        mock_degradation.can_publish.return_value = True
        publisher._degradation = mock_degradation

        # 测试数据
        backend_drug = {
            "drug_id": 1,
            "name": "布洛芬",
            "shelve_id": "A",
            "shelf_x": 2,
            "shelf_y": 3,
            "quantity": 10
        }

        success = publisher.publish_task(task_id=1001, drug=backend_drug, quantity=3)

        # 验证调用
        mock_adapter.backend_to_unity.assert_called_once_with(1001, backend_drug, 3)
        mock_publisher.publish.assert_called_once_with(mock_task_msg)
        mock_degradation.can_publish.assert_called_once()
        mock_degradation.record_success.assert_called_once()
        assert success == True

def test_task_publisher_publish_expiry_removal(mock_ros2_available):
    """测试发布过期清理任务"""
    with patch('backend.ros_integration.task_publisher.RosNodeManager') as mock_manager:
        mock_node = Mock()
        mock_publisher = Mock()
        mock_node.create_publisher.return_value = mock_publisher
        mock_manager.get_instance.return_value.get_node.return_value = mock_node

        publisher = TaskPublisher()

        # 确保发布器已初始化
        publisher._initialized = True
        publisher._new_publisher = mock_publisher

        # 模拟消息适配器
        mock_task_msg = Mock()
        mock_adapter = Mock()
        mock_adapter.expiry_to_unity.return_value = mock_task_msg
        publisher._message_adapter = mock_adapter

        # 模拟降级模式允许发布
        mock_degradation = Mock()
        mock_degradation.can_publish.return_value = True
        publisher._degradation = mock_degradation

        # 测试数据
        expired_drug = {
            "drug_id": 2,
            "name": "过期药品",
            "shelve_id": "B",
            "shelf_x": 5,
            "shelf_y": 1,
            "quantity": 8
        }

        success = publisher.publish_expiry_removal(drug=expired_drug, remove_quantity=8)

        # 验证调用
        mock_adapter.expiry_to_unity.assert_called_once_with(expired_drug, 8)
        mock_publisher.publish.assert_called_once_with(mock_task_msg)
        mock_degradation.can_publish.assert_called_once()
        assert success == True

def test_task_publisher_error_handling(mock_ros2_available):
    """测试任务发布错误处理"""
    with patch('backend.ros_integration.task_publisher.RosNodeManager') as mock_manager:
        mock_node = Mock()
        mock_manager.get_instance.return_value.get_node.return_value = mock_node

        publisher = TaskPublisher()

        # 确保发布器已初始化
        publisher._initialized = True
        mock_new_publisher = Mock()
        mock_new_publisher.publish.side_effect = Exception("ROS2 error")
        publisher._new_publisher = mock_new_publisher

        # 模拟消息适配器
        mock_task_msg = Mock()
        mock_adapter = Mock()
        mock_adapter.backend_to_unity.return_value = mock_task_msg
        publisher._message_adapter = mock_adapter

        # 模拟错误处理器
        mock_error_handler = Mock()
        mock_error_handler.handle_publish_error.return_value = {"status": "failed", "fallback": "log_only"}
        publisher._error_handler = mock_error_handler

        # 模拟降级模式允许发布
        mock_degradation = Mock()
        mock_degradation.can_publish.return_value = True
        publisher._degradation = mock_degradation

        backend_drug = {
            "drug_id": 1,
            "name": "测试药品",
            "shelve_id": "C",
            "shelf_x": 1,
            "shelf_y": 1,
            "quantity": 5
        }

        success = publisher.publish_task(task_id=1002, drug=backend_drug, quantity=2)

        # 验证错误处理被调用
        mock_error_handler.handle_publish_error.assert_called_once()
        mock_degradation.record_failure.assert_called_once()
        assert success == False

def test_task_publisher_graceful_degradation(mock_ros2_available):
    """测试优雅降级模式下的行为"""
    with patch('backend.ros_integration.task_publisher.RosNodeManager') as mock_manager:
        mock_node = Mock()
        mock_manager.get_instance.return_value.get_node.return_value = mock_node

        publisher = TaskPublisher()

        # 模拟降级模式
        mock_degradation = Mock()
        mock_degradation.can_publish.return_value = False  # 不能发布
        publisher._degradation = mock_degradation

        backend_drug = {
            "drug_id": 1,
            "name": "测试药品",
            "shelve_id": "C",
            "shelf_x": 1,
            "shelf_y": 1,
            "quantity": 5
        }

        success = publisher.publish_task(task_id=1003, drug=backend_drug, quantity=1)

        # 验证降级检查被调用
        mock_degradation.can_publish.assert_called_once()
        assert success == False  # 在降级模式下应返回False
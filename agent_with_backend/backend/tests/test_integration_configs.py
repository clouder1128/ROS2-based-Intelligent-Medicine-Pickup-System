"""
集成配置测试 - 测试不同配置模式
"""
import pytest
import os
from backend.ros_integration.config import Config

@pytest.mark.parametrize("mode,expected_topics", [
    ("new", ["/task_topic"]),  # 仅新话题
    ("legacy", ["/task_request"]),  # 仅旧话题
    ("parallel", ["/task_topic", "/task_request"]),  # 并行
])
def test_integration_modes(mode, expected_topics):
    """测试不同集成模式"""
    os.environ["ROS_INTEGRATION_MODE"] = mode
    config = Config()

    assert config.INTEGRATION_MODE == mode

    # 根据模式验证TopicPublisher的行为
    from backend.ros_integration.task_publisher import TaskPublisher
    from unittest.mock import Mock, patch

    with patch('backend.ros_integration.task_publisher.RosNodeManager') as mock_manager:
        mock_node = Mock()
        mock_manager.get_instance.return_value.get_node.return_value = mock_node

        publisher = TaskPublisher()

        # 验证根据模式创建的发布器数量
        if mode == "new":
            assert publisher._legacy_publisher is None
        elif mode == "legacy":
            assert publisher._new_publisher is None
        elif mode == "parallel":
            assert publisher._new_publisher is not None
            assert publisher._legacy_publisher is not None


def test_config_validation():
    """测试配置验证"""
    config = Config()

    # 有效配置
    config.INTEGRATION_MODE = "new"
    config.TCP_PORT = 10000
    assert config.validate() is True

    # 无效集成模式
    config.INTEGRATION_MODE = "invalid"
    with pytest.raises(ValueError):
        config.validate()

    # 无效端口
    config.INTEGRATION_MODE = "new"
    config.TCP_PORT = 0
    with pytest.raises(ValueError):
        config.validate()

    config.TCP_PORT = 65536
    with pytest.raises(ValueError):
        config.validate()


def test_topic_config_constants():
    """测试话题配置常量"""
    from backend.ros_integration.config import TopicConfig

    assert TopicConfig.TASK_TOPIC_NEW == "/task_topic"
    assert TopicConfig.TASK_TOPIC_LEGACY == "/task_request"
    assert TopicConfig.TASK_STATE_TOPIC == "/TaskState_U"
    assert TopicConfig.CAR_STATE_TOPIC == "/CarState_U"
    assert TopicConfig.CABINET_STATE_TOPIC == "/CabinetState_U"

    assert TopicConfig.QOS_DEPTH == 10
    assert TopicConfig.QOS_RELIABILITY == "RELIABLE"
    assert TopicConfig.QOS_DURABILITY == "VOLATILE"
"""配置管理测试"""

import os
import pytest
from backend.ros_integration.config import Config, TopicConfig

def test_config_default_values():
    """测试默认配置值"""
    config = Config()

    assert config.INTEGRATION_MODE == "new"
    assert config.ROS_NODE_NAME == "backend_ros_integration"
    assert config.TCP_PORT == 10000
    assert config.TASK_TOPIC_NEW == "/task_topic"
    assert config.TASK_TOPIC_LEGACY == "/task_request"

def test_config_environment_override():
    """测试环境变量覆盖"""
    os.environ["ROS_INTEGRATION_MODE"] = "parallel"
    os.environ["ROS_TCP_PORT"] = "20000"
    os.environ["ROS_IP"] = "127.0.0.1"

    config = Config()

    assert config.INTEGRATION_MODE == "parallel"
    assert config.TCP_PORT == 20000
    assert config.TCP_IP == "127.0.0.1"

    # 清理环境变量
    del os.environ["ROS_INTEGRATION_MODE"]
    del os.environ["ROS_TCP_PORT"]
    del os.environ["ROS_IP"]

def test_config_validation():
    """测试配置验证"""
    config = Config()
    assert config.validate() == True

    # 测试无效模式
    config.INTEGRATION_MODE = "invalid"
    with pytest.raises(ValueError, match="Invalid INTEGRATION_MODE"):
        config.validate()

    # 恢复有效模式
    config.INTEGRATION_MODE = "new"

def test_topic_config_constants():
    """测试话题配置常量"""
    assert TopicConfig.TASK_TOPIC_NEW == "/task_topic"
    assert TopicConfig.TASK_TOPIC_LEGACY == "/task_request"
    assert TopicConfig.TASK_STATE_TOPIC == "/TaskState_U"
    assert TopicConfig.QOS_DEPTH == 10
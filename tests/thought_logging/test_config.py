# tests/thought_logging/test_config.py
import os
import pytest
from unittest.mock import patch
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_config_defaults():
    """测试配置默认值"""
    config = ThoughtLoggingConfig()
    assert config.enabled == False
    assert config.log_level == "DETAILED"
    assert config.log_to_file == True
    assert config.log_to_console == False

def test_config_from_env():
    """测试从环境变量加载配置"""
    with patch.dict(os.environ, {
        "ENABLE_THOUGHT_LOGGING": "true",
        "THOUGHT_LOG_LEVEL": "DEBUG",
        "THOUGHT_LOG_TO_CONSOLE": "true"
    }):
        config = ThoughtLoggingConfig()
        assert config.enabled == True
        assert config.log_level == "DEBUG"
        assert config.log_to_console == True

def test_config_validation():
    """测试配置验证"""
    config = ThoughtLoggingConfig()
    config.log_level = "INVALID"
    with pytest.raises(ValueError):
        config.validate()
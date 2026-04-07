# conftest.py
"""Pytest配置文件，包含测试fixture和配置"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, Generator

# 设置测试环境变量
os.environ["LLM_PROVIDER"] = "claude"
os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["LLM_MODEL"] = "claude-3-sonnet-20240229"
os.environ["LLM_MAX_TOKENS"] = "4096"
os.environ["LLM_TEMPERATURE"] = "0.3"
os.environ["PHARMACY_BASE_URL"] = "http://localhost:8001"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["MAX_HISTORY_LEN"] = "20"
os.environ["MAX_ITERATIONS"] = "10"
os.environ["SESSION_STATE_DIR"] = "./test_sessions"
os.environ["ENABLE_ASYNC"] = "false"
os.environ["MAX_CONCURRENT_SESSIONS"] = "100"
os.environ["REQUEST_TIMEOUT"] = "30"


@pytest.fixture
def temp_session_dir() -> Generator[str, None, None]:
    """创建临时会话目录的fixture

    Yields:
        str: 临时目录路径
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # 设置环境变量
        original_dir = os.environ.get("SESSION_STATE_DIR")
        os.environ["SESSION_STATE_DIR"] = temp_dir

        yield temp_dir

        # 恢复原始环境变量
        if original_dir:
            os.environ["SESSION_STATE_DIR"] = original_dir
        else:
            del os.environ["SESSION_STATE_DIR"]


@pytest.fixture
def mock_llm_response() -> Dict[str, Any]:
    """创建模拟LLM响应的fixture

    Returns:
        Dict[str, Any]: 模拟的LLM响应
    """
    return {
        "content": "这是一个测试回复",
        "role": "assistant",
        "model": "claude-3-sonnet-20240229",
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50
        }
    }


@pytest.fixture
def mock_llm_response_with_tools() -> Dict[str, Any]:
    """创建包含工具调用的模拟LLM响应的fixture

    Returns:
        Dict[str, Any]: 包含工具调用的模拟LLM响应
    """
    return {
        "tool_calls": [
            {
                "name": "query_drug",
                "input": {"symptoms": "头痛"}
            }
        ],
        "role": "assistant",
        "model": "claude-3-sonnet-20240229",
        "usage": {
            "input_tokens": 120,
            "output_tokens": 80
        }
    }


@pytest.fixture
def mock_tool_executor() -> Mock:
    """创建模拟工具执行器的fixture

    Returns:
        Mock: 模拟的工具执行器
    """
    mock_executor = Mock()
    mock_executor.execute_tool.return_value = {
        "success": True,
        "result": {"drugs": ["布洛芬"]},
        "message": "工具执行成功"
    }
    mock_executor.get_tool_info.return_value = {
        "name": "query_drug",
        "description": "查询药物信息",
        "parameters": {
            "symptoms": {"type": "string", "description": "症状描述"}
        }
    }
    return mock_executor


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """创建模拟配置的fixture

    Returns:
        Dict[str, Any]: 模拟配置字典
    """
    return {
        "LLM_PROVIDER": "claude",
        "LLM_MODEL": "claude-3-sonnet-20240229",
        "LLM_MAX_TOKENS": 4096,
        "LLM_TEMPERATURE": 0.3,
        "PHARMACY_BASE_URL": "http://localhost:8001",
        "DATABASE_URL": "sqlite:///:memory:",
        "LOG_LEVEL": "WARNING",
        "MAX_HISTORY_LEN": 20,
        "MAX_ITERATIONS": 10,
        "SESSION_STATE_DIR": "./test_sessions",
        "ENABLE_ASYNC": False,
        "MAX_CONCURRENT_SESSIONS": 100,
        "REQUEST_TIMEOUT": 30
    }


@pytest.fixture
def patch_config() -> Generator[None, None, None]:
    """临时修改配置的fixture

    Yields:
        None
    """
    # 保存原始配置值
    original_values = {}
    config_attrs = [
        "LLM_PROVIDER", "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
        "LLM_MODEL", "LLM_MAX_TOKENS", "LLM_TEMPERATURE",
        "PHARMACY_BASE_URL", "DATABASE_URL", "LOG_LEVEL",
        "MAX_HISTORY_LEN", "MAX_ITERATIONS", "SESSION_STATE_DIR",
        "ENABLE_ASYNC", "MAX_CONCURRENT_SESSIONS", "REQUEST_TIMEOUT"
    ]

    from config import Config

    for attr in config_attrs:
        if hasattr(Config, attr):
            original_values[attr] = getattr(Config, attr)

    yield

    # 恢复原始配置值
    for attr, value in original_values.items():
        setattr(Config, attr, value)


@pytest.fixture
def invalid_config_values() -> Dict[str, Any]:
    """提供无效配置值的fixture

    Returns:
        Dict[str, Any]: 无效配置值字典
    """
    return {
        "LLM_PROVIDER": "invalid_provider",
        "MAX_ITERATIONS": 0,
        "LLM_TEMPERATURE": 3.0,
        "MAX_CONCURRENT_SESSIONS": -1,
        "REQUEST_TIMEOUT": 0
    }
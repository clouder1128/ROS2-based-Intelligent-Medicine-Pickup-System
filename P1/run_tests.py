#!/usr/bin/env python3
"""运行所有测试"""
import sys
import os
import pytest

if __name__ == "__main__":
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.dirname(__file__))

    # 尝试从sys.path中移除ROS路径（如果存在）
    ros_paths = [p for p in sys.path if 'ros' in p.lower()]
    for ros_path in ros_paths:
        if ros_path in sys.path:
            sys.path.remove(ros_path)

    # 设置环境变量（模拟conftest.py）
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

    # 设置PYTEST_PLUGINS为空，防止加载ROS插件
    os.environ["PYTEST_PLUGINS"] = ""

    # 运行pytest测试，禁用ROS插件
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-p", "no:launch_testing_ros_pytest_entrypoint",
        "-p", "no:launch_testing_ros",
        "-p", "no:launch_testing",
        "-p", "no:ament_pep257",
        "-p", "no:ament_lint",
        "-p", "no:ament_xmllint",
        "-p", "no:ament_copyright",
        "-p", "no:ament_flake8"
    ])

    sys.exit(exit_code)
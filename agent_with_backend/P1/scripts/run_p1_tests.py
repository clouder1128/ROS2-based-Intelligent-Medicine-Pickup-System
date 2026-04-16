#!/usr/bin/env python3
"""运行所有测试"""

import sys
import os
import pytest
import argparse


def run_integration_tests():
    """Run integration tests (requires backend running)"""
    print("Running integration tests...")
    print("Note: Backend service must be running on port 8001")
    print()

    # Set environment variable to enable integration tests
    os.environ["RUN_INTEGRATION_TESTS"] = "1"

    # Run integration tests
    result = pytest.main(["tests/integration/", "-v", "--tb=short"])

    return result == 0


def run_unit_tests():
    """Run unit tests only"""
    print("Running unit tests...")

    # Run unit tests (excluding integration tests)
    result = pytest.main(
        [
            "tests/",
            "-v",
            "--tb=short",
            "--disable-warnings",
            "-p",
            "no:launch_testing_ros_pytest_entrypoint",
            "-p",
            "no:launch_testing_ros",
            "-p",
            "no:launch_testing",
            "-p",
            "no:ament_pep257",
            "-p",
            "no:ament_lint",
            "-p",
            "no:ament_xmllint",
            "-p",
            "no:ament_copyright",
            "-p",
            "no:ament_flake8",
            "-k",
            "not integration",
        ]
    )

    return result == 0


def run_all_tests():
    """Run all tests (unit tests only by default)"""
    print("Running all tests (excluding integration tests)...")
    print("Use --integration to run integration tests")
    print()

    # Run all tests except integration tests
    result = pytest.main(
        [
            "tests/",
            "-v",
            "--tb=short",
            "--disable-warnings",
            "-p",
            "no:launch_testing_ros_pytest_entrypoint",
            "-p",
            "no:launch_testing_ros",
            "-p",
            "no:launch_testing",
            "-p",
            "no:ament_pep257",
            "-p",
            "no:ament_lint",
            "-p",
            "no:ament_xmllint",
            "-p",
            "no:ament_copyright",
            "-p",
            "no:ament_flake8",
            "-k",
            "not integration",
        ]
    )

    return result == 0


def setup_environment():
    """Setup test environment variables"""
    # 添加项目根目录到Python路径
    # Since this file is now in scripts/, we need to go up one level to get P1 root
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)  # Go up from scripts/ to P1/
    sys.path.insert(0, project_root)

    # 尝试从sys.path中移除ROS路径（如果存在）
    ros_paths = [p for p in sys.path if "ros" in p.lower()]
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run tests for P1 project")
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests (requires backend running)",
    )
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")

    args = parser.parse_args()

    # Setup environment
    setup_environment()

    # Determine which tests to run
    success = True

    if args.integration:
        success = run_integration_tests()
    elif args.unit:
        success = run_unit_tests()
    else:
        # Default: run all tests (excluding integration)
        success = run_all_tests()

    sys.exit(0 if success else 1)

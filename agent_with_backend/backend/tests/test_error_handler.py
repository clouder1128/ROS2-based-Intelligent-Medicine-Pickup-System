"""错误处理器测试"""

import pytest
import time
from unittest.mock import Mock, patch
from backend.ros_integration.error_handler import ErrorHandler, GracefulDegradation

def test_error_handler_initialization():
    """测试错误处理器初始化"""
    handler = ErrorHandler()

    assert handler.ERROR_LEVELS["CRITICAL"] == 0
    assert handler.ERROR_LEVELS["HIGH"] == 1
    assert handler.ERROR_LEVELS["MEDIUM"] == 2
    assert handler.ERROR_LEVELS["LOW"] == 3

def test_handle_ros_connection_error():
    """测试ROS连接错误处理"""
    handler = ErrorHandler()

    # 模拟ROS连接错误
    mock_error = Mock()
    mock_error.__class__.__name__ = "RCLError"

    with patch('backend.ros_integration.error_handler.rclpy') as mock_rclpy:
        mock_rclpy.ok.return_value = False

        result = handler._handle_ros_connection_error(mock_error)

        assert "status" in result
        assert "recovery_attempted" in result

def test_handle_timeout_error():
    """测试超时错误处理"""
    handler = ErrorHandler()

    timeout_error = TimeoutError("Publish timeout")

    result = handler._handle_timeout_error(timeout_error, task_id=1001, retry_strategy="exponential")

    assert "status" in result
    assert "retry_scheduled" in result
    assert result["task_id"] == 1001

def test_graceful_degradation_initialization():
    """测试优雅降级初始化"""
    degradation = GracefulDegradation()

    assert degradation.DEGRADATION_MODES["FULL"] == 0
    assert degradation.DEGRADATION_MODES["PUBLISH_ONLY"] == 1
    assert degradation.DEGRADATION_MODES["LOG_ONLY"] == 2
    assert degradation.DEGRADATION_MODES["DISABLED"] == 3

    assert degradation._current_mode == degradation.DEGRADATION_MODES["FULL"]
    assert degradation._failure_count == 0

def test_graceful_degradation_check_and_degrade():
    """测试优雅降级检查"""
    degradation = GracefulDegradation()

    # 初始状态应为FULL
    assert degradation._current_mode == degradation.DEGRADATION_MODES["FULL"]

    # 场景1: 冷却期过后降级
    degradation._failure_count = 5  # 达到FULL模式阈值
    degradation._last_failure_time = time.time() - 70  # 70秒前，超过60秒冷却期

    degradation.check_and_degrade()

    # 应该降级到PUBLISH_ONLY
    assert degradation._current_mode == degradation.DEGRADATION_MODES["PUBLISH_ONLY"]
    # 降级后失败计数应重置
    assert degradation._failure_count == 0

    # 场景2: 冷却期内不降级
    degradation._current_mode = degradation.DEGRADATION_MODES["FULL"]
    degradation._failure_count = 5
    degradation._last_failure_time = time.time() - 10  # 10秒前，小于60秒冷却期

    degradation.check_and_degrade()

    # 应该保持FULL（冷却期内）
    assert degradation._current_mode == degradation.DEGRADATION_MODES["FULL"]

def test_graceful_degradation_reset():
    """测试优雅降级重置"""
    degradation = GracefulDegradation()

    # 设置为降级模式
    degradation._current_mode = degradation.DEGRADATION_MODES["LOG_ONLY"]
    degradation._failure_count = 20

    degradation.reset()

    assert degradation._current_mode == degradation.DEGRADATION_MODES["FULL"]
    assert degradation._failure_count == 0
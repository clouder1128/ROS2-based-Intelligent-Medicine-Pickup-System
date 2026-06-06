"""HealthMonitor 健康监控器单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from ros_integration.health_monitor import HealthMonitor
from ros_integration.node_manager import RosNodeManager
from ros_integration.error_handler import ErrorHandler, GracefulDegradation


class TestHealthMonitorInit:
    def test_initial_state(self):
        hm = HealthMonitor()
        assert hm._running is False
        assert hm._monitor_thread is None
        assert hm._last_check_time == 0
        assert hm._connection_healthy is False
        assert hm._error_rate == 0.0
        assert hm._consecutive_failures == 0

    def test_initial_get_health_status(self):
        hm = HealthMonitor()
        status = hm.get_health_status()
        assert status["running"] is False
        assert status["connection_healthy"] is False
        assert status["error_rate"] == 0.0
        assert status["degradation_mode"] == "FULL"

    def test_initial_is_healthy_false(self):
        hm = HealthMonitor()
        assert hm.is_healthy() is False


class TestStartStop:
    def test_start_creates_monitor_thread(self):
        hm = HealthMonitor()
        hm.start()
        assert hm._running is True
        assert hm._monitor_thread is not None
        assert hm._monitor_thread.daemon is True
        hm.stop()

    def test_double_start_is_noop(self):
        hm = HealthMonitor()
        hm.start()
        thread = hm._monitor_thread
        hm.start()  # should not replace thread
        assert hm._monitor_thread is thread
        hm.stop()

    def test_stop_joins_thread(self):
        hm = HealthMonitor()
        hm.start()
        hm.stop()
        assert hm._running is False
        assert hm._monitor_thread is None

    def test_stop_when_not_started(self):
        hm = HealthMonitor()
        hm.stop()  # should not raise


class TestPerformHealthCheck:
    def test_perform_check_updates_timestamp(self):
        hm = HealthMonitor()
        hm._last_check_time = 0
        hm._perform_health_check()
        assert hm._last_check_time > 0

    def test_perform_check_updates_connection_healthy(self):
        hm = HealthMonitor()
        # node_manager.check_connection() 返回 True
        hm._node_manager.check_connection = MagicMock(return_value=True)
        hm._perform_health_check()
        assert hm._connection_healthy is True

    def test_perform_check_with_connection_failure(self):
        hm = HealthMonitor()
        hm._node_manager.check_connection = MagicMock(return_value=False)
        hm._perform_health_check()
        assert hm._connection_healthy is False

    def test_perform_check_increments_consecutive_failures(self):
        hm = HealthMonitor()
        hm._consecutive_failures = 0
        hm._node_manager.check_connection = MagicMock(return_value=False)
        hm._perform_health_check()
        assert hm._consecutive_failures == 1

    def test_perform_check_decreases_consecutive_failures_on_success(self):
        hm = HealthMonitor()
        hm._consecutive_failures = 3
        hm._node_manager.check_connection = MagicMock(return_value=True)
        hm._perform_health_check()
        assert hm._consecutive_failures == 2  # max(0, 3-1)


class TestIsHealthy:
    def test_is_healthy_true(self):
        hm = HealthMonitor()
        hm._connection_healthy = True
        hm._error_rate = 0.0
        assert hm.is_healthy() is True

    def test_is_healthy_false_when_not_connected(self):
        hm = HealthMonitor()
        hm._connection_healthy = False
        hm._error_rate = 0.0
        assert hm.is_healthy() is False

    def test_is_healthy_false_when_high_error_rate(self):
        hm = HealthMonitor()
        hm._connection_healthy = True
        hm._error_rate = 0.5
        assert hm.is_healthy() is False


class TestCheckDegradation:
    def test_degradation_failure_on_connection_lost(self):
        hm = HealthMonitor()
        hm._connection_healthy = False
        old_count = hm._degradation._failure_count
        hm._check_degradation()
        assert hm._degradation._failure_count > old_count

    def test_degradation_success_on_connection_good(self):
        hm = HealthMonitor()
        hm._connection_healthy = True
        hm._degradation._failure_count = 5
        hm._check_degradation()
        assert hm._degradation._failure_count == 4


class TestReset:
    def test_reset_clears_state(self):
        hm = HealthMonitor()
        hm._last_error_count = 10
        hm._consecutive_failures = 5
        hm._error_rate = 0.8
        hm.reset()
        assert hm._last_error_count == 0
        assert hm._consecutive_failures == 0
        assert hm._error_rate == 0.0

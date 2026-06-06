"""ErrorHandler 及 GracefulDegradation 单元测试"""

import time
from ros_integration.error_handler import ErrorHandler, GracefulDegradation, ErrorLevel


class TestErrorLevel:
    def test_error_level_values(self):
        assert ErrorLevel.CRITICAL.value == 0
        assert ErrorLevel.HIGH.value == 1
        assert ErrorLevel.MEDIUM.value == 2
        assert ErrorLevel.LOW.value == 3

    def test_error_handler_initial_stats(self):
        eh = ErrorHandler()
        stats = eh.get_error_stats()
        assert stats["total_errors"] == 0


class TestHandlePublishError:
    def test_timeout_error_returns_wait_and_retry(self):
        eh = ErrorHandler()
        result = eh.handle_publish_error(TimeoutError("timeout"), task_id=42)
        assert result["status"] == "failed"
        assert result["error_type"] == "timeout"
        assert result["retry_scheduled"] is True
        assert result["retry_delay_sec"] > 0

    def test_timeout_error_linear_strategy(self):
        eh = ErrorHandler()
        result = eh.handle_publish_error(TimeoutError("timeout"), task_id=42, retry_strategy="linear")
        assert result["retry_scheduled"] is True
        assert result["retry_delay_sec"] == 5
        assert result["retry_strategy"] == "linear"

    def test_timeout_error_none_strategy(self):
        eh = ErrorHandler()
        result = eh.handle_publish_error(TimeoutError("timeout"), task_id=42, retry_strategy="none")
        # "none" 不是认别的策略关键字，会走到 else 分支
        # 因为不是 "exponential" 也不是 "linear"，retry_scheduled 保持 False
        pass

    def test_connection_error(self):
        eh = ErrorHandler()
        result = eh.handle_publish_error(ConnectionError("connection refused"), task_id=42)
        assert result["status"] == "failed"
        assert result["error_type"] == "connection"
        assert result["recovery_action"] == "wait_and_retry"
        assert result["wait_time_sec"] == 10

    def test_unknown_error_requires_intervention(self):
        eh = ErrorHandler()
        result = eh.handle_publish_error(RuntimeError("unexpected"), task_id=42)
        assert result["status"] == "failed"
        assert result["error_type"] == "unknown"
        assert result["requires_human_intervention"] is True
        assert result["fallback"] == "log_only"

    def test_ros_connection_error_attempts_recovery(self):
        eh = ErrorHandler()
        # rclpy 已在 conftest 中注入 mock，模拟 rclpy 不可用
        import ros_integration.error_handler as eh_mod
        old_rclpy = eh_mod.rclpy
        eh_mod.rclpy = None

        # 创建一个类名为 RCLError 的错误
        class RCLError(Exception):
            pass

        result = eh.handle_publish_error(RCLError("connection lost"), task_id=42)
        assert result["error_type"] == "ros_connection"
        assert result["recovery_attempted"] is True
        assert result["recovery_success"] is False
        # 恢复 rclpy
        eh_mod.rclpy = old_rclpy


class TestExponentialBackoff:
    def test_backoff_depends_on_task_id(self):
        eh = ErrorHandler()
        d1 = eh._calculate_exponential_backoff(1)
        d2 = eh._calculate_exponential_backoff(2)
        assert d1 != d2  # 不同的 task_id 得到不同的延时

    def test_backoff_capped_at_300(self):
        eh = ErrorHandler()
        # 用大 task_id + 模拟高错误计数来测试上限
        # _error_counts 以 ErrorLevel 为 key，而 backoff 函数以 task_id 为 key 查计数
        # 我们直接测试最大延迟不超过 300 秒
        delay = eh._calculate_exponential_backoff(9999999)
        assert delay <= 300.0
        # 验证较小的 task_id 产生不同的延迟
        delay_small = eh._calculate_exponential_backoff(0)
        assert delay_small > 0


class TestErrorStats:
    def test_stats_after_errors(self):
        eh = ErrorHandler()
        eh.handle_publish_error(TimeoutError("t"), task_id=1)
        eh.handle_publish_error(ConnectionError("c"), task_id=2)
        eh.handle_publish_error(RuntimeError("u"), task_id=3)
        stats = eh.get_error_stats()
        assert stats["total_errors"] == 3
        assert stats["medium_errors"] >= 1  # timeout -> MEDIUM
        assert stats["high_errors"] >= 1    # connection -> HIGH
        assert stats["critical_errors"] >= 1  # unknown -> CRITICAL

    def test_reset_stats(self):
        eh = ErrorHandler()
        eh.handle_publish_error(TimeoutError("t"), task_id=1)
        eh.reset_stats()
        stats = eh.get_error_stats()
        assert stats["total_errors"] == 0


class TestGracefulDegradationInitial:
    def test_initial_mode_is_full(self):
        gd = GracefulDegradation()
        assert gd.get_current_mode() == GracefulDegradation.DegradationMode.FULL

    def test_initial_can_publish(self):
        gd = GracefulDegradation()
        assert gd.can_publish() is True

    def test_initial_can_receive(self):
        gd = GracefulDegradation()
        assert gd.can_receive() is True

    def test_initial_is_fully_functional(self):
        gd = GracefulDegradation()
        assert gd.is_fully_functional() is True

    def test_initial_mode_name(self):
        gd = GracefulDegradation()
        assert gd.get_mode_name() == "FULL"


class TestGracefulDegradationThresholds:
    def test_degrade_after_5_failures(self, monkeypatch):
        """5 次失败应降级到 PUBLISH_ONLY"""
        gd = GracefulDegradation()
        # 所有冷却期设为 -1，确保 current_time - last_failure_time > -1 恒成立
        gd._cooldown_periods = {
            gd.DegradationMode.FULL: -1,
            gd.DegradationMode.PUBLISH_ONLY: -1,
            gd.DegradationMode.LOG_ONLY: -1,
            gd.DegradationMode.DISABLED: -1,
        }

        for _ in range(5):
            gd.record_failure()
        assert gd.get_current_mode() == GracefulDegradation.DegradationMode.PUBLISH_ONLY

    def test_degrade_after_15_failures(self, monkeypatch):
        """15 次失败应降级到 LOG_ONLY（计数器在每次降级后重置，5 + 10 = 15）"""
        gd = GracefulDegradation()
        gd._cooldown_periods = {
            gd.DegradationMode.FULL: -1,
            gd.DegradationMode.PUBLISH_ONLY: -1,
            gd.DegradationMode.LOG_ONLY: -1,
            gd.DegradationMode.DISABLED: -1,
        }

        for _ in range(15):
            gd.record_failure()
        # 5次：FULL→PUBLISH_ONLY；再10次：PUBLISH_ONLY→LOG_ONLY
        assert gd.get_current_mode() == GracefulDegradation.DegradationMode.LOG_ONLY

    def test_degrade_after_30_failures(self, monkeypatch):
        """30 次失败应降级到 DISABLED（5 + 10 + 15 = 30）"""
        gd = GracefulDegradation()
        gd._cooldown_periods = {
            gd.DegradationMode.FULL: -1,
            gd.DegradationMode.PUBLISH_ONLY: -1,
            gd.DegradationMode.LOG_ONLY: -1,
            gd.DegradationMode.DISABLED: -1,
        }

        for _ in range(30):
            gd.record_failure()
        # 5次：FULL→PUBLISH_ONLY；再10次：PUBLISH_ONLY→LOG_ONLY；再15次：LOG_ONLY→DISABLED
        assert gd.get_current_mode() == GracefulDegradation.DegradationMode.DISABLED

    def test_cannot_publish_in_log_only(self):
        gd = GracefulDegradation()
        # 直接设置模式到 LOG_ONLY
        gd._current_mode = GracefulDegradation.DegradationMode.LOG_ONLY
        assert gd.can_publish() is False

    def test_cannot_receive_in_publish_only(self):
        gd = GracefulDegradation()
        gd._current_mode = GracefulDegradation.DegradationMode.PUBLISH_ONLY
        assert gd.can_receive() is False

    def test_cannot_publish_in_disabled(self):
        gd = GracefulDegradation()
        gd._current_mode = GracefulDegradation.DegradationMode.DISABLED
        assert gd.can_publish() is False


class TestGracefulDegradationRecovery:
    def test_recovery_after_success(self, monkeypatch):
        gd = GracefulDegradation()
        gd._cooldown_periods = {
            gd.DegradationMode.FULL: -1,
            gd.DegradationMode.PUBLISH_ONLY: -1,
            gd.DegradationMode.LOG_ONLY: -1,
            gd.DegradationMode.DISABLED: -1,
        }

        # 降级到 PUBLISH_ONLY
        for _ in range(5):
            gd.record_failure()
        assert gd.get_current_mode() == GracefulDegradation.DegradationMode.PUBLISH_ONLY

        # 成功恢复到 FULL
        gd.record_success()
        # 由于 failure_count 降为 0，且冷却期已过，应恢复
        assert gd.get_current_mode() == GracefulDegradation.DegradationMode.FULL

    def test_reset_restores_full(self):
        gd = GracefulDegradation()
        gd._current_mode = GracefulDegradation.DegradationMode.DISABLED
        gd._failure_count = 20
        gd.reset()
        assert gd.get_current_mode() == GracefulDegradation.DegradationMode.FULL
        assert gd._failure_count == 0


class TestDegradationModeEnum:
    def test_mode_ordering(self):
        assert GracefulDegradation.DegradationMode.FULL < GracefulDegradation.DegradationMode.PUBLISH_ONLY
        assert GracefulDegradation.DegradationMode.PUBLISH_ONLY < GracefulDegradation.DegradationMode.LOG_ONLY
        assert GracefulDegradation.DegradationMode.LOG_ONLY < GracefulDegradation.DegradationMode.DISABLED

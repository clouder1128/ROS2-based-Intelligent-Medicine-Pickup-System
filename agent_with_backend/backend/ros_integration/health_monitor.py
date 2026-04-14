"""
健康监控器 - 监控ROS2集成健康状态
定期检查连接状态、错误率，触发降级恢复
"""

import threading
import time
from typing import Dict, Any
from backend.ros_integration.config import Config
from backend.ros_integration.node_manager import RosNodeManager
from backend.ros_integration.error_handler import ErrorHandler, GracefulDegradation

class HealthMonitor:
    """
    健康监控器 - 定期检查系统健康状态
    """

    def __init__(self):
        """初始化健康监控器"""
        self._config = Config()
        self._node_manager = RosNodeManager.get_instance()
        self._error_handler = ErrorHandler()
        self._degradation = GracefulDegradation()

        # 监控状态
        self._running = False
        self._monitor_thread = None
        self._last_check_time = 0

        # 健康指标
        self._connection_healthy = False
        self._error_rate = 0.0
        self._last_error_count = 0
        self._consecutive_failures = 0

    def start(self):
        """启动健康监控器"""
        if self._running:
            print("[HealthMonitor] Already running")
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="health_monitor"
        )
        self._monitor_thread.start()
        print("[HealthMonitor] Started")

    def stop(self):
        """停止健康监控器"""
        self._running = False
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        print("[HealthMonitor] Stopped")

    def _monitor_loop(self):
        """监控循环"""
        check_interval = self._config.HEALTH_CHECK_INTERVAL_SEC

        while self._running:
            try:
                self._perform_health_check()
            except Exception as e:
                print(f"[HealthMonitor] Error in health check: {e}")

            # 等待下一次检查
            time.sleep(check_interval)

    def _perform_health_check(self):
        """执行健康检查"""
        current_time = time.time()

        # 检查ROS2连接状态
        connection_ok = self._node_manager.check_connection()
        self._connection_healthy = connection_ok

        # 检查错误统计
        error_stats = self._error_handler.get_error_stats()
        total_errors = error_stats.get("total_errors", 0)

        # 计算错误率（简单实现）
        if self._last_error_count > 0:
            error_increase = total_errors - self._last_error_count
            # 简单错误率计算
            self._error_rate = min(error_increase / 10.0, 1.0)  # 假设最多10次错误

        self._last_error_count = total_errors

        # 更新连续失败计数
        if not connection_ok:
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = max(0, self._consecutive_failures - 1)

        # 检查是否需要降级或恢复
        self._check_degradation()

        # 记录检查时间
        self._last_check_time = current_time

        # 打印健康状态
        if not connection_ok:
            print(f"[HealthMonitor] Connection unhealthy, consecutive failures: {self._consecutive_failures}")
        elif self._error_rate > 0.5:
            print(f"[HealthMonitor] High error rate: {self._error_rate:.2f}")

    def _check_degradation(self):
        """检查是否需要降级或恢复"""
        # 如果连接失败多次，记录失败（触发降级）
        if not self._connection_healthy:
            self._degradation.record_failure()
        else:
            # 连接健康时记录成功（可能触发恢复）
            self._degradation.record_success()

        # 获取当前模式
        current_mode = self._degradation.get_mode_name()
        if current_mode != "FULL" and self._connection_healthy and self._error_rate < 0.1:
            # 条件良好，尝试恢复
            print(f"[HealthMonitor] Conditions good, attempting recovery from {current_mode}")

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "running": self._running,
            "connection_healthy": self._connection_healthy,
            "error_rate": self._error_rate,
            "consecutive_failures": self._consecutive_failures,
            "degradation_mode": self._degradation.get_mode_name(),
            "last_check_time": self._last_check_time
        }

    def is_healthy(self) -> bool:
        """检查系统是否健康"""
        return self._connection_healthy and self._error_rate < 0.3

    def reset(self):
        """重置健康监控器"""
        self._last_error_count = 0
        self._consecutive_failures = 0
        self._error_rate = 0.0
        print("[HealthMonitor] Reset")
"""
错误处理与优雅降级 - 分级错误处理策略
"""

import time
import logging
from typing import Dict, Any
from enum import IntEnum
from .config import Config

# 条件导入ROS2模块，避免硬依赖
try:
    import rclpy
except ImportError:
    rclpy = None

class ErrorLevel(IntEnum):
    """错误级别枚举"""
    CRITICAL = 0  # 需要立即停机
    HIGH = 1      # 功能严重降级
    MEDIUM = 2    # 部分功能受影响
    LOW = 3       # 可自动恢复

class ErrorHandler:
    """
    错误处理器 - 分级错误处理策略
    """

    # 为测试兼容性提供字典
    ERROR_LEVELS = {
        "CRITICAL": ErrorLevel.CRITICAL,
        "HIGH": ErrorLevel.HIGH,
        "MEDIUM": ErrorLevel.MEDIUM,
        "LOW": ErrorLevel.LOW
    }

    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)

        # 错误统计
        self._error_counts = {
            ErrorLevel.CRITICAL: 0,
            ErrorLevel.HIGH: 0,
            ErrorLevel.MEDIUM: 0,
            ErrorLevel.LOW: 0
        }
        self._last_error_time = {}

    def handle_publish_error(self, error: Exception, task_id: int, retry_strategy: str = "exponential") -> Dict[str, Any]:
        """
        处理发布任务错误

        Args:
            error: 异常对象
            task_id: 任务ID
            retry_strategy: 重试策略 ("exponential", "linear", "none")

        Returns:
            处理结果字典
        """
        error_name = error.__class__.__name__

        # 根据错误类型分类处理
        if "RCLError" in error_name or "ROS" in error_name:
            # ROS2连接错误
            return self._handle_ros_connection_error(error)

        elif isinstance(error, TimeoutError):
            # 超时错误
            return self._handle_timeout_error(error, task_id, retry_strategy)

        elif isinstance(error, ConnectionError):
            # 连接错误
            return self._handle_connection_error(error, task_id)

        else:
            # 未知错误
            return self._handle_unknown_error(error, task_id)

    def _handle_ros_connection_error(self, error: Exception) -> Dict[str, Any]:
        """处理ROS2连接错误"""
        self._record_error(ErrorLevel.HIGH)

        result = {
            "status": "failed",
            "error_type": "ros_connection",
            "error_message": str(error),
            "recovery_attempted": False,
            "fallback": "log_only"
        }

        # 尝试重新连接
        try:
            if rclpy is None:
                raise ImportError("rclpy not available")

            if not rclpy.ok():
                rclpy.init()
                result["recovery_attempted"] = True
                result["recovery_success"] = True
                result["fallback"] = "retry"
            else:
                result["recovery_attempted"] = False
                result["recovery_success"] = None

        except Exception as recovery_error:
            result["recovery_attempted"] = True
            result["recovery_success"] = False
            result["recovery_error"] = str(recovery_error)

        self.logger.error(f"ROS connection error: {error}, recovery attempted: {result['recovery_attempted']}")
        return result

    def _handle_timeout_error(self, error: TimeoutError, task_id: int, retry_strategy: str) -> Dict[str, Any]:
        """处理超时错误"""
        self._record_error(ErrorLevel.MEDIUM)

        result = {
            "status": "failed",
            "error_type": "timeout",
            "error_message": str(error),
            "task_id": task_id,
            "retry_scheduled": False,
            "fallback": "queue_for_retry"
        }

        # 根据重试策略调度重试
        if retry_strategy == "exponential":
            retry_delay = self._calculate_exponential_backoff(task_id)
            result["retry_scheduled"] = True
            result["retry_delay_sec"] = retry_delay
            result["retry_strategy"] = "exponential"

        elif retry_strategy == "linear":
            result["retry_scheduled"] = True
            result["retry_delay_sec"] = 5  # 固定5秒延迟
            result["retry_strategy"] = "linear"

        self.logger.warning(f"Publish timeout for task {task_id}: {error}, retry scheduled: {result['retry_scheduled']}")
        return result

    def _handle_connection_error(self, error: ConnectionError, task_id: int) -> Dict[str, Any]:
        """处理连接错误"""
        self._record_error(ErrorLevel.HIGH)

        result = {
            "status": "failed",
            "error_type": "connection",
            "error_message": str(error),
            "task_id": task_id,
            "recovery_action": "wait_and_retry",
            "wait_time_sec": 10,
            "fallback": "queue_for_retry"
        }

        self.logger.error(f"Connection error for task {task_id}: {error}")
        return result

    def _handle_unknown_error(self, error: Exception, task_id: int) -> Dict[str, Any]:
        """处理未知错误"""
        self._record_error(ErrorLevel.CRITICAL)

        result = {
            "status": "failed",
            "error_type": "unknown",
            "error_message": str(error),
            "task_id": task_id,
            "fallback": "log_only",
            "requires_human_intervention": True
        }

        self.logger.critical(f"Unknown error for task {task_id}: {error}", exc_info=True)
        return result

    def _calculate_exponential_backoff(self, task_id: int) -> float:
        """计算指数退避延迟"""
        # 基于任务ID的简单哈希确定基础延迟
        base_delay = (task_id % 10) + 1  # 1-10秒

        # 获取该任务的错误计数
        error_count = self._error_counts.get(task_id, 0)

        # 指数退避: base_delay * 2^error_count
        delay = base_delay * (2 ** min(error_count, 5))  # 最大2^5=32倍

        # 限制最大延迟为300秒（5分钟）
        return min(delay, 300.0)

    def _record_error(self, level: ErrorLevel):
        """记录错误统计"""
        self._error_counts[level] += 1
        self._last_error_time[level] = time.time()

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        total_errors = sum(self._error_counts.values())

        return {
            "total_errors": total_errors,
            "critical_errors": self._error_counts[ErrorLevel.CRITICAL],
            "high_errors": self._error_counts[ErrorLevel.HIGH],
            "medium_errors": self._error_counts[ErrorLevel.MEDIUM],
            "low_errors": self._error_counts[ErrorLevel.LOW],
            "last_error_times": self._last_error_time
        }

    def reset_stats(self):
        """重置错误统计"""
        for level in ErrorLevel:
            self._error_counts[level] = 0
        self._last_error_time.clear()


class GracefulDegradation:
    """
    优雅降级策略 - 根据错误情况自动降低功能级别
    """

    class DegradationMode(IntEnum):
        """降级模式枚举"""
        FULL = 0           # 全功能模式
        PUBLISH_ONLY = 1   # 仅发布，不接收状态
        LOG_ONLY = 2       # 仅记录到数据库，不发布ROS2
        DISABLED = 3       # 完全禁用

    # 为测试兼容性提供字典
    DEGRADATION_MODES = {
        "FULL": DegradationMode.FULL,
        "PUBLISH_ONLY": DegradationMode.PUBLISH_ONLY,
        "LOG_ONLY": DegradationMode.LOG_ONLY,
        "DISABLED": DegradationMode.DISABLED
    }

    def __init__(self):
        self._current_mode = self.DegradationMode.FULL
        self._failure_count = 0
        self._last_failure_time = None
        self._config = Config()

        # 降级阈值配置
        self._thresholds = {
            self.DegradationMode.FULL: 5,          # 5次失败后降级
            self.DegradationMode.PUBLISH_ONLY: 10, # 10次失败后降级
            self.DegradationMode.LOG_ONLY: 15      # 15次失败后降级
        }

        # 冷却时间（秒）
        self._cooldown_periods = {
            self.DegradationMode.PUBLISH_ONLY: 60,    # 1分钟
            self.DegradationMode.LOG_ONLY: 300,       # 5分钟
            self.DegradationMode.DISABLED: 1800       # 30分钟
        }

    def check_and_degrade(self):
        """检查错误情况并决定是否降级"""
        current_time = time.time()

        # 检查是否需要降级
        if self._failure_count >= self._thresholds.get(self._current_mode, float('inf')):
            next_mode_value = self._current_mode.value + 1

            if next_mode_value <= self.DegradationMode.DISABLED.value:
                # 检查冷却期
                if self._last_failure_time is None or \
                   (current_time - self._last_failure_time) > self._get_cooldown_period(self._current_mode):

                    self._current_mode = self.DegradationMode(next_mode_value)
                    self._failure_count = 0
                    self._last_failure_time = current_time

                    logging.warning(f"Degraded to {self._current_mode.name} mode")

    def record_failure(self):
        """记录一次失败"""
        self._failure_count += 1
        self._last_failure_time = time.time()

        # 检查是否需要降级
        self.check_and_degrade()

    def record_success(self):
        """记录一次成功，可能恢复模式"""
        if self._failure_count > 0:
            self._failure_count = max(0, self._failure_count - 1)

        # 连续成功可能恢复更高模式
        if self._failure_count == 0 and self._current_mode.value > self.DegradationMode.FULL.value:
            # 检查是否过了冷却期
            current_time = time.time()
            if self._last_failure_time is None or \
               (current_time - self._last_failure_time) > self._get_cooldown_period(self._current_mode):

                # 尝试恢复上一级模式
                prev_mode_value = self._current_mode.value - 1
                if prev_mode_value >= self.DegradationMode.FULL.value:
                    self._current_mode = self.DegradationMode(prev_mode_value)
                    logging.info(f"Recovered to {self._current_mode.name} mode")

    def _get_cooldown_period(self, mode: DegradationMode) -> int:
        """获取指定模式的冷却时间"""
        return self._cooldown_periods.get(mode, 60)

    def get_current_mode(self) -> DegradationMode:
        """获取当前降级模式"""
        return self._current_mode

    def get_mode_name(self) -> str:
        """获取当前模式名称"""
        return self._current_mode.name

    def is_fully_functional(self) -> bool:
        """检查是否全功能模式"""
        return self._current_mode == self.DegradationMode.FULL

    def can_publish(self) -> bool:
        """检查是否可以发布消息"""
        return self._current_mode.value <= self.DegradationMode.PUBLISH_ONLY.value

    def can_receive(self) -> bool:
        """检查是否可以接收消息"""
        return self._current_mode == self.DegradationMode.FULL

    def reset(self):
        """重置到全功能模式"""
        self._current_mode = self.DegradationMode.FULL
        self._failure_count = 0
        self._last_failure_time = None
        logging.info("Degradation reset to FULL mode")
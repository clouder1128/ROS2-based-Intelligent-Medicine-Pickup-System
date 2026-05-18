# agent_with_backend/P1/thought_logging/config.py
import os
import logging
from typing import List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ThoughtLoggingConfig:
    """思考记录配置类"""

    enabled: bool = False
    log_level: str = "DETAILED"
    log_to_file: bool = True
    log_to_console: bool = False
    log_dir: str = "./logs/thoughts"
    log_formats: List[str] = field(default_factory=lambda: ["json", "text"])
    session_auto_cleanup: bool = True
    session_retention_days: int = 7

    # 支持的日志级别
    _SUPPORTED_LEVELS = ["BASIC", "STANDARD", "DETAILED", "DEBUG"]

    def __post_init__(self):
        """从环境变量加载配置"""
        self._load_from_env()
        self.validate()

    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            "ENABLE_THOUGHT_LOGGING": ("enabled", lambda x: x.lower() == "true"),
            "THOUGHT_LOG_LEVEL": ("log_level", str),
            "THOUGHT_LOG_TO_FILE": ("log_to_file", lambda x: x.lower() == "true"),
            "THOUGHT_LOG_TO_CONSOLE": ("log_to_console", lambda x: x.lower() == "true"),
            "THOUGHT_LOG_DIR": ("log_dir", str),
            "THOUGHT_LOG_FORMATS": ("log_formats", lambda x: [f.strip() for f in x.split(",")]),
            "THOUGHT_SESSION_AUTO_CLEANUP": ("session_auto_cleanup", lambda x: x.lower() == "true"),
            "THOUGHT_SESSION_RETENTION_DAYS": ("session_retention_days", int),
        }

        for env_var, (attr_name, converter) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    setattr(self, attr_name, converter(value))
                except (ValueError, TypeError) as e:
                    logger.warning(f"无法解析环境变量 {env_var}={value}: {e}")

    def validate(self):
        """验证配置有效性"""
        if self.log_level not in self._SUPPORTED_LEVELS:
            raise ValueError(
                f"无效的日志级别: {self.log_level}, 必须是 {self._SUPPORTED_LEVELS}"
            )

        if not isinstance(self.log_formats, list):
            raise ValueError("log_formats必须是列表")

        supported_formats = ["json", "text"]
        for fmt in self.log_formats:
            if fmt not in supported_formats:
                raise ValueError(
                    f"不支持的日志格式: {fmt}, 必须是 {supported_formats}"
                )

        # 确保日志目录存在
        if self.log_to_file:
            os.makedirs(self.log_dir, exist_ok=True)

    def to_dict(self):
        """转换为字典（不包含敏感信息）"""
        return {
            "enabled": self.enabled,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_to_console": self.log_to_console,
            "log_dir": self.log_dir,
            "log_formats": self.log_formats,
            "session_auto_cleanup": self.session_auto_cleanup,
            "session_retention_days": self.session_retention_days,
        }
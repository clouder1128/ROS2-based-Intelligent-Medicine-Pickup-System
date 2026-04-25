import os
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def _get_port() -> int:
    port_str = os.getenv("PORT", "8001")
    try:
        port = int(port_str)
    except ValueError:
        print(f"[Config] Warning: Invalid PORT value '{port_str}', using default 8001")
        port = 8001
    if port < 1 or port > 65535:
        print(f"[Config] Warning: Port {port} out of range (1-65535), using 8001")
        port = 8001
    return port


class Config:
    """全局配置"""

    # === 服务器配置 ===
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = _get_port()
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # === 数据库配置 ===
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH", str(Path(__file__).parent.parent / "pharmacy.db")
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./medical_assistant.db")

    # === LLM 配置 ===
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv(
        "ANTHROPIC_AUTH_TOKEN"
    )
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-sonnet-20240229")
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
    ANTHROPIC_SMALL_FAST_MODEL = os.getenv("ANTHROPIC_SMALL_FAST_MODEL")
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "false").lower() == "true"

    # === Agent 配置 ===
    MAX_HISTORY_LEN = int(os.getenv("MAX_HISTORY_LEN", "20"))
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "15"))
    SESSION_STATE_DIR = os.getenv("SESSION_STATE_DIR", "./sessions")
    PHARMACY_BASE_URL = os.getenv("PHARMACY_BASE_URL", "http://localhost:8001")

    # === 并发/异步配置 ===
    ENABLE_ASYNC = os.getenv("ENABLE_ASYNC", "false").lower() == "true"
    MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "100"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    REQUEST_BATCHING = os.getenv("REQUEST_BATCHING", "false").lower() == "true"
    LLM_REQUEST_CACHE_SIZE = int(os.getenv("LLM_REQUEST_CACHE_SIZE", "50"))

    # === ROS2 配置 ===
    ENABLE_ROS2: bool = os.getenv("ENABLE_ROS2", "true").lower() in ["true", "1"]

    # === 工作流规划器配置 ===
    ENABLE_WORKFLOW_PLANNER: bool = os.getenv("ENABLE_WORKFLOW_PLANNER", "true").lower() in ["true", "1"]

    # === 症状提取配置 ===
    ENABLE_LLM_SYMPTOM_EXTRACTION = os.getenv(
        "ENABLE_LLM_SYMPTOM_EXTRACTION", "true"
    ).lower() == "true"
    NEGATION_WORDS = ["无", "没有", "不", "否", "非", "未"]

    # === 日志配置 ===
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # === 思考记录配置 ===
    ENABLE_THOUGHT_LOGGING = os.getenv("ENABLE_THOUGHT_LOGGING", "false").lower() == "true"
    THOUGHT_LOG_LEVEL = os.getenv("THOUGHT_LOG_LEVEL", "DETAILED")
    THOUGHT_LOG_TO_FILE = os.getenv("THOUGHT_LOG_TO_FILE", "true").lower() == "true"
    THOUGHT_LOG_TO_CONSOLE = os.getenv("THOUGHT_LOG_TO_CONSOLE", "false").lower() == "true"
    THOUGHT_LOG_DIR = os.getenv("THOUGHT_LOG_DIR", "./logs/thoughts")
    THOUGHT_LOG_FORMATS = os.getenv("THOUGHT_LOG_FORMATS", "json,text").split(",")
    THOUGHT_SESSION_AUTO_CLEANUP = os.getenv("THOUGHT_SESSION_AUTO_CLEANUP", "true").lower() == "true"
    THOUGHT_SESSION_RETENTION_DAYS = int(os.getenv("THOUGHT_SESSION_RETENTION_DAYS", "7"))

    @classmethod
    def validate(cls) -> None:
        """验证配置项的有效性"""
        from common.exceptions import ConfigurationError

        if cls.LLM_PROVIDER not in ["claude", "openai", "deepseek"]:
            raise ConfigurationError(
                f"Invalid LLM provider: {cls.LLM_PROVIDER}, must be 'claude' or 'openai'"
            )
        if cls.LLM_PROVIDER == "claude" and not cls.ANTHROPIC_API_KEY:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN required for Claude provider"
            )
        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ConfigurationError("OPENAI_API_KEY required for OpenAI provider")
        if not (1 <= cls.MAX_ITERATIONS <= 50):
            raise ConfigurationError(f"MAX_ITERATIONS must be 1-50, got {cls.MAX_ITERATIONS}")
        if not (0.0 <= cls.LLM_TEMPERATURE <= 2.0):
            raise ConfigurationError(
                f"LLM_TEMPERATURE must be 0-2, got {cls.LLM_TEMPERATURE}"
            )
        if cls.MAX_CONCURRENT_SESSIONS <= 0:
            raise ConfigurationError(
                f"MAX_CONCURRENT_SESSIONS must be > 0, got {cls.MAX_CONCURRENT_SESSIONS}"
            )
        if cls.REQUEST_TIMEOUT <= 0:
            raise ConfigurationError(f"REQUEST_TIMEOUT must be > 0, got {cls.REQUEST_TIMEOUT}")
        if cls.LLM_REQUEST_CACHE_SIZE <= 0:
            raise ConfigurationError(
                f"LLM_REQUEST_CACHE_SIZE must be > 0, got {cls.LLM_REQUEST_CACHE_SIZE}"
            )
        if cls.SESSION_STATE_DIR:
            try:
                os.makedirs(cls.SESSION_STATE_DIR, exist_ok=True)
            except Exception as e:
                raise ConfigurationError(
                    f"Cannot create session dir {cls.SESSION_STATE_DIR}: {str(e)}"
                )
        if cls.THOUGHT_LOG_LEVEL not in ["BASIC", "STANDARD", "DETAILED", "DEBUG"]:
            raise ConfigurationError(
                f"Invalid THOUGHT_LOG_LEVEL: {cls.THOUGHT_LOG_LEVEL}"
            )
        if not all(fmt in ["json", "text"] for fmt in cls.THOUGHT_LOG_FORMATS):
            raise ConfigurationError(
                f"Invalid THOUGHT_LOG_FORMATS: {cls.THOUGHT_LOG_FORMATS}"
            )
        if cls.THOUGHT_SESSION_RETENTION_DAYS <= 0:
            raise ConfigurationError(
                f"THOUGHT_SESSION_RETENTION_DAYS must be > 0, got {cls.THOUGHT_SESSION_RETENTION_DAYS}"
            )
        logging.debug("Config validation passed")

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "database_path": cls.DATABASE_PATH,
            "log_level": cls.LOG_LEVEL,
            "enable_ros2": cls.ENABLE_ROS2,
            "cors_origins": cls.CORS_ORIGINS,
            "LLM_PROVIDER": cls.LLM_PROVIDER,
            "LLM_MODEL": cls.LLM_MODEL,
            "LLM_MAX_TOKENS": cls.LLM_MAX_TOKENS,
            "LLM_TEMPERATURE": cls.LLM_TEMPERATURE,
            "PHARMACY_BASE_URL": cls.PHARMACY_BASE_URL,
            "MAX_ITERATIONS": cls.MAX_ITERATIONS,
            "ENABLE_THOUGHT_LOGGING": cls.ENABLE_THOUGHT_LOGGING,
        }


try:
    Config.validate()
except Exception as e:
    from common.exceptions import ConfigurationError
    if isinstance(e, ConfigurationError):
        logging.error(f"Config validation failed: {str(e)}")
        raise
    else:
        raise

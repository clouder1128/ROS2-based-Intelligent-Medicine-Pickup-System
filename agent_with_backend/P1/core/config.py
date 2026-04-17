# config.py
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class Config:
    """全局配置，从环境变量读取"""

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv(
        "ANTHROPIC_AUTH_TOKEN"
    )  # 支持DeepSeek的ANTHROPIC_AUTH_TOKEN
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("ANTHROPIC_MODEL") or os.getenv(
        "LLM_MODEL", "claude-3-sonnet-20240229"
    )  # ANTHROPIC_MODEL优先
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL")  # 支持自定义base_url
    ANTHROPIC_SMALL_FAST_MODEL = os.getenv(
        "ANTHROPIC_SMALL_FAST_MODEL"
    )  # 快速模型（可选）
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    PHARMACY_BASE_URL = os.getenv("PHARMACY_BASE_URL", "http://localhost:8001")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medical_assistant.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    MAX_HISTORY_LEN = int(os.getenv("MAX_HISTORY_LEN", "20"))
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "15"))
    SESSION_STATE_DIR = os.getenv("SESSION_STATE_DIR", "./sessions")

    # 新增配置项
    ENABLE_ASYNC = os.getenv("ENABLE_ASYNC", "false").lower() == "true"
    MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "100"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    REQUEST_BATCHING = os.getenv("REQUEST_BATCHING", "false").lower() == "true"
    LLM_REQUEST_CACHE_SIZE = int(os.getenv("LLM_REQUEST_CACHE_SIZE", "50"))
    ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "false").lower() == "true"

    # 症状提取模式开关
    ENABLE_LLM_SYMPTOM_EXTRACTION = os.getenv(
        "ENABLE_LLM_SYMPTOM_EXTRACTION", "true"
    ).lower() == "true"

    # 否定词列表（用于规则提取器改进）
    NEGATION_WORDS = ["无", "没有", "不", "否", "非", "未"]

    # 思考记录配置
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
        """验证配置项的有效性

        Raises:
            ConfigurationError: 当配置无效时抛出
        """
        from .exceptions import ConfigurationError

        # 验证LLM提供商和API密钥
        if cls.LLM_PROVIDER not in ["claude", "openai"]:
            raise ConfigurationError(
                f"无效的LLM提供商: {cls.LLM_PROVIDER}，必须是 'claude' 或 'openai'"
            )

        if cls.LLM_PROVIDER == "claude" and not cls.ANTHROPIC_API_KEY:
            raise ConfigurationError(
                "使用Claude提供商时需要设置ANTHROPIC_API_KEY或ANTHROPIC_AUTH_TOKEN环境变量"
            )

        if cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            raise ConfigurationError("使用OpenAI提供商时需要设置OPENAI_API_KEY环境变量")

        # 验证MAX_ITERATIONS范围
        if not (1 <= cls.MAX_ITERATIONS <= 50):
            raise ConfigurationError(
                f"MAX_ITERATIONS必须在1-50之间，当前值: {cls.MAX_ITERATIONS}"
            )

        # 验证LLM_TEMPERATURE范围
        if not (0.0 <= cls.LLM_TEMPERATURE <= 2.0):
            raise ConfigurationError(
                f"LLM_TEMPERATURE必须在0-2之间，当前值: {cls.LLM_TEMPERATURE}"
            )

        # 验证MAX_CONCURRENT_SESSIONS范围
        if cls.MAX_CONCURRENT_SESSIONS <= 0:
            raise ConfigurationError(
                f"MAX_CONCURRENT_SESSIONS必须大于0，当前值: {cls.MAX_CONCURRENT_SESSIONS}"
            )

        # 验证REQUEST_TIMEOUT范围
        if cls.REQUEST_TIMEOUT <= 0:
            raise ConfigurationError(
                f"REQUEST_TIMEOUT必须大于0，当前值: {cls.REQUEST_TIMEOUT}"
            )

        # 验证LLM_REQUEST_CACHE_SIZE范围
        if cls.LLM_REQUEST_CACHE_SIZE <= 0:
            raise ConfigurationError(
                f"LLM_REQUEST_CACHE_SIZE必须大于0，当前值: {cls.LLM_REQUEST_CACHE_SIZE}"
            )

        # 验证SESSION_STATE_DIR目录
        if cls.SESSION_STATE_DIR:
            try:
                os.makedirs(cls.SESSION_STATE_DIR, exist_ok=True)
            except Exception as e:
                raise ConfigurationError(
                    f"无法创建会话目录 {cls.SESSION_STATE_DIR}: {str(e)}"
                )

        # 验证思考记录配置
        if cls.THOUGHT_LOG_LEVEL not in ["BASIC", "STANDARD", "DETAILED", "DEBUG"]:
            raise ConfigurationError(
                f"无效的THOUGHT_LOG_LEVEL: {cls.THOUGHT_LOG_LEVEL}, 必须是 BASIC, STANDARD, DETAILED 或 DEBUG"
            )

        if not all(fmt in ["json", "text"] for fmt in cls.THOUGHT_LOG_FORMATS):
            raise ConfigurationError(
                f"无效的THOUGHT_LOG_FORMATS: {cls.THOUGHT_LOG_FORMATS}, 只能包含 json 和 text"
            )

        if cls.THOUGHT_SESSION_RETENTION_DAYS <= 0:
            raise ConfigurationError(
                f"THOUGHT_SESSION_RETENTION_DAYS必须大于0，当前值: {cls.THOUGHT_SESSION_RETENTION_DAYS}"
            )

        logging.debug("配置验证通过")

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典（不包含敏感信息）

        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "LLM_PROVIDER": cls.LLM_PROVIDER,
            "LLM_MODEL": cls.LLM_MODEL,
            "LLM_MAX_TOKENS": cls.LLM_MAX_TOKENS,
            "LLM_TEMPERATURE": cls.LLM_TEMPERATURE,
            "PHARMACY_BASE_URL": cls.PHARMACY_BASE_URL,
            "DATABASE_URL": (
                cls.DATABASE_URL[:20] + "..."
                if cls.DATABASE_URL and len(cls.DATABASE_URL) > 20
                else cls.DATABASE_URL
            ),
            "LOG_LEVEL": cls.LOG_LEVEL,
            "MAX_HISTORY_LEN": cls.MAX_HISTORY_LEN,
            "MAX_ITERATIONS": cls.MAX_ITERATIONS,
            "SESSION_STATE_DIR": cls.SESSION_STATE_DIR,
            "ENABLE_ASYNC": cls.ENABLE_ASYNC,
            "MAX_CONCURRENT_SESSIONS": cls.MAX_CONCURRENT_SESSIONS,
            "REQUEST_TIMEOUT": cls.REQUEST_TIMEOUT,
            "ENABLE_THOUGHT_LOGGING": cls.ENABLE_THOUGHT_LOGGING,
            "THOUGHT_LOG_LEVEL": cls.THOUGHT_LOG_LEVEL,
            "THOUGHT_LOG_TO_FILE": cls.THOUGHT_LOG_TO_FILE,
            "THOUGHT_LOG_TO_CONSOLE": cls.THOUGHT_LOG_TO_CONSOLE,
            "THOUGHT_LOG_DIR": cls.THOUGHT_LOG_DIR,
            "THOUGHT_LOG_FORMATS": cls.THOUGHT_LOG_FORMATS,
            "THOUGHT_SESSION_AUTO_CLEANUP": cls.THOUGHT_SESSION_AUTO_CLEANUP,
            "THOUGHT_SESSION_RETENTION_DAYS": cls.THOUGHT_SESSION_RETENTION_DAYS,
        }


# 启动时验证配置
try:
    Config.validate()
except Exception as e:
    from .exceptions import ConfigurationError

    if isinstance(e, ConfigurationError):
        logging.error(f"配置验证失败: {str(e)}")
        raise
    else:
        # 其他类型的异常直接抛出
        raise

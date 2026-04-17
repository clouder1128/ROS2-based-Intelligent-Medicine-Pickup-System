"""
思考记录模块

为医疗助手Agent添加LLM思考过程记录功能，支持详细级别的思考过程记录、
双格式日志输出和可选调试模式。
"""

from .config import ThoughtLoggingConfig
from .recorder import ThoughtRecorder
from .output import OutputManager, JSONFileWriter, TextFileWriter, TerminalLogger
from .decorators import (
    with_thought_logging,
    ThoughtLoggingDecorator,
    record_llm_calls,
    record_tool_decisions
)
from .utils import (
    generate_session_id,
    format_timestamp,
    safe_json_dumps,
    ensure_directory,
    get_current_time_ms,
    sanitize_for_logging
)

__version__ = "1.0.0"
__all__ = [
    # 配置
    "ThoughtLoggingConfig",

    # 核心类
    "ThoughtRecorder",
    "OutputManager",
    "JSONFileWriter",
    "TextFileWriter",
    "TerminalLogger",

    # 装饰器
    "with_thought_logging",
    "ThoughtLoggingDecorator",
    "record_llm_calls",
    "record_tool_decisions",

    # 工具函数
    "generate_session_id",
    "format_timestamp",
    "safe_json_dumps",
    "ensure_directory",
    "get_current_time_ms",
    "sanitize_for_logging",
]
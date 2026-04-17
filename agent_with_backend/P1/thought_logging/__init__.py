# agent_with_backend/P1/thought_logging/__init__.py
"""Thought logging utilities for agent system."""

from .config import ThoughtLoggingConfig
from .recorder import ThoughtRecorder
from .output import OutputManager
from .decorators import (
    record_llm_calls,
    record_tool_decisions,
    ThoughtLoggingDecorator,
    with_thought_logging
)
from .utils import (
    generate_session_id,
    format_timestamp,
    safe_json_dumps,
    ensure_directory,
    get_current_time_ms,
    sanitize_for_logging
)

__all__ = [
    'ThoughtLoggingConfig',
    'ThoughtRecorder',
    'OutputManager',
    'record_llm_calls',
    'record_tool_decisions',
    'ThoughtLoggingDecorator',
    'with_thought_logging',
    'generate_session_id',
    'format_timestamp',
    'safe_json_dumps',
    'ensure_directory',
    'get_current_time_ms',
    'sanitize_for_logging'
]

__version__ = "0.1.0"
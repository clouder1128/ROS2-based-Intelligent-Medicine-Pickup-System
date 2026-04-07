# 工具函数模块
# 这些函数在各个子模块中定义

# 导入json_tools模块中的函数
try:
    from .json_tools import extract_json_from_text, safe_parse_json, format_tool_result
except ImportError:
    extract_json_from_text = None
    safe_parse_json = None
    format_tool_result = None

# 导入text_utils模块中的函数
try:
    from .text_utils import (
        truncate_text, estimate_tokens, log_duration,
        generate_id, hash_string, now_iso, safe_get, merge_dicts,
        validate_patient_input, extract_mentions_of_allergy,
        summarize_conversation, estimate_cost
    )
except ImportError:
    truncate_text = None
    estimate_tokens = None
    log_duration = None
    generate_id = None
    hash_string = None
    now_iso = None
    safe_get = None
    merge_dicts = None
    validate_patient_input = None
    extract_mentions_of_allergy = None
    summarize_conversation = None
    estimate_cost = None

# 导入retry模块中的函数
try:
    from .retry import retry_on_exception
except ImportError:
    retry_on_exception = None

# 导入validation模块中的函数
try:
    from .validation import create_error_response, create_success_response
except ImportError:
    create_error_response = None
    create_success_response = None

__all__ = [
    # json_tools
    'extract_json_from_text', 'safe_parse_json', 'format_tool_result',

    # text_utils
    'truncate_text', 'estimate_tokens', 'log_duration',
    'generate_id', 'hash_string', 'now_iso', 'safe_get', 'merge_dicts',
    'validate_patient_input', 'extract_mentions_of_allergy',
    'summarize_conversation', 'estimate_cost',

    # retry
    'retry_on_exception',

    # validation
    'create_error_response', 'create_success_response'
]
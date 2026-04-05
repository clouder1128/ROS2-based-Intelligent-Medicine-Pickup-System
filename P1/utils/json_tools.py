# json_tools.py
"""JSON处理工具函数"""

import json
import re
from typing import Any, Dict, Optional


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """从LLM回复中提取JSON对象"""
    patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{.*\})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    return None


def safe_parse_json(content: str) -> Optional[Dict[str, Any]]:
    """安全解析JSON，失败返回None"""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def format_tool_result(result: Any) -> str:
    """将工具返回结果统一转换为字符串"""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False)
    return str(result)


__all__ = ['extract_json_from_text', 'safe_parse_json', 'format_tool_result']
# text_utils.py
"""文本处理工具函数"""

import time
import logging
import hashlib
import re
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager
from datetime import datetime


def truncate_text(text: str, max_len: int = 500) -> str:
    """截断过长的文本"""
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."


def estimate_tokens(text: str) -> int:
    """粗略估算token数（按字符数/4）"""
    return len(text) // 4


@contextmanager
def log_duration(logger_obj: logging.Logger, operation: str):
    """记录操作耗时的上下文管理器"""
    start = time.time()
    yield
    elapsed = time.time() - start
    logger_obj.info(f"{operation} took {elapsed:.2f}s")


def generate_id(prefix: str) -> str:
    """生成唯一ID，格式：前缀-YYYYMMDD-HHMMSS"""
    now = datetime.now()
    date_part = now.strftime("%Y%m%d")
    time_part = now.strftime("%H%M%S")
    return f"{prefix}-{date_part}-{time_part}"


def hash_string(s: str) -> str:
    """返回字符串的短哈希（前8位MD5）"""
    return hashlib.md5(s.encode()).hexdigest()[:8]


def now_iso() -> str:
    """返回ISO格式当前时间"""
    return datetime.now().isoformat()


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """通过点分隔路径安全获取嵌套字典值"""
    keys = path.split('.')
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def merge_dicts(base: Dict, updates: Dict) -> Dict:
    """递归合并两个字典"""
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def validate_patient_input(text: str) -> Dict[str, Any]:
    """
    验证患者输入，返回结构化信息。
    不涉及医疗判断，仅做格式清洗。
    """
    if not text or not isinstance(text, str):
        return {"valid": False, "error": "输入不能为空"}

    cleaned = text.strip()
    if len(cleaned) < 2:
        return {"valid": False, "error": "输入太短"}

    # 简单的敏感词过滤（占位，实际可扩展）
    sensitive_words = ["自杀", "毒品"]
    for word in sensitive_words:
        if word in cleaned:
            return {"valid": False, "error": f"输入包含敏感词: {word}"}

    return {"valid": True, "cleaned": cleaned}


def extract_mentions_of_allergy(text: str) -> List[str]:
    """从文本中提取可能提及的过敏物质（简单关键词匹配）"""
    allergy_keywords = ["青霉素", "头孢", "磺胺", "阿司匹林", "青霉素类", "头孢类"]
    found = []
    for kw in allergy_keywords:
        if kw in text:
            found.append(kw)
    return found


def summarize_conversation(messages: List[Dict], max_summary_tokens: int = 200) -> str:
    """
    生成对话摘要（用于压缩时保留关键信息）。
    实际应用中可调用LLM，这里用简单规则。
    """
    user_messages = [m.get("content", "") for m in messages if m.get("role") == "user"]
    if not user_messages:
        return "无对话记录"

    summary = "患者诉求: " + "; ".join([truncate_text(um, 50) for um in user_messages[-3:]])
    return truncate_text(summary, max_summary_tokens)


def estimate_cost(tokens: int, model: str = "claude-3-sonnet") -> float:
    """粗略估算API费用（每1K tokens价格）"""
    pricing = {
        "claude-3-sonnet": 0.003,
        "claude-3-opus": 0.015,
        "gpt-4": 0.03,
        "gpt-3.5-turbo": 0.001
    }
    price_per_1k = pricing.get(model, 0.003)
    return (tokens / 1000) * price_per_1k


__all__ = [
    'truncate_text', 'estimate_tokens', 'log_duration',
    'generate_id', 'hash_string', 'now_iso', 'safe_get', 'merge_dicts',
    'validate_patient_input', 'extract_mentions_of_allergy',
    'summarize_conversation', 'estimate_cost'
]
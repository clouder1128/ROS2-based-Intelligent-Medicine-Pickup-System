# compressor.py
"""消息压缩模块，用于压缩对话历史以节省token"""

from typing import List, Dict
from utils.text_utils import estimate_tokens


def compress_messages_by_tokens(
    messages: List[Dict], max_tokens: int = 3000, preserve_system: bool = True
) -> List[Dict]:
    """
    基于token限制压缩消息历史。
    返回压缩后的消息列表。
    """
    if not messages:
        return messages

    # 分离系统消息
    system_msgs = []
    non_system = []
    for m in messages:
        if preserve_system and m.get("role") == "system":
            system_msgs.append(m)
        else:
            non_system.append(m)

    total_tokens = sum(estimate_tokens(m.get("content", "")) for m in messages)
    if total_tokens <= max_tokens:
        return messages

    # 从头部删除非系统消息直到满足限制
    while non_system and total_tokens > max_tokens:
        removed = non_system.pop(0)
        total_tokens -= estimate_tokens(removed.get("content", ""))

    return system_msgs + non_system


def compress_messages_by_count(
    messages: List[Dict], max_messages: int = 20, preserve_system: bool = True
) -> List[Dict]:
    """基于消息数量压缩历史"""
    if len(messages) <= max_messages:
        return messages

    if preserve_system:
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]
        keep = non_system[-max_messages + len(system_msgs) :]
        return system_msgs + keep
    else:
        return messages[-max_messages:]


def smart_compress(
    messages: List[Dict], max_tokens: int = 3000, max_messages: int = 20
) -> List[Dict]:
    """智能压缩：优先按token限制，其次按数量"""
    compressed = compress_messages_by_tokens(messages, max_tokens)
    compressed = compress_messages_by_count(compressed, max_messages)
    return compressed


__all__ = [
    "compress_messages_by_tokens",
    "compress_messages_by_count",
    "smart_compress",
]

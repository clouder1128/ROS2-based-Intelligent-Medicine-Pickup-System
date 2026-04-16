# manager.py
"""消息管理器，管理对话历史，支持自动压缩和截断"""

from typing import List, Dict, Optional
from ..core.config import Config
from ..utils.text_utils import estimate_tokens
from .compressor import smart_compress


class MessageManager:
    """管理对话历史，支持自动压缩和截断，基于token估算"""

    def __init__(
        self, system_prompt: Optional[str] = None, max_history: Optional[int] = None
    ) -> None:
        self.system_prompt = system_prompt
        self.max_history = max_history or Config.MAX_HISTORY_LEN
        self.max_tokens_limit = 3000  # 软限制，超过时压缩
        self.messages: List[Dict] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_message(self, role: str, content: str) -> None:
        """添加消息（role: user, assistant, tool）"""
        self.messages.append({"role": role, "content": content})
        self._compress_if_needed()

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        """添加工具调用结果（Claude格式需要）"""
        self.messages.append(
            {"role": "tool", "tool_call_id": tool_call_id, "content": content}
        )
        self._compress_if_needed()

    def get_messages(self) -> List[Dict]:
        """获取当前消息列表（不包含系统提示词）"""
        if self.messages and self.messages[0].get("role") == "system":
            return self.messages[1:]
        return self.messages

    def get_full_messages(self) -> List[Dict]:
        """获取包含系统提示词的全部消息"""
        return self.messages

    def reset(self, keep_system: bool = True) -> None:
        """重置对话，可选择保留系统提示词"""
        if keep_system and self.system_prompt:
            self.messages = [{"role": "system", "content": self.system_prompt}]
        else:
            self.messages = []

    def get_last_user_message(self) -> Optional[str]:
        """获取最后一条用户消息"""
        for m in reversed(self.messages):
            if m.get("role") == "user":
                return m.get("content", "")
        return None

    def get_conversation_length(self) -> int:
        """返回消息总数（含系统）"""
        return len(self.messages)

    def estimate_total_tokens(self) -> int:
        """估算当前对话总token数"""
        total = 0
        for m in self.messages:
            content = m.get("content", "")
            total += estimate_tokens(content)
        return total

    def _compress_if_needed(self) -> None:
        """当需要压缩时调用智能压缩"""
        # 首先按数量压缩
        if len(self.messages) > self.max_history + 1:
            system_msg = None
            if self.messages[0].get("role") == "system":
                system_msg = self.messages[0]
            keep = self.messages[-self.max_history :]
            if system_msg:
                keep.insert(0, system_msg)
            self.messages = keep

        # 然后按token压缩
        if self.estimate_total_tokens() > self.max_tokens_limit:
            self.messages = smart_compress(
                self.messages,
                max_tokens=self.max_tokens_limit,
                max_messages=self.max_history,
            )

    def _maybe_compress_by_count(self) -> None:
        """当消息数量超过阈值时，压缩早期消息（向后兼容）"""
        self._compress_if_needed()

    def _maybe_compress_by_tokens(self) -> None:
        """当估算token超过限制时，删除最早的非系统消息（向后兼容）"""
        self._compress_if_needed()


__all__ = ["MessageManager"]

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class LLMMessage:
    """LLM消息数据类"""
    role: str
    content: str
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"role": self.role, "content": self.content}
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            tool_call_id=data.get("tool_call_id"),
        )


@dataclass
class ToolCall:
    """工具调用数据类"""
    name: str
    input: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "input": self.input}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        return cls(name=data["name"], input=data["input"])


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: Optional[Dict[str, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.content is not None:
            result["content"] = self.content
        result["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.usage:
            result["usage"] = self.usage
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMResponse":
        tool_calls = []
        if "tool_calls" in data and data["tool_calls"]:
            tool_calls = [ToolCall.from_dict(tc) for tc in data["tool_calls"]]
        return cls(
            content=data.get("content"), tool_calls=tool_calls, usage=data.get("usage")
        )

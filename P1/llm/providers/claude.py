# claude.py
import logging
from typing import List, Dict, Any, Optional

from core.exceptions import LLMError
from llm.schemas import LLMMessage, ToolCall, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeProvider:
    """Claude API提供者"""

    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None):
        """初始化Claude客户端"""
        try:
            import anthropic

            # 支持自定义base_url以兼容DeepSeek等第三方API
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = anthropic.Anthropic(**kwargs)
        except ImportError:
            raise LLMError("Please install anthropic: pip install anthropic")
        self.model = model

    def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """发送对话请求到Claude API"""
        # 分离系统消息
        system = None
        claude_messages = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                claude_messages.append(msg.to_dict())

        # 转换工具格式
        claude_tools = None
        if tools:
            claude_tools = []
            for tool in tools:
                claude_tools.append(
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "input_schema": tool["input_schema"],
                    }
                )

        try:
            response = self.client.messages.create(
                model=self.model,
                system=system,
                messages=claude_messages,
                tools=claude_tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            raise LLMError(f"Claude API error: {str(e)}")

        # 解析响应
        content = None
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(name=block.name, input=block.input))

        # 构建使用量统计
        usage = None
        if hasattr(response, "usage"):
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens
                + response.usage.output_tokens,
            }

        return LLMResponse(content=content, tool_calls=tool_calls, usage=usage)

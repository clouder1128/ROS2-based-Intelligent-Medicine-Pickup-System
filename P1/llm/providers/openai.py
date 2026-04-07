# openai.py
import json
import logging
from typing import List, Dict, Any, Optional

from exceptions import LLMError
from llm.schemas import LLMMessage, ToolCall, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI API提供者"""

    def __init__(self, api_key: str, model: str):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise LLMError("Please install openai: pip install openai")
        self.model = model

    def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """发送对话请求到OpenAI API"""
        # 转换消息格式
        openai_messages = [msg.to_dict() for msg in messages]

        # 转换工具格式
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"]
                    }
                })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=openai_tools,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            raise LLMError(f"OpenAI API error: {str(e)}")

        # 解析响应
        message = response.choices[0].message
        content = message.content
        tool_calls = []

        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    name=tc.function.name,
                    input=json.loads(tc.function.arguments)
                ))

        # 构建使用量统计
        usage = None
        if hasattr(response, 'usage'):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage
        )
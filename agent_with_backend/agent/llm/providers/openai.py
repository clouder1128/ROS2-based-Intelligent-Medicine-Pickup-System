import json
import re
import logging
from typing import List, Dict, Any, Optional

from common.exceptions import LLMError
from agent.llm.schemas import LLMMessage, ToolCall, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """OpenAI API提供者"""

    def __init__(self, api_key: str, model: str):
        try:
            from openai import OpenAI
            from common.config import Config
            base_url = Config.OPENAI_BASE_URL
            self.client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        except ImportError:
            raise LLMError("Please install openai: pip install openai")
        self.model = model

    def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        openai_messages = [msg.to_dict() for msg in messages]

        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"],
                    },
                })

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=openai_tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            raise LLMError(f"OpenAI API error: {str(e)}")

        message = response.choices[0].message
        content = message.content
        tool_calls = []

        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        input=json.loads(tc.function.arguments),
                    )
                )

        # Fallback: detect tool calls in content for models that return raw SSE JSON
        if not tool_calls and content:
            tc_match = re.search(r'"tool_calls"\s*:\s*(\[[\s\S]*?\])\s*\}', content)
            if tc_match:
                try:
                    raw_tcs = json.loads(tc_match.group(1))
                    for raw in raw_tcs:
                        fn = raw.get("function", {})
                        tool_calls.append(
                            ToolCall(
                                id=raw.get("id"),
                                name=fn.get("name", ""),
                                input=json.loads(fn.get("arguments", "{}")),
                            )
                        )
                    content = re.sub(r'\s*\{"index".*', "", content).strip()
                except (json.JSONDecodeError, KeyError):
                    pass

        usage = None
        if hasattr(response, "usage"):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(content=content, tool_calls=tool_calls, usage=usage)

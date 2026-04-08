# client.py
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from core.config import Config
from core.exceptions import LLMError
from utils.retry import retry_on_exception
from .schemas import LLMMessage, ToolCall, LLMResponse
from .providers.claude import ClaudeProvider
from .providers.openai import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMClient:
    """统一的LLM客户端，支持Claude和OpenAI，带统计和重试"""

    _request_count = 0
    _total_tokens_estimate = 0

    def __init__(self, provider: str = None) -> None:
        self.provider = provider or Config.LLM_PROVIDER
        self._provider_instance = None

        if self.provider == "claude":
            self._provider_instance = ClaudeProvider(
                api_key=Config.ANTHROPIC_API_KEY,
                model=Config.LLM_MODEL,
                base_url=Config.ANTHROPIC_BASE_URL,
            )
        elif self.provider == "openai":
            self._provider_instance = OpenAIProvider(
                api_key=Config.OPENAI_API_KEY, model=Config.LLM_MODEL
            )
        else:
            raise LLMError(f"Unsupported provider: {self.provider}")

    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        """获取请求统计"""
        return {
            "requests": cls._request_count,
            "estimated_tokens": cls._total_tokens_estimate,
        }

    @classmethod
    def reset_stats(cls) -> None:
        """重置统计"""
        cls._request_count = 0
        cls._total_tokens_estimate = 0

    def _update_stats(self, messages: List[LLMMessage], response: LLMResponse) -> None:
        """更新统计信息"""
        LLMClient._request_count += 1

        # 估算输入tokens
        total_text = "".join(msg.content for msg in messages)
        input_tokens_estimate = len(total_text) // 4

        # 如果有使用量统计，使用实际值；否则估算
        if response.usage:
            output_tokens = (
                response.usage.get("output_tokens")
                or response.usage.get("completion_tokens")
                or 0
            )
            total_tokens = response.usage.get(
                "total_tokens", input_tokens_estimate + output_tokens
            )
        else:
            # 估算输出tokens
            output_text = response.content or ""
            output_tokens_estimate = len(output_text) // 4
            total_tokens = input_tokens_estimate + output_tokens_estimate

        LLMClient._total_tokens_estimate += total_tokens

    @retry_on_exception((LLMError, Exception), max_retries=3, delay=1.0)
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """向后兼容的chat接口，接受字典列表，返回字典格式"""
        # 转换消息格式
        llm_messages = [LLMMessage.from_dict(msg) for msg in messages]

        # 调用结构化接口
        response = self.chat_structured(
            messages=llm_messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 转换为字典格式返回
        return response.to_dict()

    def chat_structured(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """新的结构化chat接口，接受LLMMessage列表，返回LLMResponse"""
        temp = temperature or Config.LLM_TEMPERATURE
        max_tok = max_tokens or Config.LLM_MAX_TOKENS

        # 调用provider
        response = self._provider_instance.chat(
            messages=messages, tools=tools, temperature=temp, max_tokens=max_tok
        )

        # 更新统计
        self._update_stats(messages, response)

        return response

    async def chat_stream(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """流式响应生成器（仅OpenAI支持完整流式，Claude回退到普通）"""
        temp = temperature or Config.LLM_TEMPERATURE
        max_tok = max_tokens or Config.LLM_MAX_TOKENS

        if self.provider == "openai":
            # OpenAI流式响应
            openai_messages = messages.copy()
            stream = self._provider_instance.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=openai_messages,
                stream=True,
                temperature=temp,
                max_tokens=max_tok,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            # Claude不支持原生流式，回退到普通调用
            response = self.chat(messages, tools, None, temp, max_tok)
            content = response.get("content", "")
            if content:
                yield content

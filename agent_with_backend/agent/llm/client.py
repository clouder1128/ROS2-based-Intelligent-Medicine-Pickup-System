import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from common.config import Config
from common.exceptions import LLMError
from common.utils.retry import retry_on_exception
from agent.llm.schemas import LLMMessage, ToolCall, LLMResponse
from agent.llm.providers.claude import ClaudeProvider
from agent.llm.providers.openai import OpenAIProvider

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
        return {
            "requests": cls._request_count,
            "estimated_tokens": cls._total_tokens_estimate,
        }

    @classmethod
    def reset_stats(cls) -> None:
        cls._request_count = 0
        cls._total_tokens_estimate = 0

    def _update_stats(self, messages: List[LLMMessage], response: LLMResponse) -> None:
        LLMClient._request_count += 1
        total_text = "".join(msg.content for msg in messages)
        input_tokens_estimate = len(total_text) // 4
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
        llm_messages = [LLMMessage.from_dict(msg) for msg in messages]
        response = self.chat_structured(
            messages=llm_messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.to_dict()

    def chat_structured(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        temp = temperature or Config.LLM_TEMPERATURE
        max_tok = max_tokens or Config.LLM_MAX_TOKENS
        response = self._provider_instance.chat(
            messages=messages, tools=tools, temperature=temp, max_tokens=max_tok
        )
        self._update_stats(messages, response)
        return response

    async def chat_stream(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        temp = temperature or Config.LLM_TEMPERATURE
        max_tok = max_tokens or Config.LLM_MAX_TOKENS
        if self.provider == "openai":
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
            response = self.chat(messages, tools, None, temp, max_tok)
            content = response.get("content", "")
            if content:
                yield content

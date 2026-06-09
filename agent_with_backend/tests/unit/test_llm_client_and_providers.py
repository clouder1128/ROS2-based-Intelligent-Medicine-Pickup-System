"""测试大模型客户端统计、流式输出及 OpenAI 和 Claude 提供商适配逻辑。"""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent.llm.client import LLMClient
from agent.llm.providers.claude import ClaudeProvider
from agent.llm.providers.openai import OpenAIProvider
from agent.llm.schemas import LLMMessage, LLMResponse
from common.config import Config
from common.exceptions import LLMError


def test_llm_client_rejects_unknown_provider():
    with pytest.raises(LLMError, match="Unsupported provider"):
        LLMClient("unknown")


def test_llm_client_chat_updates_stats(monkeypatch):
    provider = MagicMock()
    provider.chat.return_value = LLMResponse(
        content="answer", usage={"total_tokens": 9}
    )
    monkeypatch.setattr("agent.llm.client.ClaudeProvider", lambda **kwargs: provider)
    monkeypatch.setattr(Config, "LLM_TEMPERATURE", 0.4)
    monkeypatch.setattr(Config, "LLM_MAX_TOKENS", 321)
    LLMClient.reset_stats()

    client = LLMClient("claude")
    result = client.chat([{"role": "user", "content": "question"}])

    assert result["content"] == "answer"
    assert LLMClient.get_stats() == {"requests": 1, "estimated_tokens": 9}
    provider.chat.assert_called_once()
    assert provider.chat.call_args.kwargs["temperature"] == 0.4
    assert provider.chat.call_args.kwargs["max_tokens"] == 321


def test_llm_client_estimates_tokens_without_usage():
    client = object.__new__(LLMClient)
    LLMClient.reset_stats()
    client._update_stats(
        [LLMMessage(role="user", content="12345678")],
        LLMResponse(content="12345678"),
    )
    assert LLMClient.get_stats() == {"requests": 1, "estimated_tokens": 4}


def test_openai_stream_yields_nonempty_chunks():
    client = object.__new__(LLMClient)
    client.provider = "openai"
    create = MagicMock(
        return_value=[
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="a"))]),
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]),
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="b"))]),
        ]
    )
    client._provider_instance = SimpleNamespace(
        client=SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
    )

    async def collect():
        return [
            chunk
            async for chunk in client.chat_stream([{"role": "user", "content": "q"}])
        ]

    chunks = asyncio.run(collect())
    assert chunks == ["a", "b"]
    assert create.call_args.kwargs["stream"] is True


def test_non_openai_stream_uses_regular_chat():
    client = object.__new__(LLMClient)
    client.provider = "claude"
    client.chat = MagicMock(return_value={"content": "complete"})

    async def collect():
        return [chunk async for chunk in client.chat_stream([])]

    chunks = asyncio.run(collect())
    assert chunks == ["complete"]


def _openai_response(content, tool_calls=None, usage=True):
    message = SimpleNamespace(content=content, tool_calls=tool_calls or [])
    response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
    if usage:
        response.usage = SimpleNamespace(
            prompt_tokens=2, completion_tokens=3, total_tokens=5
        )
    return response


def test_openai_provider_maps_tools_and_response():
    provider = object.__new__(OpenAIProvider)
    provider.model = "test-model"
    native_call = SimpleNamespace(
        id="call-1",
        function=SimpleNamespace(name="lookup", arguments='{"id": 7}'),
    )
    create = MagicMock(return_value=_openai_response("done", [native_call]))
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )

    response = provider.chat(
        [LLMMessage(role="user", content="find")],
        tools=[{"name": "lookup", "description": "Lookup", "input_schema": {"type": "object"}}],
    )

    assert response.tool_calls[0].input == {"id": 7}
    assert response.usage["total_tokens"] == 5
    assert create.call_args.kwargs["tools"][0]["function"]["name"] == "lookup"


def test_openai_provider_parses_embedded_tool_call_and_wraps_errors():
    provider = object.__new__(OpenAIProvider)
    provider.model = "test-model"
    embedded = (
        '{"tool_calls":[{"id":"x","function":{"name":"lookup",'
        '"arguments":"{\\"id\\":1}"}}]}'
    )
    create = MagicMock(return_value=_openai_response(embedded, usage=False))
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )
    response = provider.chat([LLMMessage(role="user", content="find")])
    assert response.tool_calls[0].name == "lookup"

    create.side_effect = RuntimeError("offline")
    with pytest.raises(LLMError, match="OpenAI API error"):
        provider.chat([])


def test_claude_provider_maps_messages_tools_and_usage():
    provider = object.__new__(ClaudeProvider)
    provider.model = "claude-test"
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="answer"),
            SimpleNamespace(type="tool_use", name="lookup", input={"id": 1}),
        ],
        usage=SimpleNamespace(input_tokens=4, output_tokens=6),
    )
    create = MagicMock(return_value=response)
    provider.client = SimpleNamespace(messages=SimpleNamespace(create=create))

    result = provider.chat(
        [
            LLMMessage(role="system", content="system prompt"),
            LLMMessage(role="user", content="question"),
        ],
        tools=[{"name": "lookup", "description": "Lookup", "input_schema": {}}],
    )

    assert result.content == "answer"
    assert result.tool_calls[0].input == {"id": 1}
    assert result.usage["total_tokens"] == 10
    assert create.call_args.kwargs["system"] == "system prompt"


def test_claude_provider_wraps_transport_errors():
    provider = object.__new__(ClaudeProvider)
    provider.model = "claude-test"
    provider.client = SimpleNamespace(
        messages=SimpleNamespace(create=MagicMock(side_effect=RuntimeError("offline")))
    )

    with pytest.raises(LLMError, match="Claude API error"):
        provider.chat([])

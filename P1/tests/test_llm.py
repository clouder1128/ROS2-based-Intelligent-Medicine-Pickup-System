# test_llm.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.schemas import LLMMessage, ToolCall, LLMResponse
from llm.client import LLMClient
from exceptions import LLMError


class TestLLMSchemas:
    """测试LLM Schema类"""

    def test_llm_message_to_dict(self):
        """测试LLMMessage的to_dict方法"""
        message = LLMMessage(role="user", content="Hello", tool_call_id="123")
        result = message.to_dict()
        assert result == {"role": "user", "content": "Hello", "tool_call_id": "123"}

    def test_llm_message_from_dict(self):
        """测试LLMMessage的from_dict方法"""
        data = {"role": "assistant", "content": "Hi there", "tool_call_id": "456"}
        message = LLMMessage.from_dict(data)
        assert message.role == "assistant"
        assert message.content == "Hi there"
        assert message.tool_call_id == "456"

    def test_tool_call_to_dict(self):
        """测试ToolCall的to_dict方法"""
        tool_call = ToolCall(name="search", input={"query": "test"})
        result = tool_call.to_dict()
        assert result == {"name": "search", "input": {"query": "test"}}

    def test_llm_response_to_dict(self):
        """测试LLMResponse的to_dict方法"""
        tool_calls = [ToolCall(name="search", input={"query": "test"})]
        response = LLMResponse(
            content="Hello",
            tool_calls=tool_calls,
            usage={"total_tokens": 100}
        )
        result = response.to_dict()
        assert result["content"] == "Hello"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "search"
        assert result["usage"]["total_tokens"] == 100


class TestLLMClient:
    """测试LLMClient类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        LLMClient.reset_stats()

    @patch.dict('os.environ', {
        'LLM_PROVIDER': 'claude',
        'ANTHROPIC_API_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-key'
    })
    def test_client_initialization_claude(self):
        """测试Claude客户端初始化"""
        client = LLMClient(provider="claude")
        assert client.provider == "claude"
        assert client._provider_instance is not None

    @patch.dict('os.environ', {
        'LLM_PROVIDER': 'openai',
        'ANTHROPIC_API_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-key'
    })
    def test_client_initialization_openai(self):
        """测试OpenAI客户端初始化"""
        client = LLMClient(provider="openai")
        assert client.provider == "openai"
        assert client._provider_instance is not None

    def test_client_initialization_invalid_provider(self):
        """测试无效provider的初始化"""
        with pytest.raises(LLMError, match="Unsupported provider"):
            LLMClient(provider="invalid")

    def test_get_stats(self):
        """测试获取统计信息"""
        stats = LLMClient.get_stats()
        assert "requests" in stats
        assert "estimated_tokens" in stats
        assert stats["requests"] == 0
        assert stats["estimated_tokens"] == 0

    def test_reset_stats(self):
        """测试重置统计信息"""
        # 先设置一些统计值
        LLMClient._request_count = 5
        LLMClient._total_tokens_estimate = 1000

        LLMClient.reset_stats()

        stats = LLMClient.get_stats()
        assert stats["requests"] == 0
        assert stats["estimated_tokens"] == 0

    @patch.dict('os.environ', {
        'LLM_PROVIDER': 'claude',
        'ANTHROPIC_API_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-key',
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.5',
        'LLM_MAX_TOKENS': '100'
    })
    def test_chat_backward_compatibility(self):
        """测试向后兼容的chat接口"""
        client = LLMClient()

        # Mock provider的chat方法
        mock_response = LLMResponse(
            content="Test response",
            tool_calls=[],
            usage={"total_tokens": 50}
        )
        client._provider_instance.chat = Mock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hello"}]
        result = client.chat(messages)

        assert isinstance(result, dict)
        assert result["content"] == "Test response"
        assert "tool_calls" in result
        assert "usage" in result

    @patch.dict('os.environ', {
        'LLM_PROVIDER': 'claude',
        'ANTHROPIC_API_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-key',
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.5',
        'LLM_MAX_TOKENS': '100'
    })
    def test_chat_structured(self):
        """测试结构化chat接口"""
        client = LLMClient()

        # Mock provider的chat方法
        mock_response = LLMResponse(
            content="Test response",
            tool_calls=[],
            usage={"total_tokens": 50}
        )
        client._provider_instance.chat = Mock(return_value=mock_response)

        messages = [LLMMessage(role="user", content="Hello")]
        result = client.chat_structured(messages)

        assert isinstance(result, LLMResponse)
        assert result.content == "Test response"
        assert result.usage["total_tokens"] == 50

    @patch.dict('os.environ', {
        'LLM_PROVIDER': 'openai',
        'ANTHROPIC_API_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-key',
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.5',
        'LLM_MAX_TOKENS': '100'
    })
    @pytest.mark.asyncio
    async def test_chat_stream_openai(self):
        """测试OpenAI流式响应"""
        client = LLMClient(provider="openai")

        # Mock OpenAI流式响应
        mock_chunk = Mock()
        mock_chunk.choices = [Mock()]
        mock_chunk.choices[0].delta = Mock()
        mock_chunk.choices[0].delta.content = "streaming "

        mock_stream = [mock_chunk, mock_chunk]
        client._provider_instance.client.chat.completions.create = Mock(return_value=mock_stream)

        messages = [{"role": "user", "content": "Hello"}]

        # 收集流式响应
        responses = []
        async for chunk in client.chat_stream(messages):
            responses.append(chunk)

        assert len(responses) == 2
        assert all(r == "streaming " for r in responses)

    @patch.dict('os.environ', {
        'LLM_PROVIDER': 'claude',
        'ANTHROPIC_API_KEY': 'test-key',
        'OPENAI_API_KEY': 'test-key',
        'LLM_MODEL': 'test-model',
        'LLM_TEMPERATURE': '0.5',
        'LLM_MAX_TOKENS': '100'
    })
    @pytest.mark.asyncio
    async def test_chat_stream_claude_fallback(self):
        """测试Claude流式响应回退"""
        client = LLMClient(provider="claude")

        # Mock普通chat响应
        mock_response = {"content": "fallback response"}
        client.chat = Mock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hello"}]

        # 收集流式响应
        responses = []
        async for chunk in client.chat_stream(messages):
            responses.append(chunk)

        assert len(responses) == 1
        assert responses[0] == "fallback response"
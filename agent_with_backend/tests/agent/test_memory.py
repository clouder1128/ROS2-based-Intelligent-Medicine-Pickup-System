"""MessageManager / Compressor 单元测试

MessageManager 依赖 Config.MAX_HISTORY_LEN（已在 conftest 中设为 50）。
Compressor 函数为纯算法，无外部依赖。
"""

from agent.memory.manager import MessageManager
from agent.memory.compressor import (
    compress_messages_by_tokens,
    compress_messages_by_count,
    smart_compress,
)


class TestMessageManagerInit:
    def test_init_with_system_prompt(self):
        mgr = MessageManager(system_prompt="你是医疗助手")
        messages = mgr.get_full_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "你是医疗助手"

    def test_init_without_system_prompt(self):
        mgr = MessageManager()
        messages = mgr.get_full_messages()
        assert len(messages) == 0

    def test_get_messages_without_system(self):
        mgr = MessageManager(system_prompt="system")
        messages = mgr.get_messages()
        assert len(messages) == 0


class TestMessageManagerAdd:
    def test_add_user_message(self):
        mgr = MessageManager(system_prompt="system")
        mgr.add_message("user", "头痛三天")
        full = mgr.get_full_messages()
        assert len(full) == 2
        assert full[1]["role"] == "user"
        assert full[1]["content"] == "头痛三天"

    def test_add_assistant_message(self):
        mgr = MessageManager(system_prompt="system")
        mgr.add_message("user", "头痛")
        mgr.add_message("assistant", "建议服用布洛芬")
        full = mgr.get_full_messages()
        assert len(full) == 3

    def test_add_tool_result(self):
        mgr = MessageManager(system_prompt="system")
        mgr.add_tool_result("call_123", json.dumps({"result": "ok"}))
        messages = mgr.get_full_messages()
        tool_msg = messages[-1]
        assert tool_msg["role"] == "tool"
        assert tool_msg["tool_call_id"] == "call_123"

    def test_add_tool_message_with_dict_content(self):
        mgr = MessageManager(system_prompt="system")
        mgr.add_tool_result("call_456", {"result": "ok"})
        messages = mgr.get_full_messages()
        assert messages[-1]["role"] == "tool"


class TestMessageManagerReset:
    def test_reset_keeps_system(self):
        mgr = MessageManager(system_prompt="system")
        mgr.add_message("user", "头痛")
        mgr.reset(keep_system=True)
        assert len(mgr.get_full_messages()) == 1
        assert mgr.get_full_messages()[0]["role"] == "system"

    def test_reset_without_system(self):
        mgr = MessageManager(system_prompt="system")
        mgr.add_message("user", "头痛")
        mgr.reset(keep_system=False)
        assert len(mgr.get_full_messages()) == 0


class TestCompressByTokens:
    def test_basic_compression(self):
        messages = [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "a" * 1000},
            {"role": "assistant", "content": "b" * 1000},
        ]
        result = compress_messages_by_tokens(messages, max_tokens=100, preserve_system=True)
        assert len(result) <= 2  # system + maybe one more

    def test_compress_does_not_remove_system(self):
        messages = [
            {"role": "system", "content": "keep me"},
            {"role": "user", "content": "a" * 5000},
        ]
        result = compress_messages_by_tokens(messages, max_tokens=10, preserve_system=True)
        assert len(result) >= 1
        assert result[0]["role"] == "system"

    def test_compress_removes_all_when_no_preserve(self):
        messages = [
            {"role": "system", "content": "remove me"},
        ]
        result = compress_messages_by_tokens(messages, max_tokens=1, preserve_system=False)
        assert len(result) == 0


class TestCompressByCount:
    def test_count_compression(self):
        messages = [{"role": "user", "content": f"msg{i}"} for i in range(10)]
        result = compress_messages_by_count(messages, max_messages=3, preserve_system=False)
        assert len(result) <= 3

    def test_count_preserves_system(self):
        messages = [{"role": "system", "content": "sys"}] + [
            {"role": "user", "content": f"msg{i}"} for i in range(10)
        ]
        result = compress_messages_by_count(messages, max_messages=3, preserve_system=True)
        assert len(result) <= 4
        assert result[0]["role"] == "system"

    def test_count_noop_when_under_limit(self):
        messages = [{"role": "user", "content": "hi"}]
        result = compress_messages_by_count(messages, max_messages=10)
        assert len(result) == 1


class TestSmartCompress:
    def test_smart_compress(self):
        messages = [{"role": "system", "content": "sys"}] + [
            {"role": "user", "content": "a" * 500} for _ in range(10)
        ]
        result = smart_compress(messages, max_tokens=50, max_messages=3)
        assert len(result) <= 4  # system + at most 3


import json  # noqa: E402

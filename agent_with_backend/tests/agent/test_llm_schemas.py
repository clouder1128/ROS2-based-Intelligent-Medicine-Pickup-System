"""LLM 数据模型（LLMMessage / ToolCall / LLMResponse）单元测试

纯 dataclass，无外部依赖。
"""

from agent.llm.schemas import LLMMessage, ToolCall, LLMResponse


class TestLLMMessage:
    def test_create_user_message(self):
        msg = LLMMessage(role="user", content="头痛三天")
        assert msg.role == "user"
        assert msg.content == "头痛三天"
        assert msg.tool_call_id is None
        assert msg.tool_calls is None

    def test_create_assistant_with_tool_calls(self):
        tc = ToolCall(name="query_drug", input={"query": "头痛"}, id="call_001")
        msg = LLMMessage(role="assistant", content="查询中", tool_calls=[tc])
        assert msg.role == "assistant"
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "query_drug"

    def test_to_dict(self):
        msg = LLMMessage(role="user", content="测试")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "测试"
        # tool_call_id / tool_calls 为 None 时不会出现在 dict 中

    def test_to_dict_with_tool_call_id(self):
        msg = LLMMessage(role="tool", content="result", tool_call_id="call_001")
        d = msg.to_dict()
        assert d["tool_call_id"] == "call_001"

    def test_from_dict(self):
        data = {"role": "user", "content": "测试", "tool_call_id": None, "tool_calls": None}
        msg = LLMMessage.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "测试"

    def test_from_dict_with_tool_calls(self):
        data = {
            "role": "assistant",
            "content": "",
            "tool_call_id": None,
            "tool_calls": [
                {"name": "query_drug", "input": {"query": "头痛"}, "id": "call_001"}
            ],
        }
        msg = LLMMessage.from_dict(data)
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0]["name"] == "query_drug"
        assert msg.tool_calls[0]["input"] == {"query": "头痛"}


class TestToolCall:
    def test_create_tool_call(self):
        tc = ToolCall(name="query_drug", input={"query": "头痛"}, id="call_001")
        assert tc.name == "query_drug"
        assert tc.input == {"query": "头痛"}
        assert tc.id == "call_001"

    def test_to_dict(self):
        tc = ToolCall(name="query_drug", input={"query": "头痛"}, id="call_001")
        d = tc.to_dict()
        assert d["name"] == "query_drug"
        assert d["input"] == {"query": "头痛"}
        assert d["id"] == "call_001"

    def test_from_dict(self):
        data = {"name": "query_drug", "input": {"query": "头痛"}, "id": "call_001"}
        tc = ToolCall.from_dict(data)
        assert tc.name == "query_drug"
        assert tc.input == {"query": "头痛"}
        assert tc.id == "call_001"


class TestLLMResponse:
    def test_create_response(self):
        tc = ToolCall(name="query_drug", input={"query": "头痛"}, id="call_001")
        resp = LLMResponse(
            content="查询结果",
            tool_calls=[tc],
            usage={"input_tokens": 10, "output_tokens": 20},
        )
        assert resp.content == "查询结果"
        assert len(resp.tool_calls) == 1
        assert resp.usage["input_tokens"] == 10

    def test_to_dict(self):
        resp = LLMResponse(content="您好", tool_calls=[], usage={})
        d = resp.to_dict()
        assert d["content"] == "您好"
        assert d["tool_calls"] == []

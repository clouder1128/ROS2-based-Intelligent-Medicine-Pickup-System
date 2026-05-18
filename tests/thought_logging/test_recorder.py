# tests/thought_logging/test_recorder.py
import time
import json
from unittest.mock import Mock, patch
from agent_with_backend.P1.thought_logging.recorder import ThoughtRecorder
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_recorder_initialization():
    """测试记录器初始化"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    assert recorder.enabled == True
    assert recorder.config == config
    assert recorder.session_id is not None
    assert recorder.thoughts == []
    assert recorder.current_iteration == 0

def test_recorder_disabled():
    """测试禁用状态的记录器"""
    config = ThoughtLoggingConfig(enabled=False)
    recorder = ThoughtRecorder(config)

    # 当禁用时，记录方法应该不存储数据
    recorder.record_llm_call(0, ["msg1", "msg2"], {"content": "response"})
    assert len(recorder.thoughts) == 0

    # 但应该仍然有session_id
    assert recorder.session_id is not None

def test_record_llm_call():
    """测试记录LLM调用"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    messages = [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "测试消息"}
    ]
    response = {
        "content": "调用工具",
        "tool_calls": [{"name": "query_drug", "input": {"症状": "头疼"}}]
    }
    metadata = {"provider": "claude", "model": "claude-3-sonnet"}

    recorder.record_llm_call(1, messages, response, metadata)

    assert len(recorder.thoughts) == 1
    thought = recorder.thoughts[0]

    assert thought["type"] == "llm_call"
    assert thought["iteration"] == 1
    assert thought["messages"] == messages
    assert thought["response"] == response
    assert thought["metadata"]["provider"] == "claude"
    assert "timestamp" in thought
    assert "session_id" in thought

def test_record_tool_decision():
    """测试记录工具调用决策"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    tool_name = "query_drug"
    input_data = {"症状": "头疼"}
    reasoning = "根据症状查询相关药物"
    result = {"drugs": ["布洛芬"]}

    recorder.record_tool_decision(2, tool_name, input_data, reasoning, result)

    assert len(recorder.thoughts) == 1
    thought = recorder.thoughts[0]

    assert thought["type"] == "tool_decision"
    assert thought["iteration"] == 2
    assert thought["tool_name"] == tool_name
    assert thought["input"] == input_data
    assert thought["reasoning"] == reasoning
    assert thought["result"] == result

def test_record_iteration_state():
    """测试记录迭代状态"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    state = {
        "messages_count": 5,
        "tools_called": ["query_drug"],
        "workflow_step": "query_drug"
    }

    recorder.record_iteration_state(3, state)

    assert len(recorder.thoughts) == 1
    thought = recorder.thoughts[0]

    assert thought["type"] == "iteration_state"
    assert thought["iteration"] == 3
    assert thought["state"] == state

def test_get_thoughts_by_type():
    """测试按类型获取思考记录"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    # 添加多种类型的记录
    recorder.record_llm_call(1, [], {})
    recorder.record_tool_decision(1, "tool", {}, "reason", {})
    recorder.record_llm_call(2, [], {})
    recorder.record_iteration_state(2, {})

    llm_calls = recorder.get_thoughts_by_type("llm_call")
    assert len(llm_calls) == 2

    tool_decisions = recorder.get_thoughts_by_type("tool_decision")
    assert len(tool_decisions) == 1

    iteration_states = recorder.get_thoughts_by_type("iteration_state")
    assert len(iteration_states) == 1

def test_clear_thoughts():
    """测试清空思考记录"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    recorder.record_llm_call(1, [], {})
    recorder.record_tool_decision(1, "tool", {}, "reason", {})

    assert len(recorder.thoughts) == 2

    recorder.clear_thoughts()
    assert len(recorder.thoughts) == 0
    assert recorder.current_iteration == 0

def test_update_iteration():
    """测试更新迭代计数器"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    assert recorder.current_iteration == 0

    recorder.update_iteration(5)
    assert recorder.current_iteration == 5

    # 记录应该使用新的迭代号
    recorder.record_llm_call(None, [], {})
    assert recorder.thoughts[0]["iteration"] == 5


def test_get_thoughts_by_iteration():
    """测试按迭代号获取思考记录"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    # 添加不同迭代的记录
    recorder.record_llm_call(1, [], {})
    recorder.record_tool_decision(1, "tool1", {}, "reason1", {})
    recorder.record_llm_call(2, [], {})
    recorder.record_iteration_state(2, {})
    recorder.record_llm_call(3, [], {})

    # 获取迭代1的记录
    iteration1_thoughts = recorder.get_thoughts_by_iteration(1)
    assert len(iteration1_thoughts) == 2
    assert all(t["iteration"] == 1 for t in iteration1_thoughts)

    # 获取迭代2的记录
    iteration2_thoughts = recorder.get_thoughts_by_iteration(2)
    assert len(iteration2_thoughts) == 2
    assert all(t["iteration"] == 2 for t in iteration2_thoughts)

    # 获取迭代3的记录
    iteration3_thoughts = recorder.get_thoughts_by_iteration(3)
    assert len(iteration3_thoughts) == 1
    assert all(t["iteration"] == 3 for t in iteration3_thoughts)

    # 获取不存在的迭代
    iteration4_thoughts = recorder.get_thoughts_by_iteration(4)
    assert len(iteration4_thoughts) == 0


def test_get_stats():
    """测试获取统计信息"""
    config = ThoughtLoggingConfig(enabled=True)
    recorder = ThoughtRecorder(config)

    # 空记录器
    stats = recorder.get_stats()
    assert stats["total"] == 0

    # 添加一些记录
    recorder.record_llm_call(1, [], {})
    recorder.record_tool_decision(1, "tool1", {}, "reason1", {})
    recorder.record_llm_call(2, [], {})
    recorder.record_iteration_state(2, {})
    recorder.record_llm_call(3, [], {})

    stats = recorder.get_stats()
    assert stats["total"] == 5
    assert stats["session_id"] == recorder.session_id
    assert "first_timestamp" in stats
    assert "last_timestamp" in stats

    # 检查类型统计
    assert stats["by_type"]["llm_call"] == 3
    assert stats["by_type"]["tool_decision"] == 1
    assert stats["by_type"]["iteration_state"] == 1

    # 检查迭代统计
    assert stats["by_iteration"][1] == 2
    assert stats["by_iteration"][2] == 2
    assert stats["by_iteration"][3] == 1
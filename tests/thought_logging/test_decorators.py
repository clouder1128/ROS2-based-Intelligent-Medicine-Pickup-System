# tests/thought_logging/test_decorators.py
import functools
from unittest.mock import Mock, patch, MagicMock
from agent_with_backend.P1.thought_logging.decorators import (
    with_thought_logging,
    ThoughtLoggingDecorator,
    record_llm_calls,
    record_tool_decisions
)
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig
from agent_with_backend.P1.thought_logging.recorder import ThoughtRecorder

def test_with_thought_logging_decorator():
    """测试with_thought_logging装饰器"""
    # 创建一个模拟的Agent类
    class MockAgent:
        def __init__(self):
            self.value = "original"

        def run(self, message):
            return f"Processed: {message}"

    # 创建装饰后的Agent
    config = ThoughtLoggingConfig(enabled=True)
    decorated_agent = with_thought_logging(MockAgent(), config)

    # 验证装饰器添加了_recorder属性
    assert hasattr(decorated_agent, '_recorder')
    assert isinstance(decorated_agent._recorder, ThoughtRecorder)
    assert decorated_agent._recorder.enabled == True

    # 验证原始方法仍然可用
    assert decorated_agent.value == "original"
    result = decorated_agent.run("test message")
    assert result == "Processed: test message"

def test_thought_logging_decorator_class():
    """测试ThoughtLoggingDecorator类"""
    # 创建被装饰的类
    class TestClass:
        def __init__(self, name):
            self.name = name

        def method1(self, arg):
            return f"{self.name}: {arg}"

        def method2(self, a, b):
            return a + b

    # 创建装饰器配置
    config = ThoughtLoggingConfig(enabled=True)
    decorator = ThoughtLoggingDecorator(config)

    # 装饰类
    DecoratedClass = decorator.decorate_class(TestClass)

    # 创建实例
    instance = DecoratedClass("test")

    # 验证装饰器添加了_recorder属性
    assert hasattr(instance, '_recorder')
    assert instance._recorder.enabled == True

    # 验证原始方法仍然可用
    assert instance.name == "test"
    assert instance.method1("hello") == "test: hello"
    assert instance.method2(2, 3) == 5

def test_record_llm_calls_decorator():
    """测试record_llm_calls装饰器"""
    # 创建模拟的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True

    # 创建被装饰的函数
    @record_llm_calls(mock_recorder)
    def llm_chat(messages, **kwargs):
        return {
            "content": "Test response",
            "tool_calls": []
        }

    # 调用函数
    messages = [{"role": "user", "content": "test"}]
    result = llm_chat(messages, model="claude", temperature=0.5)

    # 验证结果
    assert result["content"] == "Test response"

    # 验证recorder被调用
    assert mock_recorder.record_llm_call.called
    call_args = mock_recorder.record_llm_call.call_args

    # 验证参数（装饰器使用关键字参数调用）
    assert call_args.kwargs.get('iteration') is None  # iteration=None
    assert call_args.kwargs.get('messages') == messages
    assert call_args.kwargs.get('response')["content"] == "Test response"
    assert call_args.kwargs.get('metadata')["model"] == "claude"
    assert call_args.kwargs.get('metadata')["temperature"] == 0.5

def test_record_llm_calls_disabled():
    """测试禁用的record_llm_calls装饰器"""
    # 创建禁用的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = False

    @record_llm_calls(mock_recorder)
    def llm_chat(messages):
        return {"content": "response"}

    # 调用函数
    result = llm_chat([])

    # 验证结果
    assert result["content"] == "response"

    # 验证recorder未被调用（因为禁用）
    assert not mock_recorder.record_llm_call.called

def test_record_tool_decisions_decorator():
    """测试record_tool_decisions装饰器"""
    # 创建模拟的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True

    # 创建被装饰的函数
    @record_tool_decisions(mock_recorder)
    def execute_tool(tool_name, tool_input, **kwargs):
        return {"success": True, "result": "tool result"}

    # 调用函数
    tool_name = "query_drug"
    tool_input = {"症状": "头疼"}
    reasoning = "根据症状查询药物"

    result = execute_tool(
        tool_name,
        tool_input,
        reasoning=reasoning,
        iteration=2
    )

    # 验证结果
    assert result["success"] == True

    # 验证recorder被调用
    assert mock_recorder.record_tool_decision.called
    call_args = mock_recorder.record_tool_decision.call_args

    # 验证参数（装饰器使用关键字参数调用）
    assert call_args.kwargs.get('iteration') == 2  # iteration=2
    assert call_args.kwargs.get('tool_name') == tool_name
    assert call_args.kwargs.get('input_data') == tool_input
    assert call_args.kwargs.get('reasoning') == reasoning
    assert call_args.kwargs.get('result')["success"] == True

def test_decorator_preserves_metadata():
    """测试装饰器保留函数元数据"""
    def original_func(arg1, arg2=None):
        """原始函数的文档字符串"""
        return arg1 + (arg2 or 0)

    original_func.custom_attr = "custom_value"

    # 装饰函数
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True

    decorated_func = record_llm_calls(mock_recorder)(original_func)

    # 验证元数据被保留
    assert decorated_func.__name__ == "original_func"
    assert decorated_func.__doc__ == "原始函数的文档字符串"
    assert decorated_func.custom_attr == "custom_value"

    # 验证签名被保留
    import inspect
    sig = inspect.signature(decorated_func)
    params = list(sig.parameters.keys())
    assert params == ["arg1", "arg2"]

def test_decorator_error_handling():
    """测试装饰器错误处理"""
    # 创建会抛出异常的recorder
    mock_recorder = Mock(spec=ThoughtRecorder)
    mock_recorder.enabled = True
    mock_recorder.record_llm_call.side_effect = Exception("Recorder error")

    @record_llm_calls(mock_recorder)
    def llm_chat(messages):
        return {"content": "response"}

    # 调用应该成功，即使recorder出错
    result = llm_chat([])
    assert result["content"] == "response"

    # 验证recorder被调用（虽然出错了）
    assert mock_recorder.record_llm_call.called
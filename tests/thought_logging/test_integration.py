# tests/thought_logging/test_integration.py
import os
import tempfile
from unittest.mock import Mock, patch
from agent_with_backend.P1.thought_logging import with_thought_logging
from agent_with_backend.P1.core.agent import MedicalAgent
from agent_with_backend.P1.thought_logging.config import ThoughtLoggingConfig

def test_integration_with_medical_agent():
    """测试与MedicalAgent的集成"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建配置
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir,
            log_formats=["json", "text"]
        )

        # 创建MedicalAgent（模拟）
        class MockLLMClient:
            def chat(self, messages, tools=None, temperature=None):
                return {
                    "content": "调用 query_drug(症状='头疼')",
                    "tool_calls": [{"name": "query_drug", "input": {"症状": "头疼"}}]
                }

        # 使用patch模拟MedicalAgent的依赖
        with patch('agent_with_backend.P1.core.agent.LLMClient', MockLLMClient):
            # 创建原始Agent
            original_agent = MedicalAgent()

            # 使用思考记录装饰器
            decorated_agent = with_thought_logging(original_agent, config)

            # 验证装饰器添加了属性
            assert hasattr(decorated_agent, '_recorder')
            assert hasattr(decorated_agent, '_output_manager')
            assert decorated_agent._recorder.enabled == True

            # 验证原始方法仍然可用
            assert hasattr(decorated_agent, 'run')
            assert hasattr(decorated_agent, 'reset')
            assert hasattr(decorated_agent, 'get_approval_id')

            # 验证run方法被装饰
            # 注意：由于Mock，我们无法实际运行run方法，但可以验证属性存在

def test_integration_disabled():
    """测试禁用状态的集成"""
    # 创建禁用配置
    config = ThoughtLoggingConfig(enabled=False)

    # 创建原始Agent
    original_agent = MedicalAgent()

    # 使用思考记录装饰器
    decorated_agent = with_thought_logging(original_agent, config)

    # 验证装饰器添加了属性（即使禁用）
    assert hasattr(decorated_agent, '_recorder')
    assert decorated_agent._recorder.enabled == False

def test_integration_cli_compatibility():
    """测试CLI兼容性"""
    # 验证思考记录模块不会破坏现有CLI接口
    from agent_with_backend.P1.cli.interactive import simple_interactive_mode

    # 使用patch模拟用户输入和Agent运行
    with patch('builtins.input', side_effect=["/exit"]), \
         patch('agent_with_backend.P1.core.agent.MedicalAgent') as MockAgent, \
         patch('agent_with_backend.P1.thought_logging.with_thought_logging') as mock_decorator:

        # 配置模拟
        mock_agent_instance = Mock()
        mock_agent_instance.run.return_value = ("响应内容", [])
        MockAgent.return_value = mock_agent_instance

        # 模拟装饰器返回原对象
        mock_decorator.side_effect = lambda x, config=None: x

        # 运行CLI函数（应该正常退出）
        try:
            simple_interactive_mode()
            # 如果到达这里，说明没有异常
            assert True
        except Exception as e:
            # 不应该有异常
            assert False, f"CLI函数抛出异常: {e}"

def test_log_file_generation():
    """测试日志文件生成"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建配置
        config = ThoughtLoggingConfig(
            enabled=True,
            log_to_file=True,
            log_to_console=False,
            log_dir=temp_dir,
            log_formats=["json", "text"]
        )

        # 创建装饰器
        from agent_with_backend.P1.thought_logging import ThoughtLoggingDecorator
        decorator = ThoughtLoggingDecorator(config)

        # 模拟一个类
        class TestAgent:
            def run(self, message):
                # 简单的run方法，返回结果
                # 装饰器会自动记录迭代状态
                return f"处理结果: {message}"

        # 装饰类
        DecoratedAgent = decorator.decorate_class(TestAgent)

        # 创建实例
        agent = DecoratedAgent()

        # 运行方法
        result = agent.run("测试消息")
        assert result == "处理结果: 测试消息"

        # 检查思考记录是否生成
        print(f"Recorder enabled: {agent._recorder.enabled}")
        print(f"Thoughts count: {len(agent._recorder.thoughts)}")
        print(f"Session ID: {agent._recorder.session_id}")

        # 验证日志文件生成
        session_id = agent._recorder.session_id
        # 注意：写入器在log_dir下直接创建session_id目录，不是sessions子目录
        session_dir = os.path.join(temp_dir, session_id)

        print(f"Session dir: {session_dir}")
        print(f"Session dir exists: {os.path.exists(session_dir)}")

        assert os.path.exists(session_dir)
        assert os.path.exists(os.path.join(session_dir, "thoughts.json"))
        assert os.path.exists(os.path.join(session_dir, "thoughts.log"))
# test_core.py
"""测试核心模块：MedicalAgent和WorkflowManager"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from core import MedicalAgent, WorkflowManager, WorkflowStep
from core import run_agent, reset_agent, get_agent_status, save_current_session, load_session
from llm import LLMClient
from memory import MessageManager


class TestWorkflowManager:
    """测试WorkflowManager类"""

    def test_create_workflow(self):
        """测试创建工作流"""
        manager = WorkflowManager()
        workflow = manager.create_workflow("patient_123")

        assert workflow.patient_id == "patient_123"
        assert workflow.current_step == WorkflowStep.COLLECT_INFO
        assert len(workflow.completed_steps) == 0
        assert not workflow.is_completed

    def test_get_workflow(self):
        """测试获取工作流"""
        manager = WorkflowManager()
        manager.create_workflow("patient_123")

        workflow = manager.get_workflow("patient_123")
        assert workflow is not None
        assert workflow.patient_id == "patient_123"

        # 测试不存在的患者
        assert manager.get_workflow("nonexistent") is None

    def test_update_workflow_step(self):
        """测试更新工作流步骤"""
        manager = WorkflowManager()
        manager.create_workflow("patient_123")

        # 更新第一个步骤
        result = manager.update_workflow_step("patient_123", WorkflowStep.QUERY_DRUG, {"drug": "aspirin"})
        assert result is True

        workflow = manager.get_workflow("patient_123")
        assert WorkflowStep.QUERY_DRUG in workflow.completed_steps
        assert workflow.current_step == WorkflowStep.CHECK_ALLERGY
        assert workflow.step_data[WorkflowStep.QUERY_DRUG]["drug"] == "aspirin"

    def test_set_approval_id(self):
        """测试设置审批ID"""
        manager = WorkflowManager()
        manager.create_workflow("patient_123")

        result = manager.set_approval_id("patient_123", "approval_456")
        assert result is True

        workflow = manager.get_workflow("patient_123")
        assert workflow.approval_id == "approval_456"

        # 测试不存在的患者
        result = manager.set_approval_id("nonexistent", "approval_789")
        assert result is False

    def test_get_all_workflows(self):
        """测试获取所有工作流"""
        manager = WorkflowManager()
        manager.create_workflow("patient_123")
        manager.create_workflow("patient_456")

        workflows = manager.get_all_workflows()
        assert len(workflows) == 2
        assert all(isinstance(wf, dict) for wf in workflows)
        patient_ids = {wf["patient_id"] for wf in workflows}
        assert patient_ids == {"patient_123", "patient_456"}

    def test_clear_completed(self):
        """测试清理已完成的工作流"""
        manager = WorkflowManager()

        # 创建并完成一个工作流
        workflow1 = manager.create_workflow("patient_123")
        for step in WorkflowStep:
            workflow1.mark_step_completed(step)

        # 创建未完成的工作流
        manager.create_workflow("patient_456")

        # 清理已完成的工作流
        cleared = manager.clear_completed(older_than_hours=0)  # 立即清理
        assert cleared == 1

        workflows = manager.get_all_workflows()
        assert len(workflows) == 1
        assert workflows[0]["patient_id"] == "patient_456"

    def test_get_stats(self):
        """测试获取统计信息"""
        manager = WorkflowManager()
        manager.create_workflow("patient_123")
        manager.create_workflow("patient_456")

        stats = manager.get_stats()
        assert stats["total_workflows"] == 2
        assert stats["completed"] == 0
        assert stats["in_progress"] == 2
        assert 0 <= stats["average_progress"] <= 1


class TestMedicalAgent:
    """测试MedicalAgent类"""

    @pytest.fixture
    def mock_llm_client(self):
        """创建模拟的LLMClient"""
        mock_client = Mock(spec=LLMClient)
        mock_client.chat.return_value = {"content": "测试回复"}
        return mock_client

    @pytest.fixture
    def mock_message_manager(self):
        """创建模拟的MessageManager"""
        mock_manager = Mock(spec=MessageManager)
        mock_manager.get_full_messages.return_value = []
        mock_manager.get_conversation_length.return_value = 0
        mock_manager.estimate_total_tokens.return_value = 0
        return mock_manager

    def test_agent_creation(self, mock_llm_client, mock_message_manager):
        """测试Agent创建"""
        # 测试依赖注入
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager
        )

        assert agent.llm_client == mock_llm_client
        assert agent.message_manager == mock_message_manager
        assert agent.workflow_manager is not None
        assert agent.patient_id is None
        assert agent.approval_id is None

    def test_agent_creation_default(self):
        """测试Agent默认创建"""
        agent = MedicalAgent()

        assert isinstance(agent.llm_client, LLMClient)
        assert isinstance(agent.message_manager, MessageManager)
        assert agent.workflow_manager is not None

    @patch('core.agent.execute_tool')
    @patch('core.agent.extract_symptoms')
    def test_agent_run_basic(self, mock_extract_symptoms, mock_execute_tool, mock_llm_client, mock_message_manager):
        """测试Agent基本运行"""
        mock_extract_symptoms.return_value = {"symptoms": "头痛"}
        mock_llm_client.chat.return_value = {"content": "请提供更多症状信息"}

        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager
        )

        reply, steps = agent.run("我头痛", "patient_123")

        assert reply == "请提供更多症状信息"
        assert len(steps) == 1
        assert steps[0]["type"] == "assistant"
        assert agent.patient_id == "patient_123"

        # 验证工作流已创建
        workflow_state = agent.get_workflow_state("patient_123")
        assert workflow_state is not None
        assert workflow_state["patient_id"] == "patient_123"

    @patch('core.agent.execute_tool')
    @patch('core.agent.extract_symptoms')
    def test_agent_run_with_tool_call(self, mock_extract_symptoms, mock_execute_tool, mock_llm_client, mock_message_manager):
        """测试Agent运行包含工具调用"""
        mock_extract_symptoms.return_value = {"symptoms": "头痛"}
        mock_execute_tool.return_value = {"drugs": ["布洛芬"]}

        # 模拟LLM响应序列：第一次返回工具调用，第二次返回普通回复
        mock_llm_client.chat.side_effect = [
            {
                "tool_calls": [
                    {
                        "name": "query_drug",
                        "input": {"symptoms": "头痛"}
                    }
                ]
            },
            {
                "content": "根据查询结果，建议使用布洛芬"
            }
        ]

        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager
        )

        reply, steps = agent.run("我头痛", "patient_123")

        # 验证工具调用被记录（现在有2个步骤：工具调用和助理回复）
        assert len(steps) == 2
        assert steps[0]["type"] == "tool_call"
        assert steps[0]["tool"] == "query_drug"
        assert steps[1]["type"] == "assistant"
        assert "根据查询结果" in steps[1]["content"]

        # 验证工作流步骤已更新
        workflow_state = agent.get_workflow_state("patient_123")
        assert workflow_state is not None
        completed_steps = workflow_state["completed_steps"]
        assert "query_drug" in completed_steps

    def test_agent_reset(self, mock_llm_client, mock_message_manager):
        """测试Agent重置"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager
        )

        # 设置一些状态
        agent.patient_id = "patient_123"
        agent.approval_id = "approval_456"
        agent.last_steps = [{"step": 0, "type": "test"}]

        agent.reset()

        assert agent.patient_id is None
        assert agent.approval_id is None
        assert agent.last_steps == []
        mock_message_manager.reset.assert_called_once_with(keep_system=True)

    def test_agent_save_load_state(self, mock_llm_client, mock_message_manager):
        """测试Agent状态保存和加载"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager
        )

        # 设置一些状态
        agent.patient_id = "patient_123"
        agent.approval_id = "approval_456"

        # 模拟消息历史
        mock_message_manager.get_full_messages.return_value = [
            {"role": "user", "content": "我头痛"},
            {"role": "assistant", "content": "请提供更多信息"}
        ]

        # 保存状态
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            agent.save_state(tmp_path)
            assert os.path.exists(tmp_path)

            # 创建新Agent并加载状态
            new_agent = MedicalAgent(
                llm_client=mock_llm_client,
                message_manager=Mock(spec=MessageManager)
            )

            result = new_agent.load_state(tmp_path)
            assert result is True
            assert new_agent.patient_id == "patient_123"
            assert new_agent.approval_id == "approval_456"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_agent_get_workflow_state(self, mock_llm_client, mock_message_manager):
        """测试获取工作流状态"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager
        )

        # 没有患者ID时返回None
        assert agent.get_workflow_state() is None

        # 设置患者ID但无工作流
        agent.patient_id = "patient_123"
        assert agent.get_workflow_state() is None

        # 运行一次以创建工作流
        with patch('core.agent.extract_symptoms'):
            with patch.object(mock_llm_client, 'chat', return_value={"content": "测试"}):
                agent.run("测试", "patient_123")

        workflow_state = agent.get_workflow_state("patient_123")
        assert workflow_state is not None
        assert workflow_state["patient_id"] == "patient_123"

    def test_agent_get_all_workflows(self, mock_llm_client, mock_message_manager):
        """测试获取所有工作流"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager
        )

        # 创建多个工作流
        with patch('core.agent.extract_symptoms'):
            with patch.object(mock_llm_client, 'chat', return_value={"content": "测试"}):
                agent.run("测试1", "patient_123")
                agent.run("测试2", "patient_456")

        workflows = agent.get_all_workflows()
        assert len(workflows) == 2
        patient_ids = {wf["patient_id"] for wf in workflows}
        assert patient_ids == {"patient_123", "patient_456"}


class TestGlobalFunctions:
    """测试全局便捷函数"""

    @patch('core.MedicalAgent')
    def test_run_agent(self, mock_medical_agent_class):
        """测试run_agent函数"""
        mock_agent = Mock()
        mock_agent.run.return_value = ("回复内容", [{"step": 0, "type": "assistant"}])
        mock_agent.get_approval_id.return_value = "approval_123"
        mock_medical_agent_class.return_value = mock_agent

        # 重置全局Agent以使用模拟
        import core
        core._global_agent = mock_agent

        result = run_agent("我头痛", "patient_123")

        assert result["reply"] == "回复内容"
        assert result["steps"] == [{"step": 0, "type": "assistant"}]
        assert result["approval_id"] == "approval_123"
        mock_agent.run.assert_called_once_with("我头痛", "patient_123")

    @patch('core.MedicalAgent')
    def test_reset_agent(self, mock_medical_agent_class):
        """测试reset_agent函数"""
        mock_agent = Mock()
        mock_medical_agent_class.return_value = mock_agent

        import core
        core._global_agent = mock_agent

        reset_agent()
        mock_agent.reset.assert_called_once()

    @patch('core.MedicalAgent')
    @patch('llm.LLMClient.get_stats')
    def test_get_agent_status(self, mock_get_stats, mock_medical_agent_class):
        """测试get_agent_status函数"""
        mock_agent = Mock()
        mock_agent.patient_id = "patient_123"
        mock_agent.approval_id = "approval_456"
        mock_agent.message_manager.get_conversation_length.return_value = 5
        mock_agent.message_manager.estimate_total_tokens.return_value = 100
        mock_agent.get_workflow_stats.return_value = {"total_workflows": 2}
        mock_get_stats.return_value = {"calls": 10}
        mock_medical_agent_class.return_value = mock_agent

        import core
        core._global_agent = mock_agent

        status = get_agent_status()

        assert status["patient_id"] == "patient_123"
        assert status["approval_id"] == "approval_456"
        assert status["message_count"] == 5
        assert status["estimated_tokens"] == 100
        assert status["llm_stats"] == {"calls": 10}
        assert status["workflow_stats"] == {"total_workflows": 2}

    @patch('core.MedicalAgent')
    def test_save_current_session(self, mock_medical_agent_class):
        """测试save_current_session函数"""
        mock_agent = Mock()
        mock_medical_agent_class.return_value = mock_agent

        import core
        core._global_agent = mock_agent

        save_current_session("/tmp/test.pkl")
        mock_agent.save_state.assert_called_once_with("/tmp/test.pkl")

    @patch('core.MedicalAgent')
    def test_load_session(self, mock_medical_agent_class):
        """测试load_session函数"""
        mock_agent = Mock()
        mock_agent.load_state.return_value = True
        mock_medical_agent_class.return_value = mock_agent

        import core
        core._global_agent = mock_agent

        result = load_session("/tmp/test.pkl")
        assert result is True
        mock_agent.load_state.assert_called_once_with("/tmp/test.pkl")


class TestConfigValidation:
    """测试配置验证功能"""

    def test_config_to_dict(self):
        """测试配置转换为字典"""
        from config import Config

        config_dict = Config.to_dict()

        # 验证返回的是字典
        assert isinstance(config_dict, dict)

        # 验证包含必要的配置项
        expected_keys = [
            "LLM_PROVIDER", "LLM_MODEL", "LLM_MAX_TOKENS", "LLM_TEMPERATURE",
            "PHARMACY_BASE_URL", "DATABASE_URL", "LOG_LEVEL", "MAX_HISTORY_LEN",
            "MAX_ITERATIONS", "SESSION_STATE_DIR", "ENABLE_ASYNC",
            "MAX_CONCURRENT_SESSIONS", "REQUEST_TIMEOUT"
        ]

        for key in expected_keys:
            assert key in config_dict

        # 验证不包含敏感信息
        assert "ANTHROPIC_API_KEY" not in config_dict
        assert "OPENAI_API_KEY" not in config_dict

        # 验证数据库URL被截断
        if config_dict["DATABASE_URL"] and len(config_dict["DATABASE_URL"]) > 20:
            assert "..." in config_dict["DATABASE_URL"]

    def test_config_validate_success(self):
        """测试配置验证成功"""
        from config import Config

        # 使用conftest中设置的有效配置，应该通过验证
        Config.validate()

    def test_config_validate_invalid_provider(self, patch_config):
        """测试无效LLM提供商"""
        from config import Config
        from exceptions import ConfigurationError

        # 设置无效的LLM提供商
        Config.LLM_PROVIDER = "invalid_provider"

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "无效的LLM提供商" in str(exc_info.value)

    def test_config_validate_missing_api_key(self, patch_config):
        """测试缺少API密钥"""
        from config import Config
        from exceptions import ConfigurationError

        # 测试Claude提供商缺少API密钥
        Config.LLM_PROVIDER = "claude"
        Config.ANTHROPIC_API_KEY = None

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "ANTHROPIC_API_KEY" in str(exc_info.value)

        # 测试OpenAI提供商缺少API密钥
        Config.LLM_PROVIDER = "openai"
        Config.ANTHROPIC_API_KEY = "test_key"
        Config.OPENAI_API_KEY = None

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_config_validate_invalid_iterations(self, patch_config):
        """测试无效的MAX_ITERATIONS"""
        from config import Config
        from exceptions import ConfigurationError

        # 测试过小的值
        Config.MAX_ITERATIONS = 0

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "MAX_ITERATIONS" in str(exc_info.value)

        # 测试过大的值
        Config.MAX_ITERATIONS = 51

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "MAX_ITERATIONS" in str(exc_info.value)

    def test_config_validate_invalid_temperature(self, patch_config):
        """测试无效的LLM_TEMPERATURE"""
        from config import Config
        from exceptions import ConfigurationError

        # 测试过小的值
        Config.LLM_TEMPERATURE = -0.1

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "LLM_TEMPERATURE" in str(exc_info.value)

        # 测试过大的值
        Config.LLM_TEMPERATURE = 2.1

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "LLM_TEMPERATURE" in str(exc_info.value)

    def test_config_validate_invalid_concurrent_sessions(self, patch_config):
        """测试无效的MAX_CONCURRENT_SESSIONS"""
        from config import Config
        from exceptions import ConfigurationError

        Config.MAX_CONCURRENT_SESSIONS = -1

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "MAX_CONCURRENT_SESSIONS" in str(exc_info.value)

    def test_config_validate_invalid_request_timeout(self, patch_config):
        """测试无效的REQUEST_TIMEOUT"""
        from config import Config
        from exceptions import ConfigurationError

        Config.REQUEST_TIMEOUT = 0

        with pytest.raises(ConfigurationError) as exc_info:
            Config.validate()

        assert "REQUEST_TIMEOUT" in str(exc_info.value)

    def test_config_validate_session_dir_creation(self, temp_session_dir, patch_config):
        """测试会话目录创建"""
        from config import Config

        # 设置临时目录
        Config.SESSION_STATE_DIR = temp_session_dir

        # 应该成功验证
        Config.validate()

        # 验证目录已创建
        assert os.path.exists(temp_session_dir)

    def test_config_module_import(self):
        """测试配置模块导入时自动验证"""
        # 重新导入config模块应该触发验证
        # 由于conftest中设置了有效的环境变量，应该不会抛出异常
        import importlib
        import config as config_module

        # 重新加载模块
        importlib.reload(config_module)

        # 如果没有异常抛出，测试通过


import tempfile
import os
from unittest.mock import Mock, patch
from llm import LLMClient


class TestAgentCoreFunctions:
    """测试Agent核心功能（从test_agent.py迁移）"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 导入必要的模块
        from core import run_agent, reset_agent, save_current_session, load_session, get_agent_status
        from tools.registry import register_tool_handler, execute_tool, is_tool_registered, get_executor
        self.run_agent = run_agent
        self.reset_agent = reset_agent
        self.save_current_session = save_current_session
        self.load_session = load_session
        self.get_agent_status = get_agent_status
        self.register_tool_handler = register_tool_handler
        self.get_executor = get_executor
        self.execute_tool = execute_tool
        self.is_tool_registered = is_tool_registered

    def test_run_agent_without_llm(self):
        """测试Agent运行（不依赖真实LLM，只验证函数存在）"""
        assert callable(self.run_agent)
        assert callable(self.reset_agent)

    @patch('core._get_global_agent')
    @patch('llm.LLMClient.chat')
    def test_session_persistence(self, mock_llm_chat, mock_get_global_agent):
        """测试会话保存和加载"""
        # 创建模拟的agent
        mock_agent = Mock()
        mock_agent.run.return_value = ("模拟回复", [{"step": 0, "type": "assistant", "content": "模拟回复"}])
        mock_agent.get_approval_id.return_value = None
        mock_agent.patient_id = "test_patient"
        mock_agent.approval_id = None
        mock_agent.message_manager = Mock()
        mock_agent.message_manager.get_conversation_length.return_value = 1
        mock_agent.message_manager.estimate_total_tokens.return_value = 50
        mock_agent.get_workflow_stats.return_value = {"total_workflows": 1}
        mock_agent.save_state = Mock(return_value=None)
        mock_agent.load_state = Mock(return_value=True)
        mock_agent.reset = Mock()

        mock_get_global_agent.return_value = mock_agent

        # Mock LLM响应（虽然agent被模拟，但保持原有mock）
        mock_llm_chat.return_value = {
            "content": [{"type": "text", "text": "建议使用布洛芬，剂量200mg，每日3次。"}],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }

        self.reset_agent()
        # 先运行一次，产生一些状态
        result = self.run_agent("我头痛，年龄30岁，体重70kg，无过敏史", "test_patient")
        assert "reply" in result
        assert result["reply"] == "模拟回复"

        # 保存会话
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            save_path = f.name
        self.save_current_session(save_path)
        mock_agent.save_state.assert_called_once_with(save_path)

        # 重置并加载
        self.reset_agent()
        # reset被调用了两次：一次在之前的self.reset_agent()，一次在这里
        assert mock_agent.reset.call_count == 2
        assert self.get_agent_status()["patient_id"] == "test_patient"
        success = self.load_session(save_path)
        assert success
        mock_agent.load_state.assert_called_once_with(save_path)
        assert self.get_agent_status()["patient_id"] == "test_patient"

        # 清理
        os.unlink(save_path)

    def test_llm_stats(self):
        """测试LLM统计功能"""
        LLMClient.reset_stats()
        stats = LLMClient.get_stats()
        assert stats["requests"] == 0
        # 注意：实际调用LLM需要API密钥，这里只测试方法存在
        assert callable(LLMClient.get_stats)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
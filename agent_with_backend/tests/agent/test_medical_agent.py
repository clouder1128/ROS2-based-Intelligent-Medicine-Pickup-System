"""MedicalAgent 核心引擎单元测试

使用注入的 mock LLMClient / MessageManager 隔离所有外部依赖。
Config 环境变量由 conftest.py 的 autouse fixture + 模块级 os.environ 控制。

注意：不测试 MedicalAgent() 默认构造（需要真实 anthropic/openai SDK）。
"""

import pytest
from unittest.mock import MagicMock
from agent.engine.medical_agent import MedicalAgent


class TestMedicalAgentInit:
    def test_init_with_mocks(self, mock_llm_client, mock_message_manager):
        """注入 mock LLMClient 和 MessageManager"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        assert agent.llm_client is mock_llm_client
        assert agent.message_manager is mock_message_manager

    def test_init_has_workflow_manager(self, mock_llm_client, mock_message_manager):
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        assert hasattr(agent, "workflow_manager")
        assert hasattr(agent, "todo_manager")

    def test_init_tracking_fields(self, mock_llm_client, mock_message_manager):
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        assert agent.patient_id is None
        assert agent.approval_id is None


class TestMedicalAgentReset:
    def test_reset_clears_state(self, mock_llm_client, mock_message_manager):
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        agent.patient_id = "p001"
        agent.approval_id = "AP-001"
        agent.reset()
        assert agent.patient_id is None
        assert agent.approval_id is None


class TestMedicalAgentRun:
    def test_run_basic_with_mocks(self, mock_llm_client, mock_message_manager):
        """用 mock 运行 run()，验证基本流程走通"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        reply, steps = agent.run("我头痛，需要开药", patient_id="p001")
        assert agent.patient_id == "p001"
        assert isinstance(reply, str)
        assert isinstance(steps, list)

    def test_run_returns_reply_content(self, mock_llm_client, mock_message_manager, monkeypatch):
        mock_llm_client.chat.return_value = {
            "content": "建议服用布洛芬200mg，每日2次",
            "tool_calls": [],
            "usage": {},
        }
        # 防御：test_backend_config.py 的 importlib.reload 可能重置 Config 类属性，
        # 直接 patch medical_agent 模块引用的 Config 对象以确保 form 收集被禁用
        import agent.engine.medical_agent as ma_mod
        monkeypatch.setattr(ma_mod.Config, "ENABLE_FORM_COLLECTION", False)
        monkeypatch.setattr(ma_mod.Config, "ENABLE_LLM_SYMPTOM_EXTRACTION", False)
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        reply, steps = agent.run("头痛", patient_id="p001")
        assert "布洛芬" in reply or "建议" in reply

    def test_run_tracks_patient_id(self, mock_llm_client, mock_message_manager):
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        agent.run("头痛", patient_id="patient_42")
        assert agent.patient_id == "patient_42"


class TestMedicalAgentSubmitBasics:
    def test_submit_basics_exists(self, mock_llm_client, mock_message_manager):
        """submit_basics 是可用方法"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        assert hasattr(agent, "submit_basics")
        assert callable(agent.submit_basics)


class TestMedicalAgentGetApprovalStatus:
    def test_get_approval_status_does_not_crash(self, mock_llm_client, mock_message_manager):
        """get_approval_status 对不存在的审批不应抛出异常"""
        agent = MedicalAgent(
            llm_client=mock_llm_client,
            message_manager=mock_message_manager,
        )
        # 不应抛出异常（无论 httpx/backend 是否可用）
        agent.get_approval_status("AP-NONEXISTENT")

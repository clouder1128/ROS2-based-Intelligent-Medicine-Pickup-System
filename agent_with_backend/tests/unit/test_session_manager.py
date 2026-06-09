"""测试会话管理器的创建、缓存、持久化、恢复和删除流程。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from agent.session import manager as session_module


def test_session_manager_creates_caches_and_saves_agents(tmp_path, monkeypatch):
    agent = MagicMock()
    monkeypatch.setattr(session_module, "MedicalAgent", MagicMock(return_value=agent))
    monkeypatch.setattr(
        session_module.Config, "ENABLE_THOUGHT_LOGGING", False
    )

    manager = session_module.SessionManager(str(tmp_path))
    created = manager.get_agent("patient-1")

    assert created is agent
    assert manager.get_agent("patient-1") is agent
    assert manager.get_agent("missing", create_new=False) is None
    assert manager.list_sessions() == ["patient-1"]
    assert manager.get_active_count() == 1

    assert manager.save_session("patient-1") is True
    agent.save_state.assert_called_with(str(tmp_path / "patient-1.pkl"))
    assert manager.save_session("missing") is False

    manager.save_all()
    assert agent.save_state.call_count == 2
    assert manager.cleanup_inactive(1) == 0


def test_session_manager_loads_existing_state(tmp_path, monkeypatch):
    state_file = tmp_path / "patient-1.pkl"
    state_file.write_bytes(b"state")
    agent = MagicMock()
    agent.load_state.return_value = True
    monkeypatch.setattr(session_module, "MedicalAgent", MagicMock(return_value=agent))
    monkeypatch.setattr(
        session_module.Config, "ENABLE_THOUGHT_LOGGING", False
    )

    manager = session_module.SessionManager(str(tmp_path))
    assert manager.get_agent("patient-1") is agent

    agent.load_state.assert_called_once_with(str(state_file))
    agent._load_form_from_session.assert_called_once()


def test_session_manager_create_wrap_and_delete(tmp_path, monkeypatch):
    agent = MagicMock()
    wrapped = SimpleNamespace(_recorder=SimpleNamespace(session_id="session-1"))
    monkeypatch.setattr(session_module, "MedicalAgent", MagicMock(return_value=agent))
    monkeypatch.setattr(session_module.Config, "ENABLE_THOUGHT_LOGGING", True)
    monkeypatch.setattr(
        session_module,
        "ThoughtLoggingConfig",
        lambda: SimpleNamespace(enabled=True),
    )
    wrap = MagicMock(return_value=wrapped)
    monkeypatch.setattr(session_module, "with_thought_logging", wrap)

    manager = session_module.SessionManager(str(tmp_path))
    assert manager.create_agent("patient-1") is wrapped
    wrap.assert_called_once()

    (tmp_path / "patient-1.pkl").write_bytes(b"state")
    (tmp_path / "patient-1_form.pkl").write_bytes(b"form")
    assert manager.delete_session("patient-1") is True
    assert not (tmp_path / "patient-1.pkl").exists()
    assert not (tmp_path / "patient-1_form.pkl").exists()
    assert manager.get_active_count() == 0

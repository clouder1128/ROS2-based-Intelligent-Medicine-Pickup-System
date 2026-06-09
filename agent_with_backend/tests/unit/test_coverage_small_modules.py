"""补充测试校验器、消息管理、待办任务、模型提供商及响应工具等小型模块。"""

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask

from agent.llm.providers.claude import ClaudeProvider
from agent.llm.providers.openai import OpenAIProvider
from agent.llm.schemas import LLMMessage
from agent.memory.manager import MessageManager
from agent.planner.models import TaskCategory, TaskStatus, TodoManager, TodoTask
from common.exceptions import LLMError
from common.utils.logger import get_logger, setup_logger
from common.utils.response import (
    bad_request_response,
    created_response,
    forbidden_response,
    internal_error_response,
    not_found_response,
    paginated_response,
    success_response,
    unauthorized_response,
)
from common.utils.text_utils import (
    estimate_cost,
    estimate_tokens,
    generate_id,
    hash_string,
    log_duration,
    now_iso,
    summarize_conversation,
    validate_patient_input,
)
from common.utils.validation import (
    validate_category,
    validate_drug,
    validate_inventory_transaction,
    validate_pagination_params,
)


def _valid_drug():
    return {
        "name": "布洛芬",
        "quantity": 10,
        "expiry_date": 100,
        "shelf_x": 1,
        "shelf_y": 2,
        "shelve_id": 3,
    }


def test_drug_validation_covers_optional_types_choices_and_json_columns():
    payload = _valid_drug()
    payload.update(
        {
            "category": "C" * 201,
            "description": 123,
            "strength": "S" * 101,
            "stock": "bad",
            "expiry_date": "bad",
            "min_stock_level": -1,
            "max_stock_level": "bad",
            "cost_price": "bad",
            "purchase_price": -1,
            "dosage_form": "invalid",
            "pregnancy_category": 3,
            "unit": "invalid",
            "is_prescription": "TRUE",
            "drug_interactions": object(),
            "age_restrictions": {"bad": {1, 2}},
            "indications": ["ok", 2],
        }
    )

    ok, errors = validate_drug(payload)

    assert ok is False
    for field in [
        "category",
        "description",
        "strength",
        "stock",
        "expiry_date",
        "min_stock_level",
        "max_stock_level",
        "cost_price",
        "purchase_price",
        "dosage_form",
        "pregnancy_category",
        "unit",
        "drug_interactions",
        "age_restrictions",
        "indications",
    ]:
        assert field in errors
    assert "is_prescription" not in errors


def test_drug_validation_handles_missing_fields_long_indications_and_valid_options():
    ok, errors = validate_drug({})
    assert ok is False
    assert {"name", "quantity", "expiry_date", "shelf_x", "shelf_y", "shelve_id"} <= errors.keys()

    payload = _valid_drug()
    payload.update(
        {
            "indications": ["x" * 501],
            "dosage_form": "片剂",
            "pregnancy_category": "B",
            "unit": "盒",
            "is_prescription": "false",
            "drug_interactions": ["阿司匹林"],
            "age_restrictions": '{"min": 12}',
            "retail_price": 1.5,
        }
    )
    ok, errors = validate_drug(payload)
    assert ok is False
    assert list(errors) == ["indications"]


@pytest.mark.parametrize(
    ("validator", "payload", "fields"),
    [
        (
            validate_category,
            {"name": "x" * 51, "description": "x" * 501, "sort_order": "bad", "parent_id": "bad"},
            {"name", "description", "sort_order", "parent_id"},
        ),
        (
            validate_inventory_transaction,
            {"quantity_change": "bad", "transaction_type": "", "reason": "x" * 501, "operator": "x" * 101},
            {"quantity_change", "transaction_type", "reason", "operator"},
        ),
        (
            validate_pagination_params,
            {"page": "bad", "limit": "bad"},
            {"page", "limit"},
        ),
    ],
)
def test_other_validators_report_type_and_length_errors(validator, payload, fields):
    ok, errors = validator(payload)
    assert ok is False
    assert fields <= errors.keys()


def test_message_manager_metadata_queries_and_both_compression_paths(monkeypatch):
    manager = MessageManager(system_prompt="system", max_history=2)
    manager.add_message(
        "assistant",
        "answer",
        tool_call_id="tool-1",
        tool_calls=[{"id": "call-1"}],
    )
    manager.add_message("user", "latest question")
    manager.add_message("assistant", "final")

    assert manager.get_last_user_message() == "latest question"
    assert manager.get_conversation_length() == 3
    assert manager.estimate_total_tokens() >= 0
    assert manager.get_full_messages()[0]["role"] == "system"

    compressed = [{"role": "system", "content": "compressed"}]
    monkeypatch.setattr("agent.memory.manager.smart_compress", lambda *args, **kwargs: compressed)
    manager.max_tokens_limit = 0
    manager._maybe_compress_by_count()
    manager._maybe_compress_by_tokens()
    assert manager.messages == compressed

    empty = MessageManager()
    assert empty.get_last_user_message() is None
    empty.reset()
    assert empty.messages == []


class _Storage:
    def __init__(self):
        self.saved = []
        self.updated = []
        self.deleted = []
        self.loaded = [TodoTask("loaded")]

    def load_all_tasks(self):
        return self.loaded

    def save_task(self, task):
        self.saved.append(task.id)

    def update_task(self, task_id, data):
        self.updated.append((task_id, data))

    def delete_task(self, task_id):
        self.deleted.append(task_id)


def test_todo_edge_validation_storage_and_state_transitions():
    with pytest.raises(ValueError, match="优先级"):
        TodoTask("bad", priority=0)
    with pytest.raises(ValueError, match="状态"):
        TodoTask("bad", status="unknown")

    task = TodoTask("task")
    assert task.is_pending() is True
    assert task.get_completion_time() is None
    task.mark_pending()
    task.mark_blocked()
    task.mark_completed("done")
    assert task.notes == "done"
    assert task.get_completion_time() is not None

    storage = _Storage()
    manager = TodoManager(storage)
    assert manager.get_todo_list()[0].content == "loaded"
    with pytest.raises(ValueError, match="不能为空"):
        manager.add_todo(" ")

    added = manager.add_todo(
        "new",
        category=TaskCategory.SYMPTOM.value,
        related_symptoms=["头痛"],
    )
    assert storage.saved == [added.id]
    assert manager.get_tasks_by_symptom("头痛") == [added]
    assert manager.update_todo("missing") is False
    assert manager.update_todo(added.id, priority=9) is False
    assert manager.update_todo(added.id, status="bad") is False
    assert manager.update_todo(
        added.id,
        content="updated",
        priority=5,
        status=TaskStatus.IN_PROGRESS.value,
        category=TaskCategory.CHECK.value,
        notes="note",
    )
    assert storage.updated
    assert manager.mark_completed("missing") is False
    assert manager.mark_in_progress("missing") is False
    assert manager.delete_todo("missing") is False
    assert manager.delete_todo(added.id) is True
    assert added.id in storage.deleted


def test_todo_sort_filter_clear_and_no_storage_loader():
    manager = TodoManager()
    low = manager.add_todo("low", priority=1)
    high = manager.add_todo("high", priority=5)
    medium = manager.add_todo("medium", priority=3)

    assert manager.get_todo_list()[0] is high
    assert manager.get_todo_list(sort_ascending=True)[0] is low
    assert manager.get_todo_list(sort_by_priority=False)[0] is low
    manager.mark_in_progress(medium.id)
    assert manager.get_todo_list(filter_by_status="in_progress") == [medium]

    low.mark_completed()
    high.mark_completed()
    assert manager.clear_completed_tasks() == 2
    assert list(manager.tasks.values()) == [medium]
    manager._load_from_storage()


def test_claude_provider_maps_messages_tools_usage_and_errors():
    provider = ClaudeProvider.__new__(ClaudeProvider)
    provider.model = "claude-test"
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="answer"),
            SimpleNamespace(type="tool_use", name="search", input={"q": "headache"}),
        ],
        usage=SimpleNamespace(input_tokens=2, output_tokens=3),
    )
    provider.client = SimpleNamespace(
        messages=SimpleNamespace(create=MagicMock(return_value=response))
    )

    result = provider.chat(
        [LLMMessage("system", "sys"), LLMMessage("user", "hello")],
        tools=[{"name": "search", "description": "d", "input_schema": {"type": "object"}}],
        temperature=0.2,
        max_tokens=20,
    )
    assert result.content == "answer"
    assert result.tool_calls[0].name == "search"
    assert result.usage["total_tokens"] == 5

    provider.client.messages.create.side_effect = RuntimeError("network")
    with pytest.raises(LLMError, match="Claude API error"):
        provider.chat([LLMMessage("user", "hello")])


def test_openai_provider_maps_native_and_embedded_tool_calls_and_errors():
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.model = "gpt-test"
    native_message = SimpleNamespace(
        content="answer",
        tool_calls=[
            SimpleNamespace(
                id="tc-1",
                function=SimpleNamespace(name="search", arguments='{"q":"pain"}'),
            )
        ],
    )
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=native_message)],
        usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3, total_tokens=5),
    )
    create = MagicMock(return_value=response)
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )

    result = provider.chat(
        [LLMMessage("user", "hello")],
        tools=[{"name": "search", "description": "d", "input_schema": {"type": "object"}}],
    )
    assert result.tool_calls[0].input == {"q": "pain"}
    assert result.usage["total_tokens"] == 5

    embedded = (
        'prefix {"tool_calls":[{"id":"x","function":{"name":"search",'
        '"arguments":"{\\"q\\":\\"x\\"}"}}]}'
    )
    response.choices[0].message = SimpleNamespace(content=embedded, tool_calls=[])
    result = provider.chat([LLMMessage("user", "hello")])
    assert result.tool_calls[0].name == "search"

    create.side_effect = RuntimeError("network")
    with pytest.raises(LLMError, match="OpenAI API error"):
        provider.chat([LLMMessage("user", "hello")])


def test_logger_text_response_and_engine_convenience_wrappers(monkeypatch):
    logger = setup_logger("coverage-small", logging.DEBUG)
    assert logger.level == logging.DEBUG
    assert setup_logger("coverage-small") is logger
    assert get_logger("coverage-small") is logger

    assert estimate_tokens("abcdefgh") == 2
    assert generate_id("task").startswith("task-")
    assert len(hash_string("value")) == 8
    assert "T" in now_iso()
    assert estimate_cost(1000, "gpt-4") == 0.03
    assert estimate_cost(1000, "unknown") == 0.003
    assert validate_patient_input(None)["valid"] is False
    assert validate_patient_input("x")["valid"] is False
    assert validate_patient_input("drugs please")["valid"] is False
    assert summarize_conversation([]) == "No conversation records"
    with log_duration(logger, "operation"):
        pass

    app = Flask(__name__)
    with app.app_context():
        assert success_response({"ok": 1}, "done")[1] == 200
        assert paginated_response([], 2, 10, 21)[0].get_json()["pagination"]["has_prev"]
        assert paginated_response([], 1, 0, 0)[0].get_json()["pagination"]["pages"] == 0
        assert created_response({})[1] == 201
        assert not_found_response()[1] == 404
        assert bad_request_response()[1] == 400
        assert internal_error_response()[1] == 500
        assert unauthorized_response()[1] == 401
        assert forbidden_response()[1] == 403

    import agent.engine as engine

    fake = MagicMock()
    fake.run.return_value = ("reply", [{"step": 1}])
    fake.get_approval_id.return_value = "AP-1"
    fake.load_state.return_value = True
    monkeypatch.setattr(engine, "_global_agent", fake)
    assert engine.run_agent("hello", "p")["approval_id"] == "AP-1"
    engine.reset_agent()
    engine.save_current_session("state.pkl")
    assert engine.load_session("state.pkl") is True


def test_backend_init_db_creates_seed_rows(tmp_path, monkeypatch):
    import sqlite3
    import sys
    import types

    config_package = types.ModuleType("config")
    settings_module = types.ModuleType("config.settings")
    settings_module.Config = SimpleNamespace(DATABASE_PATH=str(tmp_path / "unused.db"))
    monkeypatch.setitem(sys.modules, "config", config_package)
    monkeypatch.setitem(sys.modules, "config.settings", settings_module)

    import backend.init_db as init_module

    db_path = tmp_path / "backend.db"
    monkeypatch.setattr(init_module, "DB_PATH", str(db_path))
    monkeypatch.setattr("common.utils.database.init_database", lambda: None)
    monkeypatch.setattr(init_module.os.path, "exists", lambda path: False)

    init_module.init_db()

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        expired = conn.execute(
            "SELECT expiry_date FROM inventory WHERE drug_id = 3"
        ).fetchone()[0]
        anchor = conn.execute(
            "SELECT v FROM app_meta WHERE k = 'expiry_sweep_date'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 3
    assert expired == 0
    assert anchor

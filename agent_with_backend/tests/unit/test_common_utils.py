from datetime import date

import pytest

from common.exceptions import AsyncError, WorkflowError
from common.utils.cache import DrugCache, SimpleCache
from common.utils.json_tools import (
    extract_json_from_text,
    format_tool_result,
    safe_parse_json,
)
from common.utils.response import parse_pagination
from common.utils.retry import retry_on_exception
from common.utils.text_utils import (
    extract_mentions_of_allergy,
    merge_dicts,
    safe_get,
    summarize_conversation,
    truncate_text,
    validate_patient_input,
)
from common.utils.validation import (
    validate_category,
    validate_drug,
    validate_inventory_transaction,
    validate_pagination_params,
)
from database.connection import json_serializer


def valid_drug_payload():
    return {
        "name": "Aspirin",
        "quantity": 10,
        "expiry_date": 30,
        "shelf_x": 1,
        "shelf_y": 2,
        "shelve_id": 3,
    }


def test_validate_drug_accepts_valid_create_payload():
    ok, errors = validate_drug(valid_drug_payload())

    assert ok is True
    assert errors == {}


def test_validate_drug_reports_multiple_invalid_fields():
    payload = valid_drug_payload()
    payload.update(
        {
            "name": " ",
            "quantity": -1,
            "min_stock_level": 20,
            "max_stock_level": 10,
            "retail_price": -0.01,
            "indications": "headache",
            "is_prescription": "maybe",
        }
    )

    ok, errors = validate_drug(payload)

    assert ok is False
    assert {
        "name",
        "quantity",
        "min_stock_level",
        "retail_price",
        "indications",
        "is_prescription",
    }.issubset(errors)


def test_validate_drug_update_allows_partial_payload():
    ok, errors = validate_drug({"quantity": 0}, is_update=True)

    assert ok is True
    assert errors == {}


@pytest.mark.parametrize(
    ("validator", "payload"),
    [
        (validate_category, {"name": "OTC", "sort_order": 0}),
        (
            validate_inventory_transaction,
            {"quantity_change": -2, "transaction_type": "out"},
        ),
        (validate_pagination_params, {"page": "2", "limit": "100"}),
    ],
)
def test_validation_helpers_accept_valid_values(validator, payload):
    assert validator(payload) == (True, {})


def test_validation_helpers_reject_invalid_values():
    assert validate_category({"name": "", "parent_id": 0})[0] is False
    assert validate_inventory_transaction(
        {"quantity_change": 0, "transaction_type": "unknown"}
    )[0] is False
    assert validate_pagination_params({"page": 0, "limit": 101})[0] is False


def test_json_helpers_extract_parse_and_format():
    assert extract_json_from_text('result: ```json\n{"ok": true}\n```') == {"ok": True}
    assert extract_json_from_text("no json here") is None
    assert safe_parse_json('{"value": 2}') == {"value": 2}
    assert safe_parse_json("{broken") is None
    assert format_tool_result({"name": "Aspirin"}) == '{"name": "Aspirin"}'
    assert format_tool_result(12) == "12"


def test_text_helpers_cover_nested_access_merge_and_summary():
    assert truncate_text("abcdef", 5) == "ab..."
    assert safe_get({"a": {"b": 3}}, "a.b") == 3
    assert safe_get({"a": 1}, "a.b", "missing") == "missing"
    assert merge_dicts({"a": {"x": 1}}, {"a": {"y": 2}}) == {
        "a": {"x": 1, "y": 2}
    }
    assert validate_patient_input("  headache  ") == {
        "valid": True,
        "cleaned": "headache",
    }
    assert validate_patient_input("suicide risk")["valid"] is False
    assert extract_mentions_of_allergy("penicillin and aspirin") == [
        "penicillin",
        "aspirin",
    ]
    summary = summarize_conversation(
        [{"role": "user", "content": "headache"}, {"role": "assistant", "content": "ok"}]
    )
    assert "headache" in summary


def test_simple_cache_expiration_and_deletion(monkeypatch):
    clock = iter([10.0, 12.0, 12.0, 12.0, 12.0])
    monkeypatch.setattr("common.utils.cache.time.monotonic", lambda: next(clock))
    cache = SimpleCache(default_ttl=1)

    cache.set("a", 1)
    assert cache.get("a") is None
    cache.set("prefix:b", 2, ttl=10)
    cache.set("prefix:c", 3, ttl=10)
    assert cache.delete_prefix("prefix:") == 2
    assert cache.info()["total_keys"] == 0


def test_drug_cache_invalidation():
    cache = DrugCache()
    cache.set_drug_list(None, None, None, "name", "asc", [{"id": 1}])
    cache.set_drug(1, {"id": 1})
    cache.set_stats({"total": 1})
    cache.set_categories(False, [{"id": 1}])

    cache.invalidate_drug_writes(drug_id=1)
    cache.invalidate_categories()

    assert cache.get_drug_list(None, None, None, "name", "asc") is None
    assert cache.get_drug(1) is None
    assert cache.get_stats() is None
    assert cache.get_categories(False) is None


def test_retry_retries_then_returns(monkeypatch):
    sleeps = []
    monkeypatch.setattr("common.utils.retry.time.sleep", sleeps.append)
    calls = {"count": 0}

    @retry_on_exception(ValueError, max_retries=3, delay=0.1, backoff=2)
    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("temporary")
        return "ok"

    assert flaky() == "ok"
    assert sleeps == [0.1, 0.2]


def test_retry_reraises_last_error(monkeypatch):
    monkeypatch.setattr("common.utils.retry.time.sleep", lambda _: None)

    @retry_on_exception(ValueError, max_retries=2, delay=0)
    def always_fails():
        raise ValueError("still broken")

    with pytest.raises(ValueError, match="still broken"):
        always_fails()


def test_pagination_and_exception_messages():
    assert parse_pagination({"page": "3", "limit": "10"}) == {
        "page": 3,
        "limit": 10,
        "offset": 20,
    }
    assert parse_pagination({"page": "bad", "limit": "999"}) == {
        "page": 1,
        "limit": 100,
        "offset": 0,
    }
    assert "workflow: wf-1" in str(WorkflowError("failed", "wf-1", "rank"))
    assert "task: task-1" in str(AsyncError(task_id="task-1"))
    assert json_serializer(date(2026, 6, 7)) == "2026-06-07"
    with pytest.raises(TypeError):
        json_serializer(object())

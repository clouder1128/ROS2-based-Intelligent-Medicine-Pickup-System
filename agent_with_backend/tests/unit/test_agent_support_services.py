"""测试症状提取、库存事务和报表生成等智能体辅助服务。"""

import json
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock

import pytest

from agent.services.symptom_service import SymptomExtractionService
from agent.tools import inventory, report_generator
from common.config import Config


def test_symptom_service_rejects_blank_input():
    with pytest.raises(ValueError):
        SymptomExtractionService.extract("   ")


def test_symptom_service_selects_rule_and_llm_modes(monkeypatch):
    extractor_class = MagicMock()
    extractor = extractor_class.return_value
    extractor.extract.return_value = SimpleNamespace(chief_complaint="headache")
    monkeypatch.setattr(
        "agent.subagents.extractor.SymptomExtractor", extractor_class
    )

    monkeypatch.setattr(Config, "ENABLE_LLM_SYMPTOM_EXTRACTION", False)
    result = SymptomExtractionService.extract("headache", llm_client=MagicMock())
    assert result.chief_complaint == "headache"
    extractor_class.assert_called_with(ANY, use_llm=False)

    extractor_class.reset_mock()
    llm_client = MagicMock()
    monkeypatch.setattr(Config, "ENABLE_LLM_SYMPTOM_EXTRACTION", True)
    SymptomExtractionService.extract("fever", llm_client=llm_client)
    extractor_class.assert_called_once_with(llm_client, use_llm=True)


def test_symptom_service_correction_combines_inputs(monkeypatch):
    extract = MagicMock(return_value=SimpleNamespace())
    monkeypatch.setattr(SymptomExtractionService, "extract", extract)

    result = SymptomExtractionService.extract_with_correction(
        "headache", "also nauseous", llm_client="client"
    )

    assert result is extract.return_value
    combined = extract.call_args.args[0]
    assert "headache" in combined
    assert "also nauseous" in combined
    assert extract.call_args.args[1] == "client"


@pytest.mark.parametrize(
    ("order_result", "expected"),
    [
        ({"success": True, "task_ids": ["task-1"]}, True),
        ({"success": False}, False),
        (None, False),
    ],
)
def test_record_transaction_outbound(monkeypatch, order_result, expected):
    client = MagicMock()
    client.create_order.return_value = order_result
    monkeypatch.setattr(inventory, "PharmacyHTTPClient", lambda: client)

    payload = json.loads(inventory.record_transaction(3, 2, "out", "rx"))

    assert payload["success"] is expected
    client.create_order.assert_called_once_with([{"id": 3, "num": 2}])


def test_record_transaction_inbound_and_exception(monkeypatch):
    inbound = json.loads(inventory.record_transaction(3, 5, "in"))
    assert inbound["success"] is True
    assert inbound["type"] == "in"

    client = MagicMock()
    client.create_order.side_effect = RuntimeError("offline")
    monkeypatch.setattr(inventory, "PharmacyHTTPClient", lambda: client)
    failed = json.loads(inventory.record_transaction(3, 1, "out"))
    assert failed["success"] is False
    assert failed["error"] == "offline"


def test_stock_report_uses_backend_data(monkeypatch):
    drugs = [
        {"drug_id": 1, "name": "A", "quantity": 20, "expiry_date": 5, "shelve_id": 2},
        {"drug_id": 2, "name": "B", "quantity": 80, "expiry_date": 0, "shelve_id": 3},
    ]
    monkeypatch.setattr(inventory, "get_all_drugs", lambda: drugs)

    payload = json.loads(
        inventory.get_stock_report("2026-01-01", "2026-01-31", limit=1)
    )

    assert payload["total_drugs"] == 2
    assert payload["current_stock_summary"]["total_quantity"] == 100
    assert payload["current_stock_summary"]["expired_count"] == 1
    assert len(payload["drugs"]) == 1


def test_stock_report_falls_back_when_backend_fails(monkeypatch):
    monkeypatch.setattr(
        inventory, "get_all_drugs", MagicMock(side_effect=RuntimeError("offline"))
    )

    payload = json.loads(inventory.get_stock_report(limit=1))

    assert payload["total_drugs"] == 1
    assert payload["total_transactions"] == payload["stock_changes"][0]["transactions"]
    assert "offline" in payload["note"]


def test_inventory_placeholder_outputs_are_structured_json():
    suggestions = json.loads(inventory.generate_purchase_suggestions())
    assert suggestions["total_suggestions"] == len(suggestions["suggestions"])
    assert inventory.inventory_health_check()["module"] == "inventory"


def test_report_generators_accept_explicit_periods():
    daily = json.loads(report_generator.generate_daily_report("2026-06-01"))
    weekly = json.loads(report_generator.generate_weekly_report("2026-06-01"))
    monthly = json.loads(report_generator.generate_monthly_report(2026, 5))
    custom = json.loads(
        report_generator.generate_custom_report("inventory", {"threshold": 10})
    )

    assert daily["report_date"] == "2026-06-01"
    assert weekly["report_period"]["week_start"] == "2026-06-01"
    assert monthly["report_period"] == {
        "year": 2026,
        "month": 5,
        "month_name": monthly["report_period"]["month_name"],
        "days_in_month": 30,
    }
    assert custom["parameters"] == {"threshold": 10}
    assert report_generator.report_system_health_check()["module"] == "report_generator"

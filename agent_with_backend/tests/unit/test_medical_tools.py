"""测试药品查询、过敏检查、剂量建议、审批提交和处方执行工具。"""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from agent.tools import medical


def test_query_drug_formats_single_and_multi_term_results(monkeypatch):
    from database import pharmacy_client

    monkeypatch.setattr(
        pharmacy_client,
        "get_drugs_by_symptom_or_name",
        lambda query: [
            {
                "drug_id": 1,
                "name": "Aspirin",
                "quantity": 8,
                "retail_price": 12.5,
                "is_prescription": 1,
                "shelve_id": 2,
                "shelf_x": 3,
                "shelf_y": 4,
            }
        ],
    )
    single = json.loads(medical.query_drug("headache"))
    assert single["status"] == "success"
    assert single["drugs"][0]["stock"] == 8
    assert single["drugs"][0]["is_prescription"] is True

    def query_term(term):
        return [
            {"drug_id": 1, "name": "A"},
            {"drug_id": 2, "name": term},
        ]

    monkeypatch.setattr(pharmacy_client, "query_drugs_by_symptom", query_term)
    multiple = json.loads(medical.query_drug("headache fever"))
    assert multiple["count"] == 2
    assert {drug["name"] for drug in multiple["drugs"]} == {"A", "headache"}


def test_query_drug_not_found_and_error(monkeypatch):
    from database import pharmacy_client

    monkeypatch.setattr(
        pharmacy_client, "get_drugs_by_symptom_or_name", lambda query: []
    )
    assert json.loads(medical.query_drug("missing"))["status"] == "not_found"

    monkeypatch.setattr(
        pharmacy_client,
        "get_drugs_by_symptom_or_name",
        MagicMock(side_effect=RuntimeError("offline")),
    )
    failed = json.loads(medical.query_drug("missing"))
    assert failed["status"] == "error"
    assert "offline" in failed["message"]


def test_allergy_check_covers_match_and_no_match():
    allergen, related = next(iter(medical.ALLERGY_MAPPING.items()))
    matched = json.loads(medical.check_allergy(allergen, related[0]))
    clear = json.loads(medical.check_allergy("unrelated", "unknown"))

    assert matched["has_allergy"] is True
    assert matched["allergy_details"]
    assert clear["has_allergy"] is False


def test_dosage_and_advice_generation():
    child = json.loads(medical.calc_dosage("ibuprofen", 8, 20, "light"))
    adult = json.loads(medical.calc_dosage("unknown", 30, 70, "medium"))
    advice = json.loads(
        medical.generate_advice(
            "Aspirin", "one tablet", duration="3 days", notes="after meals"
        )
    )
    defaults = json.loads(medical.generate_advice("Aspirin", "one tablet"))

    assert child["estimated_quantity"] >= 1
    assert "150" in child["dosage"]
    assert "adult" not in adult["dosage"].lower()
    assert advice["structured_advice"]["duration"] == "3 days"
    assert defaults["duration"]
    assert defaults["notes"]


def test_submit_approval_success_empty_and_exception(monkeypatch):
    import database.approval_manager as approval_module

    manager = MagicMock()
    manager.create.return_value = "approval-1"
    monkeypatch.setattr(approval_module, "get_approval_manager", lambda: manager)
    submitted = json.loads(
        medical.submit_approval("Alice", "Take medicine", drug_name="A", quantity=2)
    )
    assert submitted["status"] == "submitted"
    assert submitted["approval_id"] == "approval-1"

    manager.create.return_value = None
    assert json.loads(medical.submit_approval("Alice", "Advice"))["status"] == "error"

    manager.create.side_effect = RuntimeError("db error")
    failed = json.loads(medical.submit_approval("Alice", "Advice"))
    assert failed["status"] == "error"
    assert "db error" in failed["message"]


def test_fill_prescription_real_api_and_fallback(monkeypatch):
    class FakeClient:
        def __init__(self, response=None, error=None, **kwargs):
            self.response = response
            self.error = error

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            if self.error:
                raise self.error
            return self.response

    ok_response = SimpleNamespace(
        status_code=200, json=lambda: {"pickup_code": "PICKUP-1"}
    )
    monkeypatch.setattr(
        medical.httpx, "AsyncClient", lambda **kwargs: FakeClient(ok_response)
    )
    real = json.loads(
        asyncio.run(medical.fill_prescription("rx-1", "Alice", [{"id": 1}]))
    )
    assert real["mode"] == "real_api"
    assert real["pickup_code"] == "PICKUP-1"

    monkeypatch.setattr(
        medical.httpx,
        "AsyncClient",
        lambda **kwargs: FakeClient(error=RuntimeError("offline")),
    )

    async def immediate_mock(prescription_id, patient_name, drugs):
        return {
            "success": True,
            "prescription_id": prescription_id,
            "patient_name": patient_name,
            "drugs_dispensed": drugs,
            "mode": "mock",
        }

    monkeypatch.setattr(medical, "_create_mock_response", immediate_mock)
    fallback = json.loads(
        asyncio.run(medical.fill_prescription("rx-2", "Bob", [{"id": 2}]))
    )
    assert fallback["mode"] == "mock"


def test_fill_prescription_sync_and_register_tools(monkeypatch):
    async def fake_fill(*args):
        return '{"success": true}'

    monkeypatch.setattr(medical, "fill_prescription", fake_fill)
    assert json.loads(medical.fill_prescription_sync("rx", "Alice", []))["success"]

    executor = MagicMock()
    medical.register_tools(executor)
    names = [call.args[0] for call in executor.register_handler.call_args_list]
    assert names == [
        "query_drug",
        "check_allergy",
        "calc_dosage",
        "generate_advice",
        "submit_approval",
        "fill_prescription",
    ]

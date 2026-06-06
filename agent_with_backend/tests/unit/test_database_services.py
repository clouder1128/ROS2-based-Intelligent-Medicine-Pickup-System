from unittest.mock import MagicMock

from database.approval_manager import ApprovalManager
from database import pharmacy_client


def test_approval_manager_full_state_transition(tmp_path):
    manager = ApprovalManager(str(tmp_path / "approvals.db"))

    approval_id = manager.create(
        "Alice",
        "Use one tablet",
        drug_name="Aspirin",
        quantity=2,
    )

    created = manager.get(approval_id)
    assert created["status"] == "pending"
    assert created["tracking_status"] == "waiting_approval"
    assert manager.list_pending(limit=0)[0]["id"] == approval_id

    assert manager.approve(approval_id, "doctor-1", notes="Approved") is True
    approved = manager.get(approval_id)
    assert approved["status"] == "approved"
    assert "[doctor] Approved" in approved["advice"]

    assert manager.set_task_id(approval_id, "task-1") is True
    assert manager.set_tracking_status(approval_id, "dispensing") is True
    assert manager.mark_completed(approval_id) is True

    completed = manager.get(approval_id)
    assert completed["status"] == "completed"
    assert completed["tracking_status"] == "completed"
    assert completed["task_id"] == "task-1"
    assert manager.mark_completed(approval_id) is False


def test_approval_manager_rejects_only_pending_requests(tmp_path):
    manager = ApprovalManager(str(tmp_path / "approvals.db"))
    approval_id = manager.create("Bob", "Do not dispense")

    assert manager.reject(approval_id, "doctor-2", "Contraindicated") is True
    rejected = manager.get(approval_id)
    assert rejected["status"] == "rejected"
    assert rejected["reject_reason"] == "Contraindicated"
    assert manager.approve(approval_id, "doctor-2") is False
    assert manager.reject("missing", "doctor-2", "none") is False


def test_pharmacy_client_query_fallbacks(monkeypatch):
    monkeypatch.setattr(pharmacy_client, "query_drugs_by_symptom", lambda query: [])
    monkeypatch.setattr(
        pharmacy_client, "search_drugs", lambda query: [{"drug_id": 1, "name": query}]
    )
    monkeypatch.setattr(
        pharmacy_client, "query_drug_by_name", lambda query: {"drug_id": 2}
    )

    assert pharmacy_client.get_drugs_by_symptom_or_name("aspirin") == [
        {"drug_id": 1, "name": "aspirin"}
    ]


def test_pharmacy_client_update_stock_routes_operations(monkeypatch):
    client = MagicMock()
    client.create_order.return_value = {"success": True}
    client.adjust_inventory.return_value = {"success": True}
    monkeypatch.setattr(pharmacy_client, "_get_client", lambda: client)

    assert pharmacy_client.update_stock(1, 2, "out") is True
    client.create_order.assert_called_once_with([{"id": 1, "num": 2}])

    assert pharmacy_client.update_stock(1, 5, "in") is True
    client.adjust_inventory.assert_called_once()
    assert pharmacy_client.update_stock(1, 1, "invalid") is False


def test_pharmacy_client_converts_transport_errors_to_safe_defaults(monkeypatch):
    client = MagicMock()
    client.get_drugs.side_effect = RuntimeError("offline")
    client.adjust_inventory.side_effect = RuntimeError("offline")
    monkeypatch.setattr(pharmacy_client, "_get_client", lambda: client)

    assert pharmacy_client.get_all_drugs() == []
    assert pharmacy_client.adjust_inventory(1, 2) is None

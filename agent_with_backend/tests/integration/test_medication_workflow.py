from __future__ import annotations

import pytest

from common.utils.database import get_db_connection
from tests.api_helpers import create_drug, json_body


def _quantity(drug_id: int) -> int:
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT quantity FROM inventory WHERE drug_id = ?", (drug_id,)
        ).fetchone()
        return int(row["quantity"])
    finally:
        conn.close()


def test_patient_approval_doctor_dispatch_and_completion(
    client,
    admin_token,
    doctor_headers,
    patient_headers,
    monkeypatch,
):
    published = []
    monkeypatch.setattr(
        "api.approval_controller.publish_task",
        lambda task_id, drug, quantity: published.append(
            (task_id, drug["drug_id"], quantity)
        ),
    )

    drug_id = create_drug(
        client,
        admin_token,
        name="审批流程布洛芬",
        quantity=10,
        indications=["头痛", "发热"],
    )
    approval = client.post(
        "/api/approvals",
        json={
            "patient_name": "张患者",
            "patient_age": 30,
            "symptoms": "头痛、发热",
            "advice": "每次一片，每日两次",
            "drug_name": "审批流程布洛芬",
            "drug_type": "解热镇痛药",
            "quantity": 2,
        },
        headers=patient_headers,
    )
    assert approval.status_code == 201
    approval_id = json_body(approval)["approval_id"]

    pending = client.get("/api/approvals/pending", headers=doctor_headers)
    assert pending.status_code == 200
    assert approval_id in {
        item["approval_id"] for item in json_body(pending)["approvals"]
    }

    approved = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"doctor_id": "doctor1", "notes": "审批通过"},
        headers=doctor_headers,
    )
    approved_data = json_body(approved)
    assert approved.status_code == 200
    assert approved_data["order_created"] is True
    assert _quantity(drug_id) == 8
    assert published == [(approved_data["task_id"], drug_id, 2)]

    detail = client.get(
        f"/api/approvals/{approval_id}", headers=patient_headers
    )
    detail_data = json_body(detail)["approval"]
    assert detail_data["status"] == "approved"
    assert detail_data["tracking_status"] == "pending_dispatch"
    assert int(detail_data["task_id"]) == approved_data["task_id"]

    completed = client.post(
        f"/api/approvals/{approval_id}/complete", headers=patient_headers
    )
    assert completed.status_code == 200

    final_detail = client.get(
        f"/api/approvals/{approval_id}", headers=patient_headers
    )
    assert json_body(final_detail)["approval"]["status"] == "completed"


def test_batch_order_is_atomic_when_any_item_is_invalid(
    client, admin_token, admin_headers, monkeypatch
):
    published = []
    monkeypatch.setattr(
        "api.order_controller.publish_task",
        lambda *args: published.append(args),
    )
    first_id = create_drug(
        client, admin_token, name="原子订单药A", quantity=10
    )
    second_id = create_drug(
        client, admin_token, name="原子订单药B", quantity=1
    )

    response = client.post(
        "/api/order",
        json=[
            {"id": first_id, "num": 3},
            {"id": second_id, "num": 2},
        ],
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert _quantity(first_id) == 10
    assert _quantity(second_id) == 1
    assert published == []

    conn = get_db_connection()
    try:
        assert conn.execute("SELECT COUNT(*) FROM order_log").fetchone()[0] == 0
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM inventory_transactions"
            ).fetchone()[0]
            == 0
        )
    finally:
        conn.close()


def test_direct_order_writes_inventory_audit_and_order_record(
    client, admin_token, admin_headers, monkeypatch
):
    published = []
    monkeypatch.setattr(
        "api.order_controller.publish_task",
        lambda task_id, drug, quantity: published.append(
            (task_id, drug["drug_id"], quantity)
        ),
    )
    drug_id = create_drug(
        client, admin_token, name="直接订单药", quantity=6
    )

    response = client.post(
        "/api/order",
        json=[{"id": drug_id, "num": 2}],
        headers=admin_headers,
    )
    data = json_body(response)
    assert response.status_code == 200
    assert _quantity(drug_id) == 4
    assert published == [(data["task_ids"][0], drug_id, 2)]

    conn = get_db_connection()
    try:
        order = conn.execute(
            "SELECT status, target_drug_id, quantity FROM order_log"
        ).fetchone()
        transaction = conn.execute(
            """
            SELECT quantity_change, transaction_type, before_quantity,
                   after_quantity, operator
            FROM inventory_transactions
            """
        ).fetchone()
        assert dict(order) == {
            "status": "pending",
            "target_drug_id": drug_id,
            "quantity": 2,
        }
        assert dict(transaction) == {
            "quantity_change": -2,
            "transaction_type": "out",
            "before_quantity": 6,
            "after_quantity": 4,
            "operator": "admin1",
        }
    finally:
        conn.close()


@pytest.mark.xfail(
    strict=True,
    reason="审批自动下单直接扣库存，未写 inventory_transactions 审计流水",
)
def test_approval_dispatch_writes_inventory_transaction(
    client, admin_token, doctor_headers, patient_headers, monkeypatch
):
    monkeypatch.setattr("api.approval_controller.publish_task", lambda *args: None)
    drug_id = create_drug(
        client, admin_token, name="审批审计药", quantity=5
    )
    approval = client.post(
        "/api/approvals",
        json={
            "patient_name": "张患者",
            "advice": "一次一片",
            "drug_name": "审批审计药",
            "quantity": 1,
        },
        headers=patient_headers,
    )
    approval_id = json_body(approval)["approval_id"]
    approved = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"doctor_id": "doctor1"},
        headers=doctor_headers,
    )
    assert approved.status_code == 200

    conn = get_db_connection()
    try:
        transaction = conn.execute(
            """
            SELECT quantity_change, transaction_type
            FROM inventory_transactions WHERE drug_id = ?
            """,
            (drug_id,),
        ).fetchone()
        assert transaction is not None
        assert transaction["quantity_change"] == -1
        assert transaction["transaction_type"] == "out"
    finally:
        conn.close()

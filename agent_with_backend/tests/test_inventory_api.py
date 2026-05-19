"""组件2 库存 API 测试：inventory 视图、调整流水、预警、统计。"""

from __future__ import annotations

import pytest

from common.utils.database import get_db_connection
from tests.api_helpers import (
    auth_headers,
    create_drug,
    create_test_app,
    init_test_db,
    json_body,
    login,
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "pharmacy.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-dummy")
    init_test_db(str(db_path))

    app = create_test_app()
    with app.test_client() as c:
        yield c


@pytest.fixture
def admin_token(client):
    return login(client, "admin1", "123456")


@pytest.fixture
def patient_token(client):
    return login(client, "patient1", "123456")


class TestInventoryAccess:
    def test_patient_forbidden_inventory(self, client, patient_token):
        resp = client.get(
            "/api/inventory",
            headers=auth_headers(patient_token),
        )
        assert resp.status_code == 403


class TestInventoryView:
    def test_inventory_projection_fields(self, client, admin_token):
        drug_id = create_drug(
            client,
            admin_token,
            name="库区视图药",
            quantity=25,
            expiry_date=20,
            min_stock_alert=30,
            shelf_x=3,
            shelf_y=4,
            shelve_id=2,
        )
        resp = client.get(
            "/api/inventory?name=库区视图药&expiring_window=30",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = json_body(resp)
        assert data["filters"]["view"] == "inventory"
        row = next(d for d in data["data"] if d["drug_id"] == drug_id)
        assert row["location_label"] == "Shelf 2, Position (3, 4)"
        assert row["needs_restock"] is True
        assert row["expiring_soon"] is True
        assert row["is_expired_stock"] is False
        assert "manufacturer" not in row


class TestAdjustInventory:
    def test_adjust_in_writes_transaction(self, client, admin_token):
        drug_id = create_drug(client, admin_token, name="调整库存药", quantity=10)
        resp = client.post(
            f"/api/drugs/{drug_id}/adjust",
            json={
                "quantity_change": 5,
                "transaction_type": "in",
                "reason": "pytest入库",
                "operator": "admin1",
            },
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        payload = json_body(resp)["data"]
        assert payload["quantity"] == 15
        assert payload["quantity_change"] == 5
        assert payload["transaction_id"] is not None

        conn = get_db_connection()
        try:
            tx = conn.execute(
                """
                SELECT quantity_change, transaction_type, before_quantity, after_quantity, reason
                FROM inventory_transactions
                WHERE transaction_id = ?
                """,
                (payload["transaction_id"],),
            ).fetchone()
            assert tx is not None
            assert tx["quantity_change"] == 5
            assert tx["transaction_type"] == "in"
            assert tx["before_quantity"] == 10
            assert tx["after_quantity"] == 15
            assert tx["reason"] == "pytest入库"
        finally:
            conn.close()

    def test_adjust_out_insufficient_stock(self, client, admin_token):
        drug_id = create_drug(client, admin_token, name="库存不足药", quantity=3)
        resp = client.post(
            f"/api/drugs/{drug_id}/adjust",
            json={"quantity_change": -10, "transaction_type": "out"},
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 400
        data = json_body(resp)
        assert data["error"]["code"] == "INVALID_ADJUST"


class TestInventoryAlerts:
    def test_low_stock_list(self, client, admin_token):
        create_drug(
            client,
            admin_token,
            name="低库存药",
            quantity=5,
            min_stock_alert=10,
        )
        create_drug(
            client,
            admin_token,
            name="正常库存药",
            quantity=100,
        )
        resp = client.get(
            "/api/drugs/low-stock?threshold=10",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = json_body(resp)
        names = {d["name"] for d in data["data"]}
        assert "低库存药" in names
        assert "正常库存药" not in names

    def test_low_stock_respects_min_stock_alert(self, client, admin_token):
        create_drug(
            client,
            admin_token,
            name="按阈值预警药",
            quantity=8,
            min_stock_alert=10,
        )
        resp = client.get(
            "/api/drugs/low-stock",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        names = {d["name"] for d in json_body(resp)["data"]}
        assert "按阈值预警药" in names

    def test_expiring_soon_list(self, client, admin_token):
        create_drug(
            client,
            admin_token,
            name="临期药",
            expiry_date=15,
        )
        create_drug(
            client,
            admin_token,
            name="远期药",
            expiry_date=200,
        )
        resp = client.get(
            "/api/drugs/expiring-soon?days=30",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        names = {d["name"] for d in json_body(resp)["data"]}
        assert "临期药" in names
        assert "远期药" not in names

    def test_drug_stats(self, client, admin_token):
        create_drug(
            client,
            admin_token,
            name="统计过期药",
            quantity=1,
            expiry_date=0,
        )
        create_drug(
            client,
            admin_token,
            name="统计低库存药",
            quantity=2,
        )
        resp = client.get(
            "/api/drugs/stats",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        stats = json_body(resp)["data"]
        assert stats["total_drugs"] >= 2
        assert stats["expired_count"] >= 1
        assert stats["low_stock_count"] >= 1

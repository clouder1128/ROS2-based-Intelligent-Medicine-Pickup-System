import pytest
from common.utils.database import get_db_connection

class TestDrugController:

    def test_create_drug(self, client):
        """UT-001-01 新增药品"""

        response = client.post(
            "/api/drugs",
            json={
                "name": "单元测试药品",
                "quantity": 100,
                "expiry_date": 365,
                "shelf_x": 1,
                "shelf_y": 1,
                "shelve_id": 1,
                "indications": ["发热"]
            }
        )

        assert response.status_code in [200, 201]

    def test_query_drug(self, client):
        """UT-001-04 查询药品"""

        response = client.get(
            "/api/drugs?name=单元测试药品"
        )

        assert response.status_code == 200

        data = response.get_json()

        assert data["success"] is True
        assert data["count"] >= 1

    def test_adjust_inventory(self, client):
        """UT-001-03 更新库存"""

        response = client.post(
            "/api/drugs/1/adjust",
            json={
                "quantity_change": 20,
                "transaction_type": "in"
            }
        )

        assert response.status_code == 200

        conn = get_db_connection()

        row = conn.execute(
            "SELECT quantity FROM inventory WHERE drug_id=1"
        ).fetchone()

        assert row["quantity"] >= 20

        conn.close()

    def test_low_stock(self, client):
        """UT-001-05 库存不足检查"""

        response = client.get(
            "/api/drugs/low-stock"
        )

        assert response.status_code == 200

        data = response.get_json()

        assert data["success"] is True

    def test_expiring_soon(self, client):
        """UT-001-06 过期药品检测"""

        response = client.get(
            "/api/drugs/expiring-soon"
        )

        assert response.status_code == 200

        data = response.get_json()

        assert data["success"] is True

    def test_delete_drug(self, client):
        """UT-001-02 删除药品"""

        response = client.delete(
            "/api/drugs/1"
        )

        assert response.status_code == 200

        conn = get_db_connection()

        row = conn.execute(
            "SELECT is_deleted FROM inventory WHERE drug_id=1"
        ).fetchone()

        assert row["is_deleted"] == 1

        conn.close()
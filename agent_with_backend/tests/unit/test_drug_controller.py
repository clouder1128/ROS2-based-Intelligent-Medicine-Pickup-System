"""测试药品控制器的新增、删除、查询、库存调整和临期预警接口。"""

from tests.api_helpers import auth_headers, create_drug, drug_payload, json_body


class TestDrugController:
    """按药品管理业务场景组织控制器接口测试。"""

    def test_create_drug(self, client, admin_token):
        """UT-001-01 新增药品"""

        resp = client.post(
            "/api/drugs",
            json=drug_payload(name="单元测试药品"),
            headers=auth_headers(admin_token),
        )

        assert resp.status_code == 201
        data = json_body(resp)
        assert data["success"] is True
        assert "drug_id" in data["data"]

    def test_delete_drug(self, client, admin_token):
        """UT-001-02 删除药品"""

        drug_id = create_drug(client, admin_token, name="待删药品")

        resp = client.delete(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(admin_token),
        )

        assert resp.status_code == 200

        detail = client.get(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(admin_token),
        )
        assert detail.status_code == 404

    def test_adjust_inventory(self, client, admin_token):
        """UT-001-03 更新库存"""

        drug_id = create_drug(client, admin_token, quantity=50)

        resp = client.post(
            f"/api/drugs/{drug_id}/adjust",
            json={"quantity_change": 20, "transaction_type": "in"},
            headers=auth_headers(admin_token),
        )

        assert resp.status_code == 200

        detail = client.get(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(admin_token),
        )
        assert json_body(detail)["data"]["quantity"] == 70

    def test_query_drug(self, client, admin_token):
        """UT-001-04 查询药品"""

        create_drug(client, admin_token, name="单元测试药品")

        resp = client.get(
            "/api/drugs?name=单元测试药品",
            headers=auth_headers(admin_token),
        )

        assert resp.status_code == 200
        data = json_body(resp)
        assert data["success"] is True
        assert data["count"] >= 1

    def test_low_stock(self, client, admin_token):
        """UT-001-05 库存不足检查"""

        create_drug(
            client,
            admin_token,
            name="低库存药",
            quantity=5,
            min_stock_alert=10,
        )

        resp = client.get(
            "/api/drugs/low-stock?threshold=10",
            headers=auth_headers(admin_token),
        )

        assert resp.status_code == 200
        data = json_body(resp)
        assert data["success"] is True
        names = [d["name"] for d in data["data"]]
        assert "低库存药" in names

    def test_expiring_soon(self, client, admin_token):
        """UT-001-06 过期药品检测"""

        create_drug(client, admin_token, name="临期药", expiry_date=15)

        resp = client.get(
            "/api/drugs/expiring-soon?days=30",
            headers=auth_headers(admin_token),
        )

        assert resp.status_code == 200
        data = json_body(resp)
        assert data["success"] is True
        names = [d["name"] for d in data["data"]]
        assert "临期药" in names

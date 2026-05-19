"""组件2 药品 API 测试：CRUD、搜索、批量导入、导出、分类。"""

from __future__ import annotations

import pytest

from tests.api_helpers import (
    auth_headers,
    create_drug,
    create_test_app,
    drug_payload,
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


class TestDrugAuth:
    def test_list_drugs_requires_token(self, client):
        resp = client.get("/api/drugs")
        assert resp.status_code == 401

    def test_patient_cannot_delete_drug(self, client, admin_token, patient_token):
        drug_id = create_drug(client, admin_token, name="待删药品")
        resp = client.delete(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(patient_token),
        )
        assert resp.status_code == 403


class TestDrugCrud:
    def test_create_validation_error(self, client, admin_token):
        resp = client.post(
            "/api/drugs",
            json={"name": "缺字段"},
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 400
        data = json_body(resp)
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_create_get_update_delete(self, client, admin_token):
        resp = client.post(
            "/api/drugs",
            json=drug_payload(name="全流程药", retail_price=9.9),
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 201
        drug_id = json_body(resp)["data"]["drug_id"]

        resp = client.get(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        detail = json_body(resp)["data"]
        assert detail["name"] == "全流程药"
        assert detail["indications"] == ["测试适应症"]

        resp = client.put(
            f"/api/drugs/{drug_id}",
            json={"retail_price": 12.0, "indications": ["更新适应症"]},
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(admin_token),
        )
        updated = json_body(resp)["data"]
        assert updated["retail_price"] == 12.0
        assert updated["indications"] == ["更新适应症"]

        resp = client.delete(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200

        resp = client.get(
            f"/api/drugs/{drug_id}",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 404


class TestDrugListAndSearch:
    def test_list_with_pagination_and_symptom(self, client, admin_token):
        create_drug(
            client,
            admin_token,
            name="布洛芬测试",
            indications=["头痛", "发热"],
        )
        resp = client.get(
            "/api/drugs?symptom=头痛&page=1&limit=10&sort_by=name&order=asc",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = json_body(resp)
        assert data["success"] is True
        assert data["pagination"]["page"] == 1
        assert any(d["name"] == "布洛芬测试" for d in data["data"])

    def test_search_by_keyword(self, client, admin_token):
        create_drug(client, admin_token, name="独特搜索药XYZ")
        resp = client.get(
            "/api/drugs/search?keyword=独特搜索&page=1&limit=5",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = json_body(resp)
        assert data["filters"]["keyword"] == "独特搜索"
        assert any("独特搜索药XYZ" in d["name"] for d in data["data"])

    def test_search_without_keyword_like_list(self, client, admin_token):
        create_drug(client, admin_token, name="列表等价药")
        resp = client.get(
            "/api/drugs/search",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = json_body(resp)
        assert "filters" in data
        assert any(d["name"] == "列表等价药" for d in data["data"])


class TestDrugBatchAndExport:
    def test_batch_import(self, client, admin_token):
        items = [
            drug_payload(name="批量A"),
            drug_payload(name="批量B", quantity=20),
        ]
        resp = client.post(
            "/api/drugs/batch-import",
            json=items,
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 201
        data = json_body(resp)
        assert data["data"]["count"] == 2
        assert len(data["data"]["drug_ids"]) == 2

    def test_batch_import_validation_stops_all(self, client, admin_token):
        items = [drug_payload(name="合法"), {"name": "非法缺字段"}]
        resp = client.post(
            "/api/drugs/batch-import",
            json=items,
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 400

    def test_export_json(self, client, admin_token):
        create_drug(client, admin_token, name="导出JSON药")
        resp = client.get(
            "/api/drugs/export?format=json",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        data = json_body(resp)
        drugs = data["data"]["drugs"]
        assert data["data"]["count"] >= 1
        assert any(d["name"] == "导出JSON药" for d in drugs)

    def test_export_csv(self, client, admin_token):
        create_drug(client, admin_token, name="导出CSV药")
        resp = client.get(
            "/api/drugs/export?format=csv",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type
        body = resp.get_data(as_text=True)
        assert body.startswith("\ufeff") or "drug_id" in body
        assert "导出CSV药" in body


class TestCategories:
    def test_list_and_create_category(self, client, admin_token):
        resp = client.get(
            "/api/categories",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        assert json_body(resp)["success"] is True

        resp = client.post(
            "/api/categories",
            json={"name": "测试分类", "description": "pytest"},
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 201
        created = json_body(resp)["data"]
        assert created["name"] == "测试分类"

        resp = client.post(
            "/api/categories",
            json={"name": "测试分类"},
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 409

    def test_category_tree(self, client, admin_token):
        parent = client.post(
            "/api/categories",
            json={"name": "父分类"},
            headers=auth_headers(admin_token),
        )
        parent_id = json_body(parent)["data"]["id"]
        client.post(
            "/api/categories",
            json={"name": "子分类", "parent_id": parent_id},
            headers=auth_headers(admin_token),
        )
        resp = client.get(
            "/api/categories?tree=1",
            headers=auth_headers(admin_token),
        )
        assert resp.status_code == 200
        tree = json_body(resp)["data"]
        roots = [n for n in tree if n["name"] == "父分类"]
        assert roots
        assert any(c["name"] == "子分类" for c in roots[0].get("children", []))

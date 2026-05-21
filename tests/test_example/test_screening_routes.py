# 筛选路由集成测试
# 通过 Flask 测试客户端验证筛选系统 API 接口的标准化、同义词查询、筛选查询和批量查询行为。

from flask import Flask

from screening.routes.screening_routes import create_screening_blueprint


def create_test_app():
    app = Flask(__name__)
    app.register_blueprint(create_screening_blueprint())
    app.config["TESTING"] = True
    return app


def test_standardize_symptoms_endpoint():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/api/screening/symptoms/standardize",
        json={"symptoms": ["头疼", "发热"]},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert "头痛" in payload["data"]["standardized_symptoms"]
    assert payload["data"]["unmatched"] == []


def test_get_symptom_synonyms_endpoint_requires_name():
    app = create_test_app()
    client = app.test_client()

    response = client.get("/api/screening/symptoms/synonyms")
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["success"] is False
    assert "症状名称不能为空" in payload["error"]


def test_screening_query_endpoint_returns_results():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/api/screening/query",
        json={
            "symptoms": ["头痛", "发热"],
            "patient_info": {"age": 30, "gender": "M", "allergies": []},
            "filters": {"max_results": 5, "price_range": [0, 20]},
        },
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["total_count"] >= 1
    assert isinstance(payload["results"], list)


def test_batch_screening_endpoint_requires_queries():
    app = create_test_app()
    client = app.test_client()

    response = client.post("/api/screening/batch", json={})
    payload = response.get_json()

    assert response.status_code == 400
    assert payload["success"] is False
    assert payload["error"] == "查询列表不能为空"

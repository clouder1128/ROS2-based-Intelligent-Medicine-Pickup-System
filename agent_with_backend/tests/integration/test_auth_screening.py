from __future__ import annotations

from tests.api_helpers import json_body


def test_auth_registration_refresh_logout_lifecycle(client):
    register = client.post(
        "/api/auth/register",
        json={
            "username": "integration_patient",
            "password": "secret123",
            "display_name": "集成测试患者",
            "email": "integration@example.test",
        },
    )
    assert register.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"username": "integration_patient", "password": "secret123"},
    )
    assert login.status_code == 200
    credentials = json_body(login)

    verify = client.post(
        "/api/auth/verify",
        headers={"Authorization": f"Bearer {credentials['access_token']}"},
    )
    assert verify.status_code == 200
    assert json_body(verify)["user"]["display_name"] == "集成测试患者"

    refreshed = client.post(
        "/api/auth/refresh",
        json={"refresh_token": credentials["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert json_body(refreshed)["access_token"]

    logout = client.post(
        "/api/auth/logout",
        json={"refresh_token": credentials["refresh_token"]},
        headers={"Authorization": f"Bearer {credentials['access_token']}"},
    )
    assert logout.status_code == 200

    revoked_refresh = client.post(
        "/api/auth/refresh",
        json={"refresh_token": credentials["refresh_token"]},
    )
    assert revoked_refresh.status_code == 401


def test_patient_screening_and_history_flow(client, patient_headers):
    profile = client.get("/api/auth/profile", headers=patient_headers)
    user_id = json_body(profile)["user"]["id"]

    standardized = client.post(
        "/api/screening/symptoms/standardize",
        json={"symptoms": ["头疼", "发烧", "未知症状"]},
        headers=patient_headers,
    )
    assert standardized.status_code == 200
    standard_data = json_body(standardized)["data"]
    assert set(standard_data["standardized_symptoms"]) == {"头痛", "发热"}
    assert standard_data["unmatched"] == ["未知症状"]

    screened = client.post(
        "/api/screening/query",
        json={
            "symptoms": standard_data["standardized_symptoms"],
            "patient_info": {"age": 30, "allergies": []},
            "filters": {"max_results": 3, "price_range": [0, 20]},
            "user_id": user_id,
            "request_id": "integration-screening-001",
        },
        headers=patient_headers,
    )
    assert screened.status_code == 200
    result = json_body(screened)
    assert result["success"] is True
    assert 1 <= result["total_count"] <= 3
    assert result["results"][0]["confidence_score"] >= result["results"][-1]["confidence_score"]

    history = client.get(
        f"/api/screening/history?user_id={user_id}",
        headers=patient_headers,
    )
    assert history.status_code == 200
    history_data = json_body(history)
    assert history_data["total"] == 1
    assert history_data["history"][0]["request_id"] == "integration-screening-001"


def test_role_permissions_span_drug_and_approval_apis(
    client, admin_headers, patient_headers
):
    inventory = client.get("/api/inventory", headers=patient_headers)
    assert inventory.status_code == 403

    created = client.post(
        "/api/approvals",
        json={"patient_name": "张患者", "advice": "观察并按医嘱用药"},
        headers=patient_headers,
    )
    assert created.status_code == 201
    approval_id = json_body(created)["approval_id"]

    forbidden = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"doctor_id": "patient1"},
        headers=patient_headers,
    )
    assert forbidden.status_code == 403

    audit = client.get("/api/audit/logs", headers=admin_headers)
    assert audit.status_code == 200
    actions = {row["action"] for row in json_body(audit)["logs"]}
    assert "login" in actions

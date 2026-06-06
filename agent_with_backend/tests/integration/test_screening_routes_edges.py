from tests.api_helpers import json_body


def test_screening_symptom_batch_config_and_status_edges(
    client, patient_headers, admin_headers
):
    empty = client.post(
        "/api/screening/symptoms/standardize",
        json={"symptoms": []},
        headers=patient_headers,
    )
    assert empty.status_code == 400

    missing_synonym = client.get(
        "/api/screening/symptoms/synonyms", headers=patient_headers
    )
    assert missing_synonym.status_code == 400
    synonyms = client.get(
        "/api/screening/symptoms/synonyms",
        query_string={"symptom_name": "头痛"},
        headers=patient_headers,
    )
    assert synonyms.status_code == 200
    assert json_body(synonyms)["data"]["symptom_name"] == "头痛"

    empty_batch = client.post(
        "/api/screening/batch",
        json={"queries": []},
        headers=patient_headers,
    )
    assert empty_batch.status_code == 400
    batch = client.post(
        "/api/screening/batch",
        json={
            "batch_id": "batch-1",
            "queries": [{"symptoms": ["头痛"]}, {"symptoms": []}],
        },
        headers=patient_headers,
    )
    assert batch.status_code == 200
    assert json_body(batch)["data"]["total_queries"] == 2

    default_config = client.get(
        "/api/screening/config", headers=patient_headers
    )
    assert default_config.status_code == 200
    missing_config = client.get(
        "/api/screening/config",
        query_string={"config_name": "missing"},
        headers=patient_headers,
    )
    assert missing_config.status_code == 404

    invalid_update = client.put(
        "/api/screening/config",
        json={"config_name": "default", "confidence_threshold": 2},
        headers=admin_headers,
    )
    assert invalid_update.status_code == 400
    valid_update = client.put(
        "/api/screening/config",
        json={"config_name": "default", "confidence_threshold": 0.7},
        headers=admin_headers,
    )
    assert valid_update.status_code == 200
    assert json_body(valid_update)["config"]["confidence_threshold"] == 0.7

    status = client.get("/api/screening/status", headers=patient_headers)
    assert status.status_code == 200
    assert json_body(status)["success"] is True


def test_screening_history_validation_and_detail(client, patient_headers):
    missing_user = client.get(
        "/api/screening/history", headers=patient_headers
    )
    assert missing_user.status_code == 400

    invalid_date = client.get(
        "/api/screening/history",
        query_string={
            "user_id": 1,
            "start_date": "bad",
            "end_date": "also-bad",
        },
        headers=patient_headers,
    )
    assert invalid_date.status_code == 400

    valid_range = client.get(
        "/api/screening/history",
        query_string={
            "user_id": 1,
            "start_date": "2026-01-01T00:00:00",
            "end_date": "2026-12-31T23:59:59",
            "limit": 5,
            "offset": 0,
        },
        headers=patient_headers,
    )
    assert valid_range.status_code == 200

    missing_detail = client.get(
        "/api/screening/history/999", headers=patient_headers
    )
    assert missing_detail.status_code == 404


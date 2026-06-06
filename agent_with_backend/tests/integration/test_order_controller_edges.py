from common.utils.database import get_db_connection
from tests.api_helpers import create_drug, json_body


def test_order_and_pickup_validation_errors(client, admin_headers):
    assert client.options("/api/order").status_code == 204

    cases = [
        ("/api/order", None),
        ("/api/order", {}),
        ("/api/order", {"id": 1}),
        ("/api/order", {"id": "bad", "num": 1}),
        ("/api/order", {"id": 1, "num": 0}),
        ("/api/pickup", None),
        ("/api/pickup", {}),
        ("/api/pickup", {"id": 1}),
        ("/api/pickup", {"id": "bad", "num": 1}),
        ("/api/pickup", {"id": 1, "num": 0}),
    ]
    for path, payload in cases:
        response = client.post(path, json=payload, headers=admin_headers)
        assert response.status_code == 400


def test_pickup_list_complete_and_not_found(
    client, admin_token, admin_headers, monkeypatch
):
    published = []
    monkeypatch.setattr(
        "api.order_controller.publish_task",
        lambda task_id, drug, quantity: published.append((task_id, quantity)),
    )
    drug_id = create_drug(client, admin_token, name="Pickup Drug", quantity=5)

    pickup = client.post(
        "/api/pickup",
        json={"id": drug_id, "num": 2},
        headers=admin_headers,
    )
    assert pickup.status_code == 200
    task_id = json_body(pickup)["task_id"]
    assert published == [(task_id, 2)]

    listed = client.get(
        "/api/orders?page=bad&limit=999", headers=admin_headers
    )
    listed_data = json_body(listed)
    assert listed.status_code == 200
    assert listed_data["pagination"]["page"] == 1
    assert listed_data["pagination"]["limit"] == 100
    assert listed_data["data"][0]["task_id"] == task_id

    completed = client.post(
        f"/api/orders/{task_id}/complete", headers=admin_headers
    )
    assert completed.status_code == 200
    missing = client.post("/api/orders/99999/complete", headers=admin_headers)
    assert missing.status_code == 404


def test_dispense_validation_success_and_atomic_failure(
    client, admin_token, admin_headers, monkeypatch
):
    invalid_payloads = [
        {},
        {"prescription_id": "rx", "patient_name": "A"},
        {"prescription_id": "rx", "patient_name": "A", "drugs": "bad"},
        {
            "prescription_id": "rx",
            "patient_name": "A",
            "drugs": [{"quantity": 1}],
        },
        {
            "prescription_id": "rx",
            "patient_name": "A",
            "drugs": [{"name": "A", "quantity": 0}],
        },
        {
            "prescription_id": "rx",
            "patient_name": "A",
            "drugs": [{"name": "A", "quantity": "bad"}],
        },
        {
            "prescription_id": "rx",
            "patient_name": "A",
            "drugs": [{"name": "missing", "quantity": 1}],
        },
    ]
    for payload in invalid_payloads:
        response = client.post(
            "/api/dispense", json=payload, headers=admin_headers
        )
        assert response.status_code == 400

    published = []
    monkeypatch.setattr(
        "api.order_controller.publish_task",
        lambda task_id, drug, quantity: published.append((task_id, quantity)),
    )
    create_drug(client, admin_token, name="Dispense Drug", quantity=4)
    response = client.post(
        "/api/dispense",
        json={
            "prescription_id": "rx-1",
            "patient_name": "Alice",
            "drugs": [{"name": "Dispense Drug", "quantity": 2}],
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = json_body(response)
    assert data["mode"] == "real_api"
    assert published == [(data["task_ids"][0], 2)]


def test_create_order_for_drug_missing_and_insufficient(tmp_path, monkeypatch):
    from api.order_controller import create_order_for_drug
    from common.config import Config
    from common.utils.database import init_database

    monkeypatch.setattr(Config, "DATABASE_PATH", str(tmp_path / "orders.db"))
    init_database()
    conn = get_db_connection()
    try:
        missing, error = create_order_for_drug(
            conn, 99, 1, {"name": "Missing"}, publish_now=False
        )
        assert missing is None
        assert error

        conn.execute(
            """
            INSERT INTO inventory
            (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id)
            VALUES (1, 'Low', 1, 30, 1, 1, 1)
            """
        )
        insufficient, error = create_order_for_drug(
            conn,
            1,
            2,
            {"drug_id": 1, "name": "Low"},
            publish_now=False,
        )
        assert insufficient is None
        assert error
    finally:
        conn.close()


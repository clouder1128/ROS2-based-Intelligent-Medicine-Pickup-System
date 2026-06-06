from __future__ import annotations

import pytest

from ros_integration.state_store import RosStateStore
from tests.api_helpers import json_body


def test_ros_subscription_state_is_exposed_through_http(
    client, patient_headers
):
    store = RosStateStore()
    store.update_car(car_id=2, x=1.5, y=3.25, isrunning=1)
    store.update_task(task_id="TASK-101", task_state=1, car_id=2)
    store.update_cabinet(
        cabinet_id=3,
        medicine_list=[{"drug_id": 9, "quantity": 12}],
    )

    status = client.get("/api/ros/status", headers=patient_headers)
    data = json_body(status)["data"]
    assert status.status_code == 200
    assert data["car_count"] == 1
    assert data["active_tasks"] == 1

    task = client.get(
        "/api/ros/task-states/TASK-101", headers=patient_headers
    )
    assert task.status_code == 200
    assert json_body(task)["data"]["car_id"] == 2

    cabinets = client.get(
        "/api/ros/cabinet-states", headers=patient_headers
    )
    assert json_body(cabinets)["data"][0]["medicine_list"][0]["quantity"] == 12


@pytest.mark.xfail(
    strict=True,
    reason="Python 3.10 的 datetime.fromisoformat 不解析末尾 Z，最新 ROS 状态被误判为离线",
)
def test_recent_ros_state_reports_connected(client, patient_headers):
    RosStateStore().update_car(car_id=1, x=0.0, y=0.0, isrunning=1)
    status = client.get("/api/ros/status", headers=patient_headers)
    assert json_body(status)["data"]["connected"] is True


def test_ros_return_command_requires_inventory_permission(
    client, patient_headers, admin_headers, monkeypatch
):
    patient_response = client.post(
        "/api/ros/return-to-queue", headers=patient_headers
    )
    assert patient_response.status_code == 403

    calls = []
    monkeypatch.setattr(
        "ros_integration.bridge.publish_return_to_queue",
        lambda: calls.append("published"),
    )
    admin_response = client.post(
        "/api/ros/return-to-queue", headers=admin_headers
    )
    assert admin_response.status_code == 200
    assert calls == ["published"]

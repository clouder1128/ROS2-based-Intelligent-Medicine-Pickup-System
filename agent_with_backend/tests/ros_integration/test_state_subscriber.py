from types import SimpleNamespace
from unittest.mock import MagicMock

from ros_integration.state_store import RosStateStore
from ros_integration.state_subscriber import StateSubscriber


def make_subscriber():
    subscriber = object.__new__(StateSubscriber)
    subscriber._initialized = False
    subscriber._task_state_callback = None
    subscriber._car_state_callback = None
    subscriber._cabinet_state_callback = None
    subscriber._message_adapter = MagicMock()
    subscriber._error_handler = MagicMock()
    return subscriber


def test_callback_setters_start_and_state_updates(monkeypatch):
    subscriber = make_subscriber()
    task_callback = MagicMock()
    car_callback = MagicMock()
    cabinet_callback = MagicMock()
    subscriber.set_task_state_callback(task_callback)
    subscriber.set_car_state_callback(car_callback)
    subscriber.set_cabinet_state_callback(cabinet_callback)

    assert subscriber.start() is False
    subscriber._initialized = True
    assert subscriber.start() is True
    assert subscriber.is_initialized() is True

    subscriber._message_adapter.unity_to_backend.return_value = {"task_id": "1"}
    connection = MagicMock()
    monkeypatch.setattr(
        "ros_integration.state_subscriber.get_db_connection",
        lambda: connection,
    )
    subscriber._task_state_callback_wrapper(
        SimpleNamespace(taskid="1", task_state=2, car_id=3)
    )
    task_callback.assert_called_once_with({"task_id": "1"})
    connection.commit.assert_called_once()
    connection.close.assert_called_once()
    assert RosStateStore().get_task("1")["task_state"] == 2

    subscriber._car_state_callback_wrapper(
        SimpleNamespace(car_id=4, x=1.5, y=2.5, isrunning=1)
    )
    car_callback.assert_called_once()
    assert RosStateStore().get_all_cars()[0]["car_id"] == 4

    medicine = SimpleNamespace(row=1, column=2, count=3)
    subscriber._cabinet_state_callback_wrapper(
        SimpleNamespace(cabinet_id=5, medicine_list=[medicine])
    )
    cabinet_callback.assert_called_once()
    assert RosStateStore().get_all_cabinets()[0]["medicine_list"][0]["count"] == 3


def test_task_callback_error_is_reported():
    subscriber = make_subscriber()
    subscriber._task_state_callback = MagicMock(side_effect=RuntimeError("callback"))
    subscriber._message_adapter.unity_to_backend.return_value = {"task_id": "1"}
    subscriber._task_state_callback_wrapper(
        SimpleNamespace(taskid="1", task_state=0, car_id=0)
    )
    subscriber._error_handler.handle_publish_error.assert_called_once()


def test_user_callback_errors_are_swallowed():
    subscriber = make_subscriber()
    subscriber._car_state_callback = MagicMock(side_effect=RuntimeError("car"))
    subscriber._cabinet_state_callback = MagicMock(
        side_effect=RuntimeError("cabinet")
    )

    subscriber._car_state_callback_wrapper(SimpleNamespace())
    subscriber._cabinet_state_callback_wrapper(SimpleNamespace())


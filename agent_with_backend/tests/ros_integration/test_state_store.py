"""RosStateStore 内存状态存储单元测试

纯 Python 实现，不依赖任何 ROS2 外部模块，可直接测试。
"""

import time
import threading
from ros_integration.state_store import RosStateStore


class TestSingleton:
    def test_singleton_returns_same_instance(self):
        store1 = RosStateStore()
        store2 = RosStateStore()
        assert store1 is store2

    def test_singleton_initialized_once(self):
        store = RosStateStore()
        assert store._initialized is True

    def test_reset_singleton(self):
        RosStateStore._instance = None
        store1 = RosStateStore()
        RosStateStore._instance = None
        store2 = RosStateStore()
        assert store1 is not store2


class TestCarState:
    def test_update_and_get_car(self):
        store = RosStateStore()
        store.update_car(1, 10.5, 20.3, 1)
        cars = store.get_all_cars()
        assert len(cars) == 1
        assert cars[0]["car_id"] == 1
        assert cars[0]["x"] == 10.5
        assert cars[0]["y"] == 20.3
        assert cars[0]["isrunning"] == 1
        assert "updated_at" in cars[0]

    def test_update_multiple_cars(self):
        store = RosStateStore()
        store.update_car(1, 1.0, 2.0, 1)
        store.update_car(2, 3.0, 4.0, 0)
        cars = store.get_all_cars()
        assert len(cars) == 2

    def test_update_same_car_overwrites(self):
        store = RosStateStore()
        store.update_car(1, 1.0, 2.0, 1)
        store.update_car(1, 5.0, 6.0, 0)
        cars = store.get_all_cars()
        assert len(cars) == 1
        assert cars[0]["x"] == 5.0
        assert cars[0]["y"] == 6.0


class TestTaskState:
    def test_update_and_get_task(self):
        store = RosStateStore()
        store.update_task("task_001", 1, 42)
        tasks = store.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "task_001"
        assert tasks[0]["task_state"] == 1
        assert tasks[0]["car_id"] == 42

    def test_get_single_task(self):
        store = RosStateStore()
        store.update_task("task_001", 1, 42)
        task = store.get_task("task_001")
        assert task is not None
        assert task["task_id"] == "task_001"

    def test_get_nonexistent_task(self):
        store = RosStateStore()
        assert store.get_task("nonexistent") is None

    def test_update_multiple_tasks(self):
        store = RosStateStore()
        store.update_task("t1", 1, 1)
        store.update_task("t2", 2, 2)
        assert len(store.get_all_tasks()) == 2


class TestCabinetState:
    def test_update_and_get_cabinet(self):
        store = RosStateStore()
        medicine_list = [{"row": 1, "column": 2, "count": 3}]
        store.update_cabinet(1, medicine_list)
        cabinets = store.get_all_cabinets()
        assert len(cabinets) == 1
        assert cabinets[0]["cabinet_id"] == 1
        assert cabinets[0]["medicine_list"] == medicine_list

    def test_update_multiple_cabinets(self):
        store = RosStateStore()
        store.update_cabinet(1, [])
        store.update_cabinet(2, [{"row": 1, "column": 1, "count": 5}])
        assert len(store.get_all_cabinets()) == 2


class TestGetAll:
    def test_get_all_returns_all_states(self):
        store = RosStateStore()
        store.update_car(1, 0, 0, 1)
        store.update_task("t1", 1, 1)
        store.update_cabinet(1, [])
        all_states = store.get_all()
        assert "cars" in all_states
        assert "tasks" in all_states
        assert "cabinets" in all_states
        assert len(all_states["cars"]) == 1
        assert len(all_states["tasks"]) == 1
        assert len(all_states["cabinets"]) == 1


class TestIsConnected:
    def test_not_connected_when_empty(self):
        store = RosStateStore()
        assert store.is_connected() is False

    def test_connected_with_recent_update(self):
        store = RosStateStore()
        store.update_car(1, 0, 0, 1)
        assert store.is_connected() is True

    def test_connected_with_recent_task_update(self):
        store = RosStateStore()
        store.update_task("t1", 1, 1)
        assert store.is_connected() is True


class TestThreadSafety:
    def test_concurrent_updates(self):
        store = RosStateStore()
        errors = []

        def writer(thread_id):
            try:
                for i in range(50):
                    store.update_car(thread_id, float(i), float(i), 1)
                    store.update_task(f"t_{thread_id}_{i}", i, thread_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(tid,)) for tid in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0
        # at least some data was written
        assert len(store.get_all_cars()) > 0

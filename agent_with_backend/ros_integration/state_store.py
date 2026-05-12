"""
ROS2 状态存储器 - 内存存储
保存从 Unity 仿真订阅的最新状态，供 API 实时读取。
"""

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class RosStateStore:
    """ROS2 订阅状态内存存储（单例）"""

    _instance: Optional["RosStateStore"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "RosStateStore":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._data_lock = threading.Lock()
        self._car_states: Dict[int, Dict[str, Any]] = {}
        self._task_states: Dict[str, Dict[str, Any]] = {}
        self._cabinet_states: Dict[int, Dict[str, Any]] = {}
        self._initialized = True

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---- 小车状态 ----

    def update_car(self, car_id: int, x: float, y: float, isrunning: int) -> None:
        with self._data_lock:
            self._car_states[car_id] = {
                "car_id": car_id,
                "x": x,
                "y": y,
                "isrunning": isrunning,
                "updated_at": self._now_iso(),
            }

    def get_all_cars(self) -> List[Dict[str, Any]]:
        with self._data_lock:
            return list(self._car_states.values())

    # ---- 任务状态 ----

    def update_task(self, task_id: str, task_state: int, car_id: int) -> None:
        with self._data_lock:
            self._task_states[task_id] = {
                "task_id": task_id,
                "task_state": task_state,
                "car_id": car_id,
                "updated_at": self._now_iso(),
            }

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        with self._data_lock:
            return list(self._task_states.values())

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._data_lock:
            return self._task_states.get(task_id)

    # ---- 药柜状态 ----

    def update_cabinet(self, cabinet_id: int, medicine_list: list) -> None:
        with self._data_lock:
            self._cabinet_states[cabinet_id] = {
                "cabinet_id": cabinet_id,
                "medicine_list": medicine_list,
                "updated_at": self._now_iso(),
            }

    def get_all_cabinets(self) -> List[Dict[str, Any]]:
        with self._data_lock:
            return list(self._cabinet_states.values())

    # ---- 通用 ----

    def get_all(self) -> Dict[str, Any]:
        with self._data_lock:
            return {
                "cars": list(self._car_states.values()),
                "tasks": list(self._task_states.values()),
                "cabinets": list(self._cabinet_states.values()),
            }

    def is_connected(self) -> bool:
        """判断 ROS2 是否最近有数据更新（30 秒内）"""
        import time
        now = time.time()
        with self._data_lock:
            for states in (self._car_states, self._task_states):
                for s in states.values():
                    try:
                        t = datetime.fromisoformat(s["updated_at"])
                        if (now - t.timestamp()) < 30:
                            return True
                    except Exception:
                        continue
            return False

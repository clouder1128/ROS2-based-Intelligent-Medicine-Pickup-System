"""
消息格式适配器 - 处理新旧消息格式转换
关键映射: backend格式 <-> Unity task_msgs格式
"""

import threading
from typing import Dict, Any
from datetime import datetime

class MessageAdapter:
    """
    消息格式适配器（单例模式）
    负责backend数据格式与Unity ROS2消息格式之间的转换
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """初始化适配器"""
        if not hasattr(self, '_initialized') or not self._initialized:
            self._initialized = True

    def backend_to_unity(self, task_id: int, drug: Dict[str, Any], quantity: int):
        """
        将backend药品数据转换为Unity Task消息

        Args:
            task_id: 任务ID
            drug: backend药品字典，必须包含:
                - drug_id: 药品ID
                - name: 药品名称
                - shelve_id: 货架ID
                - shelf_x: X坐标（列）
                - shelf_y: Y坐标（行）
                - quantity: 库存数量
            quantity: 需要取药的数量

        Returns:
            task_msgs.msg.Task: Unity任务消息

        Raises:
            KeyError: 如果drug缺少必要字段
            ValueError: 如果quantity无效
        """
        # 先检查必要字段
        required_fields = ["shelve_id", "shelf_x", "shelf_y"]
        for field in required_fields:
            if field not in drug:
                raise KeyError(f"Missing required field: {field}")

        # 然后验证quantity
        if quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity}")

        if quantity > drug.get("quantity", 0):
            raise ValueError(f"Quantity {quantity} exceeds available stock {drug.get('quantity', 0)}")

        try:
            # 尝试导入task_msgs
            from task_msgs.msg import Task, CabinetOrder, MedicineData

            # 创建Task消息
            task_msg = Task()
            task_msg.task_id = str(task_id)
            task_msg.type = "0"  # pickup类型

            # 创建CabinetOrder
            cabinet = CabinetOrder()
            cabinet.cabinet_id = str(drug["shelve_id"])

            # 创建MedicineData
            medicine = MedicineData()
            # 关键映射: shelf_x -> column, shelf_y -> row
            medicine.column = int(drug["shelf_x"])
            medicine.row = int(drug["shelf_y"])
            medicine.count = int(quantity)

            cabinet.medicine_list = [medicine]
            task_msg.cabinets = [cabinet]

            return task_msg

        except ImportError as e:
            raise ImportError(f"Failed to import task_msgs: {e}. Make sure task_msgs is installed.")

    def expiry_to_unity(self, drug: Dict[str, Any], remove_quantity: int):
        """
        将过期药品数据转换为Unity清理任务消息

        Args:
            drug: backend药品字典，必须包含:
                - shelve_id: 货架ID
                - shelf_x: X坐标（列）
                - shelf_y: Y坐标（行）
            remove_quantity: 清理数量

        Returns:
            task_msgs.msg.Task: 过期清理任务消息

        Raises:
            KeyError: 如果drug缺少必要字段
        """
        # 检查必要字段
        required_fields = ["shelve_id", "shelf_x", "shelf_y"]
        for field in required_fields:
            if field not in drug:
                raise KeyError(f"Missing required field: {field}")

        try:
            from task_msgs.msg import Task, CabinetOrder, MedicineData

            task_msg = Task()
            task_msg.task_id = ""  # 过期清理任务无ID
            task_msg.type = "expiry_removal"

            cabinet = CabinetOrder()
            cabinet.cabinet_id = str(drug["shelve_id"])

            medicine = MedicineData()
            medicine.column = int(drug["shelf_x"])
            medicine.row = int(drug["shelf_y"])
            medicine.count = int(remove_quantity)

            cabinet.medicine_list = [medicine]
            task_msg.cabinets = [cabinet]

            return task_msg

        except ImportError as e:
            raise ImportError(f"Failed to import task_msgs: {e}")

    def unity_to_backend(self, task_state_msg):
        """
        将Unity状态消息转换为backend格式

        Args:
            task_state_msg: task_msgs.msg.TaskState消息

        Returns:
            dict: backend状态字典
        """
        backend_state = {
            "task_id": task_state_msg.taskid,
            "task_state": int(task_state_msg.task_state),
            "car_id": int(task_state_msg.car_id) if hasattr(task_state_msg, 'car_id') else None,
            "timestamp": datetime.now().isoformat()
        }
        return backend_state

    def validate_mapping(self, drug: Dict[str, Any]) -> bool:
        """
        验证行列映射是否正确

        Args:
            drug: backend药品字典

        Returns:
            bool: 映射是否有效
        """
        try:
            shelf_x = drug.get("shelf_x")
            shelf_y = drug.get("shelf_y")

            if shelf_x is None or shelf_y is None:
                return False

            # 验证坐标在合理范围内（假设货架最大10x10）
            if not (1 <= int(shelf_x) <= 10 and 1 <= int(shelf_y) <= 10):
                return False

            return True

        except (ValueError, TypeError):
            return False
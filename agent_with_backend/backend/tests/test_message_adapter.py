"""消息格式适配器测试"""

import pytest
from datetime import datetime
from backend.ros_integration.message_adapter import MessageAdapter

def test_backend_to_unity_conversion():
    """测试backend格式到Unity消息格式转换"""
    # 如果task_msgs不可用则跳过
    pytest.importorskip("task_msgs.msg")

    adapter = MessageAdapter()

    # 模拟backend药品数据
    backend_drug = {
        "drug_id": 1,
        "name": "布洛芬",
        "shelve_id": "A",
        "shelf_x": 2,
        "shelf_y": 3,
        "quantity": 5,
        "expiry_date": 30
    }

    task_msg = adapter.backend_to_unity(task_id=1001, drug=backend_drug, quantity=3)

    assert task_msg.task_id == "1001"
    assert task_msg.type == "0"  # pickup类型

    # 验证药柜信息
    assert len(task_msg.cabinets) == 1
    cabinet = task_msg.cabinets[0]
    assert cabinet.cabinet_id == "A"

    # 验证药品信息
    assert len(cabinet.medicine_list) == 1
    medicine = cabinet.medicine_list[0]
    assert medicine.row == 3  # shelf_y -> row
    assert medicine.column == 2  # shelf_x -> column
    assert medicine.count == 3

def test_backend_to_unity_multiple_quantities():
    """测试不同数量转换"""
    # 如果task_msgs不可用则跳过
    pytest.importorskip("task_msgs.msg")

    adapter = MessageAdapter()

    backend_drug = {
        "drug_id": 2,
        "name": "阿莫西林",
        "shelve_id": "B",
        "shelf_x": 5,
        "shelf_y": 1,
        "quantity": 10
    }

    # 测试数量小于库存
    task_msg = adapter.backend_to_unity(task_id=1002, drug=backend_drug, quantity=2)
    medicine = task_msg.cabinets[0].medicine_list[0]
    assert medicine.count == 2

    # 测试数量等于库存
    task_msg = adapter.backend_to_unity(task_id=1003, drug=backend_drug, quantity=10)
    medicine = task_msg.cabinets[0].medicine_list[0]
    assert medicine.count == 10

def test_backend_to_unity_invalid_input():
    """测试无效输入处理"""
    # 如果task_msgs不可用则跳过
    pytest.importorskip("task_msgs.msg")

    adapter = MessageAdapter()

    # 缺少必要字段
    invalid_drug = {"drug_id": 1, "name": "测试"}

    with pytest.raises(KeyError):
        adapter.backend_to_unity(task_id=1004, drug=invalid_drug, quantity=1)

def test_expiry_removal_conversion():
    """测试过期药品清理消息转换"""
    # 如果task_msgs不可用则跳过
    pytest.importorskip("task_msgs.msg")

    adapter = MessageAdapter()

    expired_drug = {
        "drug_id": 3,
        "name": "过期药品",
        "shelve_id": "C",
        "shelf_x": 4,
        "shelf_y": 6,
        "quantity": 8
    }

    task_msg = adapter.expiry_to_unity(drug=expired_drug, remove_quantity=8)

    assert task_msg.task_id is None or task_msg.task_id == ""
    assert task_msg.type == "expiry_removal"

    cabinet = task_msg.cabinets[0]
    assert cabinet.cabinet_id == "C"

    medicine = cabinet.medicine_list[0]
    assert medicine.row == 6
    assert medicine.column == 4
    assert medicine.count == 8

def test_unity_to_backend_conversion():
    """测试Unity状态消息到backend格式转换"""
    adapter = MessageAdapter()

    # 模拟TaskState消息（需导入task_msgs）
    try:
        from task_msgs.msg import TaskState

        task_state_msg = TaskState()
        task_state_msg.taskid = "1001"
        task_state_msg.task_state = 1  # 执行中
        task_state_msg.car_id = 3

        backend_state = adapter.unity_to_backend(task_state_msg)

        assert backend_state["task_id"] == "1001"
        assert backend_state["task_state"] == 1
        assert backend_state["car_id"] == 3
        assert "timestamp" in backend_state

    except ImportError:
        # task_msgs未安装时跳过
        pytest.skip("task_msgs not installed")

def test_message_adapter_singleton():
    """测试适配器单例模式"""
    adapter1 = MessageAdapter()
    adapter2 = MessageAdapter()

    # 应该返回同一个实例
    assert adapter1 is adapter2
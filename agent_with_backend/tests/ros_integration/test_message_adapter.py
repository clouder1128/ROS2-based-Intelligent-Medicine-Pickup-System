"""MessageAdapter 消息格式转换单元测试

注意：message_adapter.py 的方法使用懒导入（from task_msgs.msg import ... 在方法内部），
conftest.py 已通过 sys.modules 注入了 mock 模块，因此测试中方法调用应正常。
"""

import pytest
from ros_integration.message_adapter import MessageAdapter


class TestSingleton:
    def test_singleton(self):
        m1 = MessageAdapter()
        m2 = MessageAdapter()
        assert m1 is m2


class TestBackendToUnity:
    def test_valid_drug_returns_task_msg(self):
        adapter = MessageAdapter()
        drug = {"drug_id": 1, "name": "布洛芬", "shelve_id": 1, "shelf_x": 3, "shelf_y": 4, "quantity": 50}
        result = adapter.backend_to_unity(1001, drug, 2)
        # 应返回 mock 的 Task 对象
        assert result is not None
        assert result.task_id == "1001"
        assert result.type == "0"
        assert hasattr(result, "cabinets")

    def test_shelf_mapping(self):
        """验证 shelf_x -> column, shelf_y -> row 映射"""
        adapter = MessageAdapter()
        drug = {"drug_id": 1, "name": "药", "shelve_id": 2, "shelf_x": 5, "shelf_y": 7, "quantity": 30}
        result = adapter.backend_to_unity(1, drug, 1)
        cabinet = result.cabinets[0]
        assert cabinet.cabinet_id == "2"
        medicine = cabinet.medicine_list[0]
        assert medicine.column == 5
        assert medicine.row == 7
        assert medicine.count == 1

    def test_missing_shelve_id_raises_key_error(self):
        adapter = MessageAdapter()
        drug = {"drug_id": 1, "name": "药", "shelf_x": 1, "shelf_y": 2, "quantity": 10}
        with pytest.raises(KeyError):
            adapter.backend_to_unity(1, drug, 1)

    def test_missing_shelf_x_raises_key_error(self):
        adapter = MessageAdapter()
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_y": 2, "quantity": 10}
        with pytest.raises(KeyError):
            adapter.backend_to_unity(1, drug, 1)

    def test_invalid_quantity_zero_raises_value_error(self):
        adapter = MessageAdapter()
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 1, "shelf_y": 2, "quantity": 10}
        with pytest.raises(ValueError, match="Invalid quantity"):
            adapter.backend_to_unity(1, drug, 0)

    def test_quantity_exceeds_stock_raises_value_error(self):
        adapter = MessageAdapter()
        drug = {"drug_id": 1, "name": "药", "shelve_id": 1, "shelf_x": 1, "shelf_y": 2, "quantity": 10}
        with pytest.raises(ValueError, match="exceeds available stock"):
            adapter.backend_to_unity(1, drug, 20)


class TestExpiryToUnity:
    def test_expiry_removal_returns_task_msg(self):
        adapter = MessageAdapter()
        drug = {"drug_id": 1, "shelve_id": 1, "shelf_x": 2, "shelf_y": 3}
        result = adapter.expiry_to_unity(drug, 5)
        assert result is not None
        assert result.type == "expiry_removal"
        assert result.task_id == ""

    def test_expiry_missing_field_raises_key_error(self):
        adapter = MessageAdapter()
        with pytest.raises(KeyError):
            adapter.expiry_to_unity({"drug_id": 1}, 5)


class TestUnityToBackend:
    def test_converts_task_state(self):
        adapter = MessageAdapter()
        # 创建一个 mock TaskState 对象
        class MockTaskState:
            taskid = "task_001"
            task_state = 2
            car_id = 42

        msg = MockTaskState()
        result = adapter.unity_to_backend(msg)
        assert result["task_id"] == "task_001"
        assert result["task_state"] == 2
        assert result["car_id"] == 42
        assert "timestamp" in result

    def test_converts_without_car_id(self):
        adapter = MessageAdapter()
        class MockTaskStateNoCar:
            taskid = "task_002"
            task_state = 1

        msg = MockTaskStateNoCar()
        result = adapter.unity_to_backend(msg)
        assert result["car_id"] is None


class TestValidateMapping:
    def test_valid_mapping(self):
        adapter = MessageAdapter()
        assert adapter.validate_mapping({"shelf_x": 1, "shelf_y": 1}) is True
        assert adapter.validate_mapping({"shelf_x": 10, "shelf_y": 10}) is True
        assert adapter.validate_mapping({"shelf_x": 5, "shelf_y": 8}) is True

    def test_invalid_mapping_out_of_range(self):
        adapter = MessageAdapter()
        assert adapter.validate_mapping({"shelf_x": 0, "shelf_y": 1}) is False
        assert adapter.validate_mapping({"shelf_x": 11, "shelf_y": 1}) is False
        assert adapter.validate_mapping({"shelf_x": 1, "shelf_y": 0}) is False
        assert adapter.validate_mapping({"shelf_x": 1, "shelf_y": 11}) is False

    def test_invalid_mapping_missing_fields(self):
        adapter = MessageAdapter()
        assert adapter.validate_mapping({}) is False
        assert adapter.validate_mapping({"shelf_x": 1}) is False

    def test_invalid_mapping_non_numeric(self):
        adapter = MessageAdapter()
        assert adapter.validate_mapping({"shelf_x": "abc", "shelf_y": 1}) is False

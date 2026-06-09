"""测试药品、分类、订单和审批等领域模型的转换、状态与序列化逻辑。"""

from datetime import datetime, timedelta

from database.models.approval import Approval
from database.models.category import Category
from database.models.drug import Drug
from database.models.order import Order


def test_drug_from_dict_coerces_fields_and_round_trips():
    drug = Drug.from_dict(
        {
            "drug_id": "5",
            "name": "Aspirin",
            "quantity": "20",
            "expiry_date": "30",
            "shelf_x": "1",
            "shelf_y": 2,
            "shelve_id": "3",
            "retail_price": "12.5",
            "is_prescription": "yes",
            "indications": ["headache"],
        }
    )

    assert drug.drug_id == 5
    assert drug.quantity == 20
    assert drug.retail_price == 12.5
    assert drug.is_prescription is True
    assert drug.to_dict()["indications"] == ["headache"]
    assert drug.get_location() == "Shelf 3, Position (1, 2)"


def test_drug_stock_rules_cover_expired_deleted_and_available():
    available = Drug(1, "A", 10, 1, 0, 0, 1)
    expired = Drug(2, "B", 10, 0, 0, 0, 1)
    deleted = Drug(3, "C", 10, 1, 0, 0, 1, is_deleted=True)

    assert available.has_sufficient_stock(10) is True
    assert available.has_sufficient_stock(11) is False
    assert expired.is_expired() is True
    assert expired.has_sufficient_stock(1) is False
    assert deleted.has_sufficient_stock(1) is False


def test_category_from_dict_handles_optional_and_invalid_integers():
    category = Category.from_dict(
        {"id": "2", "name": "Pain relief", "parent_id": "bad", "sort_order": "4"}
    )

    assert category.id == 2
    assert category.parent_id is None
    assert category.to_dict()["sort_order"] == 4


def test_order_status_serialization_and_age():
    created_at = (datetime.now() - timedelta(seconds=2)).isoformat()
    order = Order.from_dict(
        {
            "task_id": 1,
            "status": "completed",
            "target_drug_id": 9,
            "quantity": 2,
            "created_at": created_at,
            "drug_name": "Aspirin",
        }
    )

    assert order.is_pending() is False
    assert order.is_completed() is True
    assert order.to_dict()["drug_name"] == "Aspirin"
    assert order.get_age_seconds() >= 1


def test_approval_status_optional_fields_and_age():
    approval = Approval.from_dict(
        {
            "id": "AP-1",
            "patient_name": "Alice",
            "advice": "Take after meals",
            "status": "approved",
            "created_at": (datetime.now() - timedelta(seconds=2)).isoformat(),
            "patient_age": 30,
            "drug_name": "Aspirin",
        }
    )

    data = approval.to_dict()
    assert approval.is_approved() is True
    assert approval.is_pending() is False
    assert approval.is_rejected() is False
    assert approval.get_approval_id() == "AP-1"
    assert data["patient_age"] == 30
    assert "reject_reason" not in data
    assert approval.get_age_seconds() >= 1

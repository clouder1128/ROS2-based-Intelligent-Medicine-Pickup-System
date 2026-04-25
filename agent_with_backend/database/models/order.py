"""
Order model representing the order_log table in the pharmacy database.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Order:
    """Order model representing a medication pickup order."""

    task_id: int
    status: str
    target_drug_id: int
    quantity: int
    created_at: str
    drug_name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        return cls(
            task_id=data.get("task_id"),
            status=data.get("status", "pending"),
            target_drug_id=data.get("target_drug_id"),
            quantity=data.get("quantity", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            drug_name=data.get("drug_name"),
        )

    def to_dict(self) -> dict:
        result = {
            "task_id": self.task_id,
            "status": self.status,
            "target_drug_id": self.target_drug_id,
            "quantity": self.quantity,
            "created_at": self.created_at,
        }
        if self.drug_name:
            result["drug_name"] = self.drug_name
        return result

    def is_pending(self) -> bool:
        return self.status == "pending"

    def is_completed(self) -> bool:
        return self.status == "completed"

    def get_created_datetime(self) -> datetime:
        try:
            return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now()

    def get_age_seconds(self) -> float:
        created_dt = self.get_created_datetime()
        return (datetime.now() - created_dt).total_seconds()

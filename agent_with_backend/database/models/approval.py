"""
Approval model representing the approvals table in the pharmacy database.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Approval:
    """Approval model representing a medication approval request."""

    id: str
    patient_name: str
    advice: str
    status: str
    created_at: str
    patient_age: Optional[int] = None
    patient_weight: Optional[float] = None
    symptoms: Optional[str] = None
    drug_name: Optional[str] = None
    drug_type: Optional[str] = None
    quantity: int = 1
    doctor_id: Optional[str] = None
    reject_reason: Optional[str] = None
    approved_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Approval":
        return cls(
            id=data.get("id"),
            patient_name=data.get("patient_name", ""),
            advice=data.get("advice", ""),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            patient_age=data.get("patient_age"),
            patient_weight=data.get("patient_weight"),
            symptoms=data.get("symptoms"),
            drug_name=data.get("drug_name"),
            drug_type=data.get("drug_type"),
            quantity=data.get("quantity", 1),
            doctor_id=data.get("doctor_id"),
            reject_reason=data.get("reject_reason"),
            approved_at=data.get("approved_at"),
        )

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "patient_name": self.patient_name,
            "advice": self.advice,
            "status": self.status,
            "created_at": self.created_at,
            "quantity": self.quantity,
        }
        optional_fields = [
            "patient_age", "patient_weight", "symptoms",
            "drug_name", "drug_type", "doctor_id",
            "reject_reason", "approved_at",
        ]
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                result[field] = value
        return result

    def is_pending(self) -> bool:
        return self.status == "pending"

    def is_approved(self) -> bool:
        return self.status == "approved"

    def is_rejected(self) -> bool:
        return self.status == "rejected"

    def get_created_datetime(self) -> datetime:
        try:
            return datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return datetime.now()

    def get_age_seconds(self) -> float:
        created_dt = self.get_created_datetime()
        return (datetime.now() - created_dt).total_seconds()

    def get_approval_id(self) -> str:
        return self.id

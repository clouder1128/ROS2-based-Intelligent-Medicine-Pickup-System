"""
Approval model representing the approvals table in the pharmacy database.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Approval:
    """Approval model representing a medication approval request."""

    # Primary fields from database
    id: str  # Format: AP-YYYYMMDD-XXXXXX
    patient_name: str
    advice: str
    status: str  # 'pending', 'approved', 'rejected'
    created_at: str  # ISO format timestamp

    # Optional patient information
    patient_age: Optional[int] = None
    patient_weight: Optional[float] = None
    symptoms: Optional[str] = None

    # Optional drug information
    drug_name: Optional[str] = None
    drug_type: Optional[str] = None
    quantity: int = 1

    # Approval/rejection information
    doctor_id: Optional[str] = None
    reject_reason: Optional[str] = None
    approved_at: Optional[str] = None  # ISO format timestamp

    @classmethod
    def from_dict(cls, data: dict) -> 'Approval':
        """Create an Approval instance from a dictionary."""
        return cls(
            id=data.get('id'),
            patient_name=data.get('patient_name', ''),
            advice=data.get('advice', ''),
            status=data.get('status', 'pending'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            patient_age=data.get('patient_age'),
            patient_weight=data.get('patient_weight'),
            symptoms=data.get('symptoms'),
            drug_name=data.get('drug_name'),
            drug_type=data.get('drug_type'),
            quantity=data.get('quantity', 1),
            doctor_id=data.get('doctor_id'),
            reject_reason=data.get('reject_reason'),
            approved_at=data.get('approved_at')
        )

    def to_dict(self) -> dict:
        """Convert Approval instance to dictionary."""
        result = {
            'id': self.id,
            'patient_name': self.patient_name,
            'advice': self.advice,
            'status': self.status,
            'created_at': self.created_at,
            'quantity': self.quantity
        }

        # Add optional fields if they exist
        optional_fields = [
            'patient_age', 'patient_weight', 'symptoms',
            'drug_name', 'drug_type', 'doctor_id',
            'reject_reason', 'approved_at'
        ]
        for field in optional_fields:
            value = getattr(self, field)
            if value is not None:
                result[field] = value

        return result

    def is_pending(self) -> bool:
        """Check if the approval is pending."""
        return self.status == 'pending'

    def is_approved(self) -> bool:
        """Check if the approval is approved."""
        return self.status == 'approved'

    def is_rejected(self) -> bool:
        """Check if the approval is rejected."""
        return self.status == 'rejected'

    def get_created_datetime(self) -> datetime:
        """Parse created_at string into datetime object."""
        try:
            # Try parsing ISO format
            return datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # Fallback to current time if parsing fails
            return datetime.now()

    def get_age_seconds(self) -> float:
        """Get the age of the approval in seconds."""
        created_dt = self.get_created_datetime()
        return (datetime.now() - created_dt).total_seconds()

    def get_approval_id(self) -> str:
        """Get the approval ID (alias for id property)."""
        return self.id
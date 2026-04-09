"""
Drug model representing the inventory table in the pharmacy database.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Drug:
    """Drug model representing a medication in inventory."""

    drug_id: int
    name: str
    quantity: int
    expiry_date: (
        int  # Days until expiration (0 = expired, negative = expired for X days)
    )
    shelf_x: int
    shelf_y: int
    shelve_id: int

    @classmethod
    def from_dict(cls, data: dict) -> "Drug":
        """Create a Drug instance from a dictionary."""
        return cls(
            drug_id=data.get("drug_id"),
            name=data.get("name", ""),
            quantity=data.get("quantity", 0),
            expiry_date=data.get("expiry_date", 0),
            shelf_x=data.get("shelf_x", 0),
            shelf_y=data.get("shelf_y", 0),
            shelve_id=data.get("shelve_id", 0),
        )

    def to_dict(self) -> dict:
        """Convert Drug instance to dictionary."""
        return {
            "drug_id": self.drug_id,
            "name": self.name,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date,
            "shelf_x": self.shelf_x,
            "shelf_y": self.shelf_y,
            "shelve_id": self.shelve_id,
        }

    def is_expired(self) -> bool:
        """Check if the drug is expired."""
        return self.expiry_date <= 0

    def has_sufficient_stock(self, required_quantity: int) -> bool:
        """Check if there's sufficient stock for the required quantity."""
        return not self.is_expired() and self.quantity >= required_quantity

    def get_location(self) -> str:
        """Get the shelf location as a string."""
        return f"Shelf {self.shelve_id}, Position ({self.shelf_x}, {self.shelf_y})"

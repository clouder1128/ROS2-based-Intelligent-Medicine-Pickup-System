"""
Drug model representing the inventory table in the pharmacy database.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Drug:
    """Drug model representing a medication in inventory."""

    drug_id: int
    name: str
    quantity: int
    expiry_date: int
    shelf_x: int
    shelf_y: int
    shelve_id: int
    category: str = ""
    is_prescription: bool = False
    retail_price: float = 0.0
    indications: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Drug":
        return cls(
            drug_id=data.get("drug_id"),
            name=data.get("name", ""),
            quantity=data.get("quantity", 0),
            expiry_date=data.get("expiry_date", 0),
            shelf_x=data.get("shelf_x", 0),
            shelf_y=data.get("shelf_y", 0),
            shelve_id=data.get("shelve_id", 0),
            category=data.get("category", ""),
            is_prescription=bool(data.get("is_prescription", False)),
            retail_price=float(data.get("retail_price", 0.0)),
            indications=data.get("indications", []),
        )

    def to_dict(self) -> dict:
        return {
            "drug_id": self.drug_id,
            "name": self.name,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date,
            "shelf_x": self.shelf_x,
            "shelf_y": self.shelf_y,
            "shelve_id": self.shelve_id,
            "category": self.category,
            "is_prescription": self.is_prescription,
            "retail_price": self.retail_price,
            "indications": self.indications,
        }

    def is_expired(self) -> bool:
        return self.expiry_date <= 0

    def has_sufficient_stock(self, required_quantity: int) -> bool:
        return not self.is_expired() and self.quantity >= required_quantity

    def get_location(self) -> str:
        return f"Shelf {self.shelve_id}, Position ({self.shelf_x}, {self.shelf_y})"

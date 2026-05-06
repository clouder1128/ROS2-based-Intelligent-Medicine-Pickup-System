"""
Drug model representing the inventory table in the pharmacy database.

indications 来自 drug_indications 关联表，非 inventory 列。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


def _str_field(data: dict, key: str, default: str = "") -> str:
    v = data.get(key, default)
    if v is None:
        return default
    return str(v)


def _int_field(data: dict, key: str, default: int = 0) -> int:
    v = data.get(key, default)
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _float_field(data: dict, key: str, default: float = 0.0) -> float:
    v = data.get(key, default)
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _bool_field(data: dict, key: str, default: bool = False) -> bool:
    v = data.get(key, default)
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y")
    return default


@dataclass
class Drug:
    """药品主数据 + 库存位点，映射 inventory 一行；适应症为关联数据。"""

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
    stock: int = 0

    generic_name: str = ""
    description: str = ""
    manufacturer: str = ""
    specification: str = ""
    dosage_form: str = ""
    unit: str = ""
    pack_size: str = ""
    approval_number: str = ""
    barcode: str = ""
    storage_condition: str = ""
    usage_dosage: str = ""
    contraindications: str = ""
    side_effects: str = ""
    interaction_warning: str = ""
    pregnancy_category: str = ""
    pediatric_caution: str = ""
    supplier: str = ""
    country_of_origin: str = ""
    cost_price: float = 0.0
    min_stock_alert: int = 0
    image_url: str = ""
    is_deleted: bool = False
    created_at: str = ""
    updated_at: str = ""

    indications: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Drug":
        drug_id_raw = data.get("drug_id")
        drug_id = int(drug_id_raw) if drug_id_raw is not None else 0
        return cls(
            drug_id=drug_id,
            name=_str_field(data, "name"),
            quantity=_int_field(data, "quantity"),
            expiry_date=_int_field(data, "expiry_date"),
            shelf_x=_int_field(data, "shelf_x"),
            shelf_y=_int_field(data, "shelf_y"),
            shelve_id=_int_field(data, "shelve_id"),
            category=_str_field(data, "category"),
            is_prescription=_bool_field(data, "is_prescription"),
            retail_price=_float_field(data, "retail_price"),
            stock=_int_field(data, "stock"),
            generic_name=_str_field(data, "generic_name"),
            description=_str_field(data, "description"),
            manufacturer=_str_field(data, "manufacturer"),
            specification=_str_field(data, "specification"),
            dosage_form=_str_field(data, "dosage_form"),
            unit=_str_field(data, "unit"),
            pack_size=_str_field(data, "pack_size"),
            approval_number=_str_field(data, "approval_number"),
            barcode=_str_field(data, "barcode"),
            storage_condition=_str_field(data, "storage_condition"),
            usage_dosage=_str_field(data, "usage_dosage"),
            contraindications=_str_field(data, "contraindications"),
            side_effects=_str_field(data, "side_effects"),
            interaction_warning=_str_field(data, "interaction_warning"),
            pregnancy_category=_str_field(data, "pregnancy_category"),
            pediatric_caution=_str_field(data, "pediatric_caution"),
            supplier=_str_field(data, "supplier"),
            country_of_origin=_str_field(data, "country_of_origin"),
            cost_price=_float_field(data, "cost_price"),
            min_stock_alert=_int_field(data, "min_stock_alert"),
            image_url=_str_field(data, "image_url"),
            is_deleted=_bool_field(data, "is_deleted"),
            created_at=_str_field(data, "created_at"),
            updated_at=_str_field(data, "updated_at"),
            indications=list(data.get("indications") or []),
        )

    def to_dict(self) -> dict:
        return {
            "drug_id": self.drug_id,
            "name": self.name,
            "generic_name": self.generic_name,
            "description": self.description,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date,
            "shelf_x": self.shelf_x,
            "shelf_y": self.shelf_y,
            "shelve_id": self.shelve_id,
            "category": self.category,
            "is_prescription": self.is_prescription,
            "retail_price": self.retail_price,
            "stock": self.stock,
            "manufacturer": self.manufacturer,
            "specification": self.specification,
            "dosage_form": self.dosage_form,
            "unit": self.unit,
            "pack_size": self.pack_size,
            "approval_number": self.approval_number,
            "barcode": self.barcode,
            "storage_condition": self.storage_condition,
            "usage_dosage": self.usage_dosage,
            "contraindications": self.contraindications,
            "side_effects": self.side_effects,
            "interaction_warning": self.interaction_warning,
            "pregnancy_category": self.pregnancy_category,
            "pediatric_caution": self.pediatric_caution,
            "supplier": self.supplier,
            "country_of_origin": self.country_of_origin,
            "cost_price": self.cost_price,
            "min_stock_alert": self.min_stock_alert,
            "image_url": self.image_url,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "indications": self.indications,
        }

    def is_expired(self) -> bool:
        return self.expiry_date <= 0

    def has_sufficient_stock(self, required_quantity: int) -> bool:
        if self.is_deleted:
            return False
        return not self.is_expired() and self.quantity >= required_quantity

    def get_location(self) -> str:
        return f"Shelf {self.shelve_id}, Position ({self.shelf_x}, {self.shelf_y})"

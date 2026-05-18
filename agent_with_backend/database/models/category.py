"""Category 映射 `categories` 表一行（与 inventory.category 通过 name 关联）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


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


def _optional_int_field(data: dict, key: str) -> Optional[int]:
    v = data.get(key)
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


@dataclass
class Category:
    id: int
    name: str
    description: str = ""
    parent_id: Optional[int] = None
    sort_order: int = 0
    created_at: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Category":
        return cls(
            id=_int_field(data, "id"),
            name=_str_field(data, "name"),
            description=_str_field(data, "description"),
            parent_id=_optional_int_field(data, "parent_id"),
            sort_order=_int_field(data, "sort_order"),
            created_at=_str_field(data, "created_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "sort_order": self.sort_order,
            "created_at": self.created_at,
        }

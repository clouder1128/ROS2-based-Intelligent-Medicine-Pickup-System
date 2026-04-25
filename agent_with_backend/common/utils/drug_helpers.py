"""
Drug Helper Functions
Shared utility functions for drug-related operations to avoid circular imports
"""

import re
from common.utils.database import get_db_connection


def query_drug(drug_id: int) -> dict | None:
    """Query a single drug by ID"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?",
            (drug_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"Database error in query_drug: {e}")
        return None
    finally:
        if conn:
            conn.close()


def validate_and_get_drug(drug_id: int, num: int) -> tuple[dict | None, str | None]:
    """Validate drug availability and return drug info"""
    drug = query_drug(drug_id)
    if not drug:
        return None, f"药品不存在: id={drug_id}"
    if drug["expiry_date"] is not None and drug["expiry_date"] <= 0:
        return None, f'药品已过期: {drug["name"]}'
    if drug["quantity"] < num:
        return None, f'库存不足: {drug["name"]} 库存 {drug["quantity"]}，需求 {num}'
    return drug, None


def find_drug_id_by_name(drug_name: str) -> int | None:
    """Find drug ID by name using multi-level matching strategy"""
    normalized = drug_name.strip()
    if not normalized:
        return None

    if len(normalized) > 100:
        print(f"Warning: Drug name too long: {normalized[:50]}...")
        return None

    if re.search(r'[;\\\'"`]', normalized):
        print(f"Warning: Suspicious characters in drug name: {normalized}")
        return None

    cleaned = re.sub(r"[\s\W_]+", "", normalized)

    conn = None
    try:
        conn = get_db_connection()
        # 1. Exact match
        cur = conn.execute(
            "SELECT drug_id FROM inventory WHERE name = ?", (normalized,)
        )
        row = cur.fetchone()
        if row:
            return row["drug_id"]

        # 2. Normalized match
        if cleaned and cleaned != normalized:
            cur = conn.execute("SELECT drug_id, name FROM inventory")
            rows = cur.fetchall()
            for r in rows:
                db_name = r["name"]
                db_cleaned = re.sub(r"[\s\W_]+", "", db_name)
                if cleaned == db_cleaned:
                    return r["drug_id"]

        # 3. Fuzzy match
        cur = conn.execute(
            "SELECT drug_id FROM inventory WHERE name LIKE ?", (f"%{normalized}%",)
        )
        row = cur.fetchone()
        return row["drug_id"] if row else None

    except Exception as e:
        print(f"Database error in find_drug_id_by_name: {e}")
        return None
    finally:
        if conn:
            conn.close()

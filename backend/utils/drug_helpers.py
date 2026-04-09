"""
Drug Helper Functions
Shared utility functions for drug-related operations to avoid circular imports
"""

import re
from .database import get_db_connection


def query_drug(drug_id: int) -> dict | None:
    """Query a single drug by ID

    Args:
        drug_id: Drug ID to query

    Returns:
        Drug dictionary or None if not found
    """
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
        # Log the error (in production, use proper logging)
        print(f"Database error in query_drug: {e}")
        return None
    finally:
        if conn:
            conn.close()


def validate_and_get_drug(drug_id: int, num: int) -> tuple[dict | None, str | None]:
    """Validate drug availability and return drug info

    Args:
        drug_id: Drug ID to validate
        num: Quantity required

    Returns:
        Tuple of (drug_dict, error_msg). error_msg is None if validation passes.
    """
    drug = query_drug(drug_id)
    if not drug:
        return None, f"药品不存在: id={drug_id}"
    if drug["expiry_date"] is not None and drug["expiry_date"] <= 0:
        return None, f'药品已过期: {drug["name"]}'
    if drug["quantity"] < num:
        return None, f'库存不足: {drug["name"]} 库存 {drug["quantity"]}，需求 {num}'
    return drug, None


def find_drug_id_by_name(drug_name: str) -> int | None:
    """Find drug ID by name using multi-level matching strategy

    Args:
        drug_name: Drug name to search for

    Returns:
        Drug ID or None if not found
    """
    # Normalize drug name: strip whitespace, convert to lowercase (Chinese unaffected)
    normalized = drug_name.strip()
    if not normalized:
        return None

    # Input validation: limit length and check for dangerous characters
    if len(normalized) > 100:
        # Log warning (in production, use proper logging)
        print(f"Warning: Drug name too long: {normalized[:50]}...")
        return None

    # Check for SQL injection attempts (conservative check)
    if re.search(r'[;\\\'"`]', normalized):
        # Log warning (in production, use proper logging)
        print(f"Warning: Suspicious characters in drug name: {normalized}")
        return None

    # Create cleaned version: remove all whitespace and punctuation
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

        # 2. Normalized match (if cleaned differs from original and is not empty)
        if cleaned and cleaned != normalized:
            # Get all drug names for client-side normalized matching
            cur = conn.execute("SELECT drug_id, name FROM inventory")
            rows = cur.fetchall()
            for r in rows:
                db_name = r["name"]
                db_cleaned = re.sub(r"[\s\W_]+", "", db_name)
                if cleaned == db_cleaned:
                    return r["drug_id"]

        # 3. Fuzzy match (fallback)
        cur = conn.execute(
            "SELECT drug_id FROM inventory WHERE name LIKE ?", (f"%{normalized}%",)
        )
        row = cur.fetchone()
        return row["drug_id"] if row else None

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in find_drug_id_by_name: {e}")
        return None
    finally:
        if conn:
            conn.close()

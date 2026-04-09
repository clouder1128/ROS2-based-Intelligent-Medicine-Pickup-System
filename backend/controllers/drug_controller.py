"""
Drug Controller
Handles drug inventory management and queries
"""

import re
from flask import Blueprint, jsonify, request
from utils.database import get_db_connection

# Create blueprint for drug routes
drug_bp = Blueprint('drug', __name__, url_prefix='/api')


def query_drug(drug_id: int) -> dict | None:
    """Query a single drug by ID

    Args:
        drug_id: Drug ID to query

    Returns:
        Drug dictionary or None if not found
    """
    conn = get_db_connection()
    try:
        cur = conn.execute(
            'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?',
            (drug_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
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
        return None, f'药品不存在: id={drug_id}'
    if drug['expiry_date'] is not None and drug['expiry_date'] <= 0:
        return None, f'药品已过期: {drug["name"]}'
    if drug['quantity'] < num:
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

    # Create cleaned version: remove all whitespace and punctuation
    cleaned = re.sub(r'[\s\W_]+', '', normalized)

    conn = get_db_connection()
    try:
        # 1. Exact match
        cur = conn.execute(
            'SELECT drug_id FROM inventory WHERE name = ?',
            (normalized,)
        )
        row = cur.fetchone()
        if row:
            return row['drug_id']

        # 2. Normalized match (if cleaned differs from original and is not empty)
        if cleaned and cleaned != normalized:
            # Get all drug names for client-side normalized matching
            cur = conn.execute('SELECT drug_id, name FROM inventory')
            rows = cur.fetchall()
            for r in rows:
                db_name = r['name']
                db_cleaned = re.sub(r'[\s\W_]+', '', db_name)
                if cleaned == db_cleaned:
                    return r['drug_id']

        # 3. Fuzzy match (fallback)
        cur = conn.execute(
            'SELECT drug_id FROM inventory WHERE name LIKE ?',
            (f'%{normalized}%',)
        )
        row = cur.fetchone()
        return row['drug_id'] if row else None

    finally:
        conn.close()


@drug_bp.route('/drugs', methods=['GET'])
def list_drugs():
    """Get list of drugs with optional name filtering

    Query parameters:
    - name: Optional partial name filter (case-sensitive)

    Returns:
    - New format: {"success": True, "drugs": [...], "count": N, "filters": {"name": <value>}}
    - Old format (backward compatibility): {"ok": True, "data": [...]}
    """
    name_filter = request.args.get('name')

    conn = get_db_connection()
    try:
        if name_filter is not None:
            # Use LIKE for partial matching
            cur = conn.execute(
                'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE name LIKE ?',
                (f'%{name_filter}%',)
            )
        else:
            cur = conn.execute(
                'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory'
            )

        drugs = [dict(row) for row in cur.fetchall()]

        # Return both new format for P1 compatibility and old format for backward compatibility
        response_data = {
            'success': True,  # New format
            'ok': True,       # Old format for backward compatibility
            'drugs': drugs,   # New format
            'data': drugs,    # Old format for backward compatibility
            'count': len(drugs),
            'filters': {'name': name_filter if name_filter is not None else ''}
        }
        return jsonify(response_data)
    finally:
        conn.close()


@drug_bp.route('/drugs/<int:drug_id>', methods=['GET'])
def get_drug(drug_id):
    """Get a single drug by ID

    Returns:
    - Success: {"success": True, "drug": {...}}
    - Not found: {"error": True, "message": "...", "code": "DRUG_NOT_FOUND"} with 404 status
    """
    conn = get_db_connection()
    try:
        cur = conn.execute(
            'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?',
            (drug_id,)
        )
        row = cur.fetchone()

        if row is None:
            return jsonify({
                'error': True,
                'message': f'Drug not found: id={drug_id}',
                'code': 'DRUG_NOT_FOUND'
            }), 404

        drug = dict(row)
        return jsonify({
            'success': True,
            'drug': drug
        })
    finally:
        conn.close()
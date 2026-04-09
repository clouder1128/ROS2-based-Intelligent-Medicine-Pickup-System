"""
Drug Controller
Handles drug inventory management and queries
"""

from flask import Blueprint, jsonify, request
from utils.database import get_db_connection

# Create blueprint for drug routes
drug_bp = Blueprint('drug', __name__, url_prefix='/api')


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

    # Validate name_filter if provided
    if name_filter is not None:
        # Limit length to prevent excessively long queries
        if len(name_filter) > 100:
            return jsonify({
                'success': False,
                'ok': False,
                'error': 'Name filter too long (max 100 characters)',
                'code': 'INVALID_INPUT'
            }), 400

        # Basic validation: allow alphanumeric, Chinese characters, spaces, and common punctuation
        # This is a conservative check to prevent SQL injection attempts
        import re
        if re.search(r'[;\\\'"`]', name_filter):
            return jsonify({
                'success': False,
                'ok': False,
                'error': 'Invalid characters in name filter',
                'code': 'INVALID_INPUT'
            }), 400

    conn = None
    try:
        conn = get_db_connection()
        if name_filter is not None:
            # Use LIKE for partial matching with parameterized query (safe)
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
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in list_drugs: {e}")
        return jsonify({
            'success': False,
            'ok': False,
            'error': 'Database error while fetching drugs',
            'code': 'DB_ERROR'
        }), 500
    finally:
        if conn:
            conn.close()


@drug_bp.route('/drugs/<int:drug_id>', methods=['GET'])
def get_drug(drug_id):
    """Get a single drug by ID

    Returns:
    - Success: {"success": True, "drug": {...}}
    - Not found: {"error": True, "message": "...", "code": "DRUG_NOT_FOUND"} with 404 status
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?',
            (drug_id,)
        )
        row = cur.fetchone()

        if row is None:
            return jsonify({
                'success': False,
                'ok': False,
                'error': f'Drug not found: id={drug_id}',
                'code': 'DRUG_NOT_FOUND'
            }), 404

        drug = dict(row)
        return jsonify({
            'success': True,
            'drug': drug
        })
    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Database error in get_drug: {e}")
        return jsonify({
            'success': False,
            'ok': False,
            'error': 'Database error while fetching drug',
            'code': 'DB_ERROR'
        }), 500
    finally:
        if conn:
            conn.close()
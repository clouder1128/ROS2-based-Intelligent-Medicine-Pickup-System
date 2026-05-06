"""
Drug Controller
Handles drug inventory management and queries
"""

import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from common.utils.database import get_db_connection

drug_bp = Blueprint("drug", __name__, url_prefix="/api")

# ORDER BY 仅允许白名单列，防止注入
_SORT_SQL = {
    "drug_id": "drug_id",
    "name": "name COLLATE NOCASE",
    "quantity": "quantity",
    "expiry_date": "expiry_date",
    "retail_price": "retail_price",
    "category": "category COLLATE NOCASE",
    "shelve_id": "shelve_id",
    "created_at": "created_at",
    "updated_at": "updated_at",
}

# PUT 允许更新的列（不含 drug_id、stock 按方案 A 不维护）
_UPDATABLE_COLUMNS = {
    "name", "generic_name", "description", "quantity", "expiry_date",
    "shelf_x", "shelf_y", "shelve_id", "category", "is_prescription",
    "retail_price", "manufacturer", "specification", "dosage_form", "unit",
    "pack_size", "approval_number", "barcode", "storage_condition",
    "usage_dosage", "contraindications", "side_effects", "interaction_warning",
    "pregnancy_category", "pediatric_caution", "supplier", "country_of_origin",
    "cost_price", "min_stock_alert", "image_url",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _error(message: str, code: str, status: int):
    return jsonify({"success": False, "ok": False, "error": message, "code": code}), status


def _fetch_drugs_with_indications(conn, where_clause: str, params: tuple):
    """SELECT * FROM inventory + 拼接 indications"""
    sql = f"SELECT * FROM inventory {where_clause}"
    cur = conn.execute(sql, params)
    drugs = [dict(row) for row in cur.fetchall()]

    drug_ids = [d["drug_id"] for d in drugs]
    if drug_ids:
        placeholders = ",".join("?" for _ in drug_ids)
        cur = conn.execute(
            f"SELECT drug_id, indication FROM drug_indications WHERE drug_id IN ({placeholders})",
            drug_ids,
        )
        indications_map = {}
        for row in cur.fetchall():
            di = row["drug_id"]
            indications_map.setdefault(di, []).append(row["indication"])
        for d in drugs:
            d["indications"] = indications_map.get(d["drug_id"], [])
    else:
        for d in drugs:
            d["indications"] = []

    return drugs


def _deduplicate_drugs(drugs):
    seen = set()
    result = []
    for d in drugs:
        if d["drug_id"] not in seen:
            seen.add(d["drug_id"])
            result.append(d)
    return result


def _parse_pagination():
    try:
        page = int(request.args.get("page", "1"))
    except (TypeError, ValueError):
        return None
    try:
        limit = int(request.args.get("limit", "20"))
    except (TypeError, ValueError):
        return None
    page = max(1, page)
    limit = min(100, max(1, limit))
    offset = (page - 1) * limit
    return page, limit, offset


def _pagination_dict(page: int, limit: int, total: int):
    pages = (total + limit - 1) // limit if limit else 0
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "has_next": page * limit < total,
        "has_prev": page > 1,
    }


@drug_bp.route("/drugs", methods=["GET"])
def list_drugs():
    name_filter = request.args.get("name")
    symptom_filter = request.args.get("symptom")
    category_filter = request.args.get("category")
    sort_by = request.args.get("sort_by") or "drug_id"
    sort_order = (request.args.get("order") or "asc").lower()
    if sort_order not in ("asc", "desc"):
        return _error("order must be asc or desc", "INVALID_INPUT", 400)
    if sort_by not in _SORT_SQL:
        return _error(
            f"sort_by must be one of: {', '.join(sorted(_SORT_SQL))}",
            "INVALID_INPUT",
            400,
        )

    # 未传 page/limit 时保持旧行为：返回全量列表（与 PharmacyHTTPClient 等调用方兼容）
    use_pagination = (
        request.args.get("page") is not None or request.args.get("limit") is not None
    )
    if use_pagination:
        paginated = _parse_pagination()
        if paginated is None:
            return _error("page and limit must be integers", "INVALID_INPUT", 400)
        page, limit, offset = paginated
    else:
        page, limit, offset = 1, 20, 0

    if name_filter is not None and len(name_filter) > 100:
        return _error("Name filter too long (max 100 characters)", "INVALID_INPUT", 400)
    if symptom_filter is not None and len(symptom_filter) > 100:
        return _error("Symptom filter too long (max 100 characters)", "INVALID_INPUT", 400)
    if category_filter is not None and len(category_filter) > 200:
        return _error("category filter too long", "INVALID_INPUT", 400)

    for f in [name_filter, symptom_filter, category_filter]:
        if f is not None and re.search(r'[;\\\'"`]', f):
            return _error("Invalid characters in filter", "INVALID_INPUT", 400)

    order_sql = f"ORDER BY {_SORT_SQL[sort_by]} {sort_order.upper()}"

    conn = None
    try:
        conn = get_db_connection()

        if symptom_filter is not None:
            base_where = (
                "WHERE drug_id IN (SELECT DISTINCT drug_id FROM drug_indications WHERE indication LIKE ?) "
                "AND quantity > 0 AND is_deleted = 0"
            )
            drugs = _fetch_drugs_with_indications(conn, base_where, (f"%{symptom_filter}%",))

            if not drugs:
                cur = conn.execute(
                    "SELECT DISTINCT standard_term FROM symptom_synonyms WHERE synonym LIKE ?",
                    (f"%{symptom_filter}%",),
                )
                standard_terms = [row["standard_term"] for row in cur.fetchall()]
                for term in standard_terms:
                    matched = _fetch_drugs_with_indications(
                        conn,
                        base_where,
                        (f"%{term}%",),
                    )
                    drugs.extend(matched)
                drugs = _deduplicate_drugs(drugs)

            if category_filter:
                drugs = [d for d in drugs if (d.get("category") or "") == category_filter]
            if name_filter:
                drugs = [d for d in drugs if name_filter.lower() in (d.get("name") or "").lower()]

            sort_col = sort_by if sort_by in _SORT_SQL else "drug_id"
            reverse = sort_order == "desc"
            if sort_col in ("name", "category"):
                drugs.sort(
                    key=lambda d: ((d.get(sort_col) or "").lower(), d["drug_id"]),
                    reverse=reverse,
                )
            else:
                drugs.sort(key=lambda d: d.get(sort_col, 0), reverse=reverse)

            total = len(drugs)
            if use_pagination:
                drugs = drugs[offset : offset + limit]

            out = {
                "success": True,
                "ok": True,
                "drugs": drugs,
                "data": drugs,
                "count": len(drugs),
                "filters": {
                    "symptom": symptom_filter,
                    "category": category_filter or "",
                    "name": name_filter or "",
                    "sort_by": sort_by,
                    "order": sort_order,
                },
            }
            if use_pagination:
                out["pagination"] = _pagination_dict(page, limit, total)
            return jsonify(out)

        where_parts = ["is_deleted = 0"]
        params: list = []

        if category_filter:
            where_parts.append("category = ?")
            params.append(category_filter)
        if name_filter:
            where_parts.append("name LIKE ?")
            params.append(f"%{name_filter}%")
        where_sql = "WHERE " + " AND ".join(where_parts)

        if use_pagination:
            cur = conn.execute(
                f"SELECT COUNT(*) FROM inventory {where_sql}",
                tuple(params),
            )
            total = cur.fetchone()[0]
        else:
            total = 0

        if use_pagination:
            list_sql = f"SELECT * FROM inventory {where_sql} {order_sql} LIMIT ? OFFSET ?"
            cur = conn.execute(list_sql, tuple(params) + (limit, offset))
        else:
            list_sql = f"SELECT * FROM inventory {where_sql} {order_sql}"
            cur = conn.execute(list_sql, tuple(params))
        drugs = [dict(row) for row in cur.fetchall()]
        drug_ids = [d["drug_id"] for d in drugs]
        if drug_ids:
            ph = ",".join("?" for _ in drug_ids)
            cur = conn.execute(
                f"SELECT drug_id, indication FROM drug_indications WHERE drug_id IN ({ph})",
                drug_ids,
            )
            imap = {}
            for row in cur.fetchall():
                imap.setdefault(row["drug_id"], []).append(row["indication"])
            for d in drugs:
                d["indications"] = imap.get(d["drug_id"], [])
        else:
            for d in drugs:
                d["indications"] = []

        out = {
            "success": True,
            "ok": True,
            "drugs": drugs,
            "data": drugs,
            "count": len(drugs),
            "filters": {
                "name": name_filter or "",
                "category": category_filter or "",
                "sort_by": sort_by,
                "order": sort_order,
            },
        }
        if use_pagination:
            out["pagination"] = _pagination_dict(page, limit, total)
        return jsonify(out)

    except Exception as e:
        print(f"Database error in list_drugs: {e}")
        return _error("Database error while fetching drugs", "DB_ERROR", 500)
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>", methods=["GET"])
def get_drug(drug_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT * FROM inventory WHERE drug_id = ?", (drug_id,))
        row = cur.fetchone()
        if row is None:
            return _error(f"Drug not found: id={drug_id}", "DRUG_NOT_FOUND", 404)
        drug = dict(row)
        if drug.get("is_deleted"):
            return _error(f"Drug not found: id={drug_id}", "DRUG_NOT_FOUND", 404)

        cur = conn.execute(
            "SELECT indication FROM drug_indications WHERE drug_id = ?", (drug_id,))
        drug["indications"] = [r["indication"] for r in cur.fetchall()]

        return jsonify({"success": True, "drug": drug})
    except Exception as e:
        print(f"Database error in get_drug: {e}")
        return _error("Database error while fetching drug", "DB_ERROR", 500)
    finally:
        if conn:
            conn.close()


def _next_drug_id(conn) -> int:
    row = conn.execute("SELECT COALESCE(MAX(drug_id), 0) + 1 FROM inventory").fetchone()
    return int(row[0])


def _replace_indications(conn, drug_id: int, indications):
    conn.execute("DELETE FROM drug_indications WHERE drug_id = ?", (drug_id,))
    if not indications:
        return
    for ind in indications:
        if not isinstance(ind, str) or not ind.strip():
            continue
        s = ind.strip()
        if len(s) > 500:
            continue
        conn.execute(
            "INSERT INTO drug_indications (drug_id, indication) VALUES (?, ?)",
            (drug_id, s),
        )


@drug_bp.route("/drugs", methods=["POST"])
def create_drug():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return _error("Request body must be a JSON object", "INVALID_JSON", 400)

    required = ["name", "quantity", "expiry_date", "shelf_x", "shelf_y", "shelve_id"]
    missing = [k for k in required if k not in data]
    if missing:
        return _error(f"Missing required fields: {', '.join(missing)}", "MISSING_FIELDS", 400)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return _error("name must be a non-empty string", "INVALID_INPUT", 400)
    name = name.strip()
    if len(name) > 500:
        return _error("name too long", "INVALID_INPUT", 400)

    try:
        quantity = int(data["quantity"])
        expiry_date = int(data["expiry_date"])
        shelf_x = int(data["shelf_x"])
        shelf_y = int(data["shelf_y"])
        shelve_id = int(data["shelve_id"])
    except (TypeError, ValueError):
        return _error("quantity, expiry_date, shelf_*, shelve_id must be integers", "INVALID_TYPE", 400)

    if quantity < 0:
        return _error("quantity must be >= 0", "INVALID_INPUT", 400)

    indications = data.get("indications")
    if indications is not None and not isinstance(indications, list):
        return _error("indications must be a list of strings", "INVALID_TYPE", 400)
    indications = indications or []

    now = _utc_now_iso()

    optional_defaults = {
        "generic_name": "", "description": "", "manufacturer": "", "specification": "",
        "dosage_form": "", "unit": "", "pack_size": "", "approval_number": "", "barcode": "",
        "storage_condition": "", "usage_dosage": "", "contraindications": "", "side_effects": "",
        "interaction_warning": "", "pregnancy_category": "", "pediatric_caution": "",
        "supplier": "", "country_of_origin": "", "image_url": "", "category": "",
    }
    row_vals = {
        "name": name,
        "quantity": quantity,
        "expiry_date": expiry_date,
        "shelf_x": shelf_x,
        "shelf_y": shelf_y,
        "shelve_id": shelve_id,
        "category": str(data.get("category") or "").strip()[:200],
        "is_prescription": 1 if data.get("is_prescription") in (True, 1, "1", "true") else 0,
        "retail_price": _float_safe(data.get("retail_price"), 0.0),
        "cost_price": _float_safe(data.get("cost_price"), 0.0),
        "min_stock_alert": _int_safe(data.get("min_stock_alert"), 0),
    }
    for k, dv in optional_defaults.items():
        if k in ("category",):
            continue
        if k in row_vals:
            continue
        v = data.get(k, dv)
        row_vals[k] = str(v).strip()[:2000] if isinstance(v, str) else (dv if v is None else str(v))

    conn = None
    try:
        conn = get_db_connection()
        drug_id = _next_drug_id(conn)
        conn.execute(
            """
            INSERT INTO inventory (
                drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id,
                category, is_prescription, retail_price, stock,
                generic_name, description, manufacturer, specification, dosage_form,
                unit, pack_size, approval_number, barcode, storage_condition,
                usage_dosage, contraindications, side_effects, interaction_warning,
                pregnancy_category, pediatric_caution, supplier, country_of_origin,
                cost_price, min_stock_alert, image_url,
                is_deleted, created_at, updated_at
            ) VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
            """,
            (
                drug_id,
                row_vals["name"],
                row_vals["quantity"],
                row_vals["expiry_date"],
                row_vals["shelf_x"],
                row_vals["shelf_y"],
                row_vals["shelve_id"],
                row_vals["category"],
                row_vals["is_prescription"],
                row_vals["retail_price"],
                0,
                row_vals.get("generic_name", ""),
                row_vals.get("description", ""),
                row_vals.get("manufacturer", ""),
                row_vals.get("specification", ""),
                row_vals.get("dosage_form", ""),
                row_vals.get("unit", ""),
                row_vals.get("pack_size", ""),
                row_vals.get("approval_number", ""),
                row_vals.get("barcode", ""),
                row_vals.get("storage_condition", ""),
                row_vals.get("usage_dosage", ""),
                row_vals.get("contraindications", ""),
                row_vals.get("side_effects", ""),
                row_vals.get("interaction_warning", ""),
                row_vals.get("pregnancy_category", ""),
                row_vals.get("pediatric_caution", ""),
                row_vals.get("supplier", ""),
                row_vals.get("country_of_origin", ""),
                row_vals["cost_price"],
                row_vals["min_stock_alert"],
                str(data.get("image_url") or "")[:2000],
                0,
                now,
                now,
            ),
        )
        _replace_indications(conn, drug_id, indications)
        conn.commit()
        return jsonify({
            "success": True,
            "ok": True,
            "drug_id": drug_id,
            "message": "Drug created",
        }), 201
    except Exception as e:
        print(f"Database error in create_drug: {e}")
        if conn:
            conn.rollback()
        return _error("Database error while creating drug", "DB_ERROR", 500)
    finally:
        if conn:
            conn.close()


def _float_safe(v, default):
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _int_safe(v, default):
    if v is None:
        return default
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


@drug_bp.route("/drugs/<int:drug_id>", methods=["PUT"])
def update_drug(drug_id):
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return _error("Request body must be a JSON object", "INVALID_JSON", 400)

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT drug_id, is_deleted FROM inventory WHERE drug_id = ?", (drug_id,)
        )
        row = cur.fetchone()
        if row is None or row["is_deleted"]:
            return _error(f"Drug not found: id={drug_id}", "DRUG_NOT_FOUND", 404)

        sets = []
        params = []
        for key, val in data.items():
            if key == "indications":
                continue
            if key not in _UPDATABLE_COLUMNS:
                continue
            if key in ("is_prescription",):
                sets.append("is_prescription = ?")
                params.append(1 if val in (True, 1, "1", "true") else 0)
            elif key in ("quantity", "expiry_date", "shelf_x", "shelf_y", "shelve_id", "min_stock_alert"):
                try:
                    iv = int(val)
                except (TypeError, ValueError):
                    return _error(f"Invalid integer for {key}", "INVALID_TYPE", 400)
                sets.append(f"{key} = ?")
                params.append(iv)
            elif key == "retail_price" or key == "cost_price":
                try:
                    fv = float(val)
                except (TypeError, ValueError):
                    return _error(f"Invalid float for {key}", "INVALID_TYPE", 400)
                sets.append(f"{key} = ?")
                params.append(fv)
            else:
                sets.append(f"{key} = ?")
                params.append(str(val) if val is not None else "")

        now = _utc_now_iso()
        sets.append("updated_at = ?")
        params.append(now)
        params.append(drug_id)

        if sets:
            sql = f"UPDATE inventory SET {', '.join(sets)} WHERE drug_id = ?"
            conn.execute(sql, tuple(params))

        if "indications" in data:
            inds = data["indications"]
            if inds is not None and not isinstance(inds, list):
                return _error("indications must be a list", "INVALID_TYPE", 400)
            _replace_indications(conn, drug_id, inds or [])

        conn.commit()
        return jsonify({"success": True, "ok": True, "message": "Drug updated"})
    except Exception as e:
        print(f"Database error in update_drug: {e}")
        if conn:
            conn.rollback()
        return _error("Database error while updating drug", "DB_ERROR", 500)
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>", methods=["DELETE"])
def delete_drug(drug_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT drug_id, is_deleted FROM inventory WHERE drug_id = ?", (drug_id,)
        )
        row = cur.fetchone()
        if row is None:
            return _error(f"Drug not found: id={drug_id}", "DRUG_NOT_FOUND", 404)
        if row["is_deleted"]:
            return jsonify({
                "success": True,
                "ok": True,
                "message": "Drug already deleted",
            })

        now = _utc_now_iso()
        conn.execute(
            "UPDATE inventory SET is_deleted = 1, updated_at = ? WHERE drug_id = ?",
            (now, drug_id),
        )
        conn.commit()
        return jsonify({"success": True, "ok": True, "message": "Drug soft-deleted"})
    except Exception as e:
        print(f"Database error in delete_drug: {e}")
        if conn:
            conn.rollback()
        return _error("Database error while deleting drug", "DB_ERROR", 500)
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs", methods=["POST"])
def create_drug():
    """Create a new drug in inventory"""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify(
                {"success": False, "error": "请求体必须为 JSON", "code": "INVALID_JSON"}
            ),
            400,
        )

    required_fields = ["name", "quantity", "expiry_date", "shelf_x", "shelf_y", "shelve_id"]
    for field in required_fields:
        if field not in data:
            return (
                jsonify(
                    {"success": False, "error": f"缺少必要字段: {field}", "code": "MISSING_FIELD"}
                ),
                400,
            )

    try:
        name = str(data["name"])
        quantity = int(data["quantity"])
        expiry_date = int(data["expiry_date"])
        shelf_x = int(data["shelf_x"])
        shelf_y = int(data["shelf_y"])
        shelve_id = int(data["shelve_id"])
    except (TypeError, ValueError):
        return (
            jsonify({"success": False, "error": "字段类型错误", "code": "INVALID_TYPE"}),
            400,
        )

    if quantity < 0:
        return (
            jsonify({"success": False, "error": "库存数量不能为负数", "code": "INVALID_QUANTITY"}),
            400,
        )

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT MAX(drug_id) FROM inventory")
        row = cur.fetchone()
        new_id = (row[0] or 0) + 1

        conn.execute(
            "INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id),
        )
        conn.commit()

        drug = {
            "drug_id": new_id, "name": name, "quantity": quantity,
            "expiry_date": expiry_date, "shelf_x": shelf_x,
            "shelf_y": shelf_y, "shelve_id": shelve_id,
        }
        return jsonify({"success": True, "drug": drug, "message": "药品添加成功"}), 201
    except Exception as e:
        print(f"Database error in create_drug: {e}")
        if conn:
            conn.rollback()
        return (
            jsonify({"success": False, "error": "数据库错误", "code": "DB_ERROR"}),
            500,
        )
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>", methods=["PUT"])
def update_drug(drug_id):
    """Update an existing drug"""
    data = request.get_json(silent=True)
    if not data:
        return (
            jsonify({"success": False, "error": "请求体必须为 JSON", "code": "INVALID_JSON"}),
            400,
        )

    allowed_fields = ["name", "quantity", "expiry_date", "shelf_x", "shelf_y", "shelve_id"]
    updates = {}
    for key in allowed_fields:
        if key in data:
            try:
                updates[key] = str(data[key]) if key == "name" else int(data[key])
            except (TypeError, ValueError):
                return (
                    jsonify({"success": False, "error": f"字段 {key} 类型错误", "code": "INVALID_TYPE"}),
                    400,
                )

    if not updates:
        return (
            jsonify({"success": False, "error": "没有需要更新的字段", "code": "NO_UPDATES"}),
            400,
        )

    if "quantity" in updates and updates["quantity"] < 0:
        return (
            jsonify({"success": False, "error": "库存数量不能为负数", "code": "INVALID_QUANTITY"}),
            400,
        )

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT * FROM inventory WHERE drug_id = ?", (drug_id,))
        if not cur.fetchone():
            return (
                jsonify({"success": False, "error": f"药品不存在: id={drug_id}", "code": "DRUG_NOT_FOUND"}),
                404,
            )

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE inventory SET {set_clause} WHERE drug_id = ?", list(updates.values()) + [drug_id])
        conn.commit()

        cur = conn.execute(
            "SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?",
            (drug_id,),
        )
        drug = dict(cur.fetchone())
        return jsonify({"success": True, "drug": drug, "message": "药品更新成功"})
    except Exception as e:
        print(f"Database error in update_drug: {e}")
        if conn:
            conn.rollback()
        return (
            jsonify({"success": False, "error": "数据库错误", "code": "DB_ERROR"}),
            500,
        )
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>", methods=["DELETE"])
def delete_drug(drug_id):
    """Delete a drug from inventory"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT name FROM inventory WHERE drug_id = ?", (drug_id,))
        existing = cur.fetchone()
        if not existing:
            return (
                jsonify({"success": False, "error": f"药品不存在: id={drug_id}", "code": "DRUG_NOT_FOUND"}),
                404,
            )

        drug_name = existing["name"]
        conn.execute("DELETE FROM inventory WHERE drug_id = ?", (drug_id,))
        conn.commit()
        return jsonify({"success": True, "message": f"药品 '{drug_name}' 已删除", "drug_id": drug_id})
    except Exception as e:
        print(f"Database error in delete_drug: {e}")
        if conn:
            conn.rollback()
        return (
            jsonify({"success": False, "error": "数据库错误", "code": "DB_ERROR"}),
            500,
        )
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/stats", methods=["GET"])
def drug_stats():
    """Get drug inventory statistics"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT COUNT(*) as total, SUM(quantity) as total_qty FROM inventory")
        row = cur.fetchone()
        total = row["total"] or 0
        total_quantity = row["total_qty"] or 0

        cur = conn.execute("SELECT COUNT(*) FROM inventory WHERE expiry_date <= 0")
        expired = cur.fetchone()[0]

        cur = conn.execute("SELECT COUNT(*) FROM inventory WHERE quantity < 10")
        low_stock = cur.fetchone()[0]

        cur = conn.execute("SELECT COUNT(*) FROM inventory WHERE expiry_date <= 30 AND expiry_date > 0")
        expiring_soon = cur.fetchone()[0]

        return jsonify({
            "success": True,
            "stats": {
                "total_drugs": total,
                "total_quantity": total_quantity,
                "expired_count": expired,
                "low_stock_count": low_stock,
                "expiring_soon_count": expiring_soon,
            },
        })
    except Exception as e:
        print(f"Database error in drug_stats: {e}")
        return (
            jsonify({"success": False, "error": "数据库错误", "code": "DB_ERROR"}),
            500,
        )
    finally:
        if conn:
            conn.close()

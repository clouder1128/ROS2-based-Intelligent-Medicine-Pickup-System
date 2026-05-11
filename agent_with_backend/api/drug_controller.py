"""
Drug Controller
Handles drug inventory management and queries
"""

import json
import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from auth.constants import (
    PERM_BATCH_DRUG,
    PERM_CREATE_DRUG,
    PERM_DELETE_DRUG,
    PERM_READ_DRUG,
    PERM_READ_INVENTORY,
    PERM_UPDATE_DRUG,
    PERM_UPDATE_INVENTORY,
)
from auth.middleware import require_permission
from common.utils.database import get_db_connection
from common.utils.validation import validate_drug
from common.utils import (
    success_response,
    created_response,
    error_response,
    not_found_response,
    bad_request_response,
    internal_error_response,
)

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
# 含组件1 Week1 扩展列：strength、drug_interactions、age_restrictions、
# min_stock_level、max_stock_level、purchase_price（与 inventory DDL / validate_drug 对齐）
_UPDATABLE_COLUMNS = {
    "name", "generic_name", "description", "quantity", "expiry_date",
    "shelf_x", "shelf_y", "shelve_id", "category", "is_prescription",
    "retail_price", "manufacturer", "specification", "dosage_form", "unit",
    "pack_size", "approval_number", "barcode", "storage_condition",
    "usage_dosage", "contraindications", "side_effects", "interaction_warning",
    "pregnancy_category", "pediatric_caution", "supplier", "country_of_origin",
    "cost_price", "min_stock_alert", "image_url",
    "strength", "drug_interactions", "age_restrictions",
    "min_stock_level", "max_stock_level", "purchase_price",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")



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
@require_permission(PERM_READ_DRUG)
def list_drugs():
    name_filter = request.args.get("name")
    symptom_filter = request.args.get("symptom")
    category_filter = request.args.get("category")
    sort_by = request.args.get("sort_by") or "drug_id"
    sort_order = (request.args.get("order") or "asc").lower()
    if sort_order not in ("asc", "desc"):
        return bad_request_response("order must be asc or desc")
    if sort_by not in _SORT_SQL:
        return bad_request_response(
            f"sort_by must be one of: {', '.join(sorted(_SORT_SQL))}"
        )

    # 未传 page/limit 时保持旧行为：返回全量列表（与 PharmacyHTTPClient 等调用方兼容）
    use_pagination = (
        request.args.get("page") is not None or request.args.get("limit") is not None
    )
    if use_pagination:
        paginated = _parse_pagination()
        if paginated is None:
            return bad_request_response("page and limit must be integers")
        page, limit, offset = paginated
    else:
        page, limit, offset = 1, 20, 0

    if name_filter is not None and len(name_filter) > 100:
        return bad_request_response("Name filter too long (max 100 characters)")
    if symptom_filter is not None and len(symptom_filter) > 100:
        return bad_request_response("Symptom filter too long (max 100 characters)")
    if category_filter is not None and len(category_filter) > 200:
        return bad_request_response("category filter too long")

    for f in [name_filter, symptom_filter, category_filter]:
        if f is not None and re.search(r'[;\\\'"`]', f):
            return bad_request_response("Invalid characters in filter")

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
                "data": drugs,
                "count": len(drugs),
                "filters": {
                    "symptom": symptom_filter,
                    "category": category_filter or "",
                    "name": name_filter or "",
                    "sort_by": sort_by,
                    "order": sort_order,
                },
                "pagination": _pagination_dict(page, limit, total) if use_pagination else None,
                "error": None,
            }
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
            "data": drugs,
            "count": len(drugs),
            "filters": {
                "name": name_filter or "",
                "category": category_filter or "",
                "sort_by": sort_by,
                "order": sort_order,
            },
            "pagination": _pagination_dict(page, limit, total) if use_pagination else None,
            "error": None,
        }
        return jsonify(out)

    except Exception as e:
        print(f"Database error in list_drugs: {e}")
        return internal_error_response("Database error while fetching drugs")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/inventory", methods=["GET"])
@require_permission(PERM_READ_INVENTORY)
def list_inventory():
    return list_drugs()


@drug_bp.route("/drugs/search", methods=["GET"])
@require_permission(PERM_READ_DRUG)
def search_drugs():
    return list_drugs()


@drug_bp.route("/drugs/<int:drug_id>", methods=["GET"])
@require_permission(PERM_READ_DRUG)
def get_drug(drug_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT * FROM inventory WHERE drug_id = ?", (drug_id,))
        row = cur.fetchone()
        if row is None:
            return not_found_response(f"Drug not found: id={drug_id}")
        drug = dict(row)
        if drug.get("is_deleted"):
            return not_found_response(f"Drug not found: id={drug_id}")

        cur = conn.execute(
            "SELECT indication FROM drug_indications WHERE drug_id = ?", (drug_id,))
        drug["indications"] = [r["indication"] for r in cur.fetchall()]

        return success_response(drug)
    except Exception as e:
        print(f"Database error in get_drug: {e}")
        return internal_error_response("Database error while fetching drug")
    finally:
        if conn:
            conn.close()


def _next_drug_id(conn) -> int:
    row = conn.execute("SELECT COALESCE(MAX(drug_id), 0) + 1 FROM inventory").fetchone()
    return int(row[0])


def _coerce_inventory_json_text(val, *, empty: str, max_len: int = 65535) -> str:
    """inventory 中与组件1 DDL 对齐的 JSON 文本列（str / list / dict）。"""
    if val is None:
        return empty
    if isinstance(val, str):
        s = val.strip()
    elif isinstance(val, (list, dict)):
        s = json.dumps(val, ensure_ascii=False)
    else:
        s = str(val)
    return s[:max_len] if len(s) > max_len else s


def _strength_coerce(val) -> str:
    if val is None:
        return ""
    return str(val).strip()[:100]


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
@require_permission(PERM_CREATE_DRUG)
def create_drug():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return bad_request_response("Request body must be a JSON object")

    ok, val_errors = validate_drug(data, is_update=False)
    if not ok:
        return error_response("VALIDATION_ERROR", f"参数错误: {val_errors}", 400)

    name = data["name"].strip()
    quantity = int(data["quantity"])
    expiry_date = int(data["expiry_date"])
    shelf_x = int(data["shelf_x"])
    shelf_y = int(data["shelf_y"])
    shelve_id = int(data["shelve_id"])
    indications = data.get("indications") or []

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
        "strength": _strength_coerce(data.get("strength")),
        "drug_interactions": _coerce_inventory_json_text(
            data.get("drug_interactions"), empty="[]"
        ),
        "age_restrictions": _coerce_inventory_json_text(
            data.get("age_restrictions"), empty="{}"
        ),
        "min_stock_level": _int_safe(data.get("min_stock_level"), 10),
        "max_stock_level": _int_safe(data.get("max_stock_level"), 500),
        "purchase_price": _float_safe(data.get("purchase_price"), 0.0),
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
                strength, drug_interactions, age_restrictions,
                min_stock_level, max_stock_level, purchase_price,
                is_deleted, created_at, updated_at
            ) VALUES (
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?,?
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
                row_vals["strength"],
                row_vals["drug_interactions"],
                row_vals["age_restrictions"],
                row_vals["min_stock_level"],
                row_vals["max_stock_level"],
                row_vals["purchase_price"],
                0,
                now,
                now,
            ),
        )
        _replace_indications(conn, drug_id, indications)
        conn.commit()
        return created_response({"drug_id": drug_id}, "Drug created")
    except Exception as e:
        print(f"Database error in create_drug: {e}")
        if conn:
            conn.rollback()
        return internal_error_response("Database error while creating drug")
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
@require_permission(PERM_UPDATE_DRUG)
def update_drug(drug_id):
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return bad_request_response("Request body must be a JSON object")

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT drug_id, is_deleted FROM inventory WHERE drug_id = ?", (drug_id,)
        )
        row = cur.fetchone()
        if row is None or row["is_deleted"]:
            return not_found_response(f"Drug not found: id={drug_id}")

        ok, val_errors = validate_drug(data, is_update=True)
        if not ok:
            return error_response("VALIDATION_ERROR", f"参数错误: {val_errors}", 400)

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
            elif key in (
                "quantity",
                "expiry_date",
                "shelf_x",
                "shelf_y",
                "shelve_id",
                "min_stock_alert",
                "min_stock_level",
                "max_stock_level",
            ):
                try:
                    iv = int(val)
                except (TypeError, ValueError):
                    return bad_request_response(f"Invalid integer for {key}")
                sets.append(f"{key} = ?")
                params.append(iv)
            elif key in ("retail_price", "cost_price", "purchase_price"):
                try:
                    fv = float(val)
                except (TypeError, ValueError):
                    return bad_request_response(f"Invalid float for {key}")
                sets.append(f"{key} = ?")
                params.append(fv)
            elif key in ("drug_interactions", "age_restrictions"):
                sets.append(f"{key} = ?")
                empty = "[]" if key == "drug_interactions" else "{}"
                params.append(_coerce_inventory_json_text(val, empty=empty))
            elif key == "strength":
                sets.append("strength = ?")
                params.append(_strength_coerce(val))
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
            _replace_indications(conn, drug_id, data["indications"] or [])

        conn.commit()
        return success_response(None, "Drug updated")
    except Exception as e:
        print(f"Database error in update_drug: {e}")
        if conn:
            conn.rollback()
        return internal_error_response("Database error while updating drug")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>", methods=["DELETE"])
@require_permission(PERM_DELETE_DRUG)
def delete_drug(drug_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT drug_id, is_deleted FROM inventory WHERE drug_id = ?", (drug_id,)
        )
        row = cur.fetchone()
        if row is None:
            return not_found_response(f"Drug not found: id={drug_id}")
        if row["is_deleted"]:
            return success_response(None, "Drug already deleted")

        now = _utc_now_iso()
        conn.execute(
            "UPDATE inventory SET is_deleted = 1, updated_at = ? WHERE drug_id = ?",
            (now, drug_id),
        )
        conn.commit()
        return success_response(None, "Drug soft-deleted")
    except Exception as e:
        print(f"Database error in delete_drug: {e}")
        if conn:
            conn.rollback()
        return internal_error_response("Database error while deleting drug")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>/adjust", methods=["POST"])
@require_permission(PERM_UPDATE_INVENTORY)
def adjust_drug_inventory(drug_id):
    """库存数量调整：JSON `quantity`（绝对值）或 `delta`（增量）。"""
    data = request.get_json(silent=True) or {}
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT drug_id, quantity, is_deleted FROM inventory WHERE drug_id = ?",
            (drug_id,),
        )
        row = cur.fetchone()
        if row is None or row["is_deleted"]:
            return error_response(
                "DRUG_NOT_FOUND", f"Drug not found: id={drug_id}", 404
            )

        now = _utc_now_iso()
        if "quantity" in data:
            try:
                q = int(data["quantity"])
            except (TypeError, ValueError):
                return error_response(
                    "INVALID_TYPE", "quantity must be an integer", 400
                )
            if q < 0:
                return error_response("INVALID_INPUT", "quantity must be >= 0", 400)
            conn.execute(
                "UPDATE inventory SET quantity = ?, updated_at = ? WHERE drug_id = ?",
                (q, now, drug_id),
            )
        elif "delta" in data:
            try:
                d = int(data["delta"])
            except (TypeError, ValueError):
                return error_response("INVALID_TYPE", "delta must be an integer", 400)
            cur = conn.execute(
                """
                UPDATE inventory
                SET quantity = quantity + ?, updated_at = ?
                WHERE drug_id = ? AND quantity + ? >= 0
                """,
                (d, now, drug_id, d),
            )
            if cur.rowcount == 0:
                return error_response(
                    "INVALID_ADJUST",
                    "Insufficient quantity for delta adjustment",
                    400,
                )
        else:
            return error_response("MISSING_FIELDS", "Provide quantity or delta", 400)

        conn.commit()
        cur = conn.execute(
            "SELECT quantity FROM inventory WHERE drug_id = ?", (drug_id,)
        )
        qrow = cur.fetchone()
        return success_response(
            {
                "drug_id": drug_id,
                "quantity": qrow["quantity"] if qrow else None,
            }
        )
    except Exception as e:
        print(f"Database error in adjust_drug_inventory: {e}")
        if conn:
            conn.rollback()
        return internal_error_response("Database error while adjusting inventory")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/batch-import", methods=["POST"])
@require_permission(PERM_BATCH_DRUG)
def batch_import_drugs():
    """批量创建药品（每项字段与简化 POST /drugs 一致）。"""
    items = request.get_json(silent=True)
    if not isinstance(items, list) or not items:
        return error_response(
            "INVALID_JSON",
            "Request body must be a non-empty JSON array",
            400,
        )

    required_fields = ["name", "quantity", "expiry_date", "shelf_x", "shelf_y", "shelve_id"]
    conn = None
    try:
        conn = get_db_connection()
        created_ids: list[int] = []
        for idx, data in enumerate(items):
            if not isinstance(data, dict):
                return error_response(
                    "INVALID_TYPE", f"Item {idx} must be an object", 400
                )
            for field in required_fields:
                if field not in data:
                    return error_response(
                        "MISSING_FIELDS",
                        f"Item {idx} missing field: {field}",
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
                return error_response(
                    "INVALID_TYPE", f"Item {idx} has invalid field types", 400
                )

            if quantity < 0:
                return error_response(
                    "INVALID_QUANTITY",
                    f"Item {idx}: quantity cannot be negative",
                    400,
                )

            new_id = _next_drug_id(conn)
            conn.execute(
                "INSERT INTO inventory (drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (new_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id),
            )
            created_ids.append(new_id)

        conn.commit()
        return created_response(
            {"drug_ids": created_ids, "count": len(created_ids)},
            "Batch import completed",
        )
    except Exception as e:
        print(f"Database error in batch_import_drugs: {e}")
        if conn:
            conn.rollback()
        return internal_error_response("Database error during batch import")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/stats", methods=["GET"])
@require_permission(PERM_READ_INVENTORY)
def drug_stats():
    """Get drug inventory statistics"""
    conn = None
    try:
        conn = get_db_connection()
        active = "COALESCE(is_deleted, 0) = 0"
        cur = conn.execute(
            f"SELECT COUNT(*) as total, SUM(quantity) as total_qty FROM inventory WHERE {active}"
        )
        row = cur.fetchone()
        total = row["total"] or 0
        total_quantity = row["total_qty"] or 0

        cur = conn.execute(
            f"SELECT COUNT(*) FROM inventory WHERE expiry_date <= 0 AND {active}"
        )
        expired = cur.fetchone()[0]

        cur = conn.execute(
            f"SELECT COUNT(*) FROM inventory WHERE quantity < 10 AND {active}"
        )
        low_stock = cur.fetchone()[0]

        cur = conn.execute(
            f"SELECT COUNT(*) FROM inventory WHERE expiry_date <= 30 AND expiry_date > 0 AND {active}"
        )
        expiring_soon = cur.fetchone()[0]

        return success_response({
            "total_drugs": total,
            "total_quantity": total_quantity,
            "expired_count": expired,
            "low_stock_count": low_stock,
            "expiring_soon_count": expiring_soon,
        })
    except Exception as e:
        print(f"Database error in drug_stats: {e}")
        return internal_error_response("数据库错误")
    finally:
        if conn:
            conn.close()

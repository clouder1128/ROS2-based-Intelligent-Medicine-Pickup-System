"""
Drug Controller
Handles drug inventory management and queries
"""

import csv
import json
import re
from datetime import datetime, timezone
from io import StringIO

from flask import Blueprint, Response, jsonify, request

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
from common.utils.drug_service import (
    query_drugs,
    get_drug as load_drug_detail,
    _deduplicate as _deduplicate_drugs,
    _fetch_with_indications as _fetch_drugs_with_indications,
)
from common.utils.validation import (
    TRANSACTION_TYPE_CHOICES,
    validate_drug,
    validate_inventory_transaction,
)
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


def _parse_alert_threshold(default: int = 10):
    """低库存兜底阈值（与 stats 默认 quantity < 10 对齐）；可用 ?threshold= 覆盖。"""
    try:
        t = int(request.args.get("threshold", str(default)))
    except (TypeError, ValueError):
        return None
    if t < 0 or t > 1_000_000:
        return None
    return t


def _parse_expiring_days(default: int = 30):
    """临期：剩余有效天数 expiry_date ∈ (0, days]；与 stats 默认 days=30 对齐。"""
    try:
        d = int(request.args.get("days", str(default)))
    except (TypeError, ValueError):
        return None
    if d < 1 or d > 3650:
        return None
    return d


def _attach_indications_inplace(conn, drugs: list):
    drug_ids = [d["drug_id"] for d in drugs]
    if not drug_ids:
        return
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


# GET /inventory 拣货视图：收窄字段并附运营标记（≠ GET /drugs 全字段）
_INVENTORY_VIEW_KEYS = (
    "drug_id",
    "name",
    "generic_name",
    "quantity",
    "expiry_date",
    "shelf_x",
    "shelf_y",
    "shelve_id",
    "category",
    "barcode",
    "unit",
    "dosage_form",
    "specification",
    "min_stock_alert",
    "min_stock_level",
    "max_stock_level",
    "is_prescription",
    "storage_condition",
    "retail_price",
)


def _inventory_projection(d: dict, *, low_threshold: int, expiring_window: int) -> dict:
    out = {k: d.get(k) for k in _INVENTORY_VIEW_KEYS}
    out["indications"] = d.get("indications") or []
    try:
        sx = int(out.get("shelf_x") or 0)
        sy = int(out.get("shelf_y") or 0)
        sh = int(out.get("shelve_id") or 0)
        out["location_label"] = f"Shelf {sh}, Position ({sx}, {sy})"
    except (TypeError, ValueError):
        out["location_label"] = ""

    q = int(out.get("quantity") or 0)
    try:
        ed = int(out.get("expiry_date") or 0)
    except (TypeError, ValueError):
        ed = 0

    ma = out.get("min_stock_alert")
    if ma is not None:
        try:
            ma_int = int(ma)
            needs_restock = q <= ma_int
        except (TypeError, ValueError):
            needs_restock = q < low_threshold
    else:
        needs_restock = q < low_threshold

    out["needs_restock"] = needs_restock
    out["is_expired_stock"] = ed <= 0
    out["expiring_soon"] = (ed > 0) and (ed <= expiring_window)
    return out


def _wants_csv_export() -> bool:
    """?format=json|csv；未指定时用 Accept（text/csv 优先导出表格）"""
    fmt = (request.args.get("format") or "").strip().lower()
    if fmt == "csv":
        return True
    if fmt == "json":
        return False
    best = request.accept_mimetypes.best_match(["application/json", "text/csv"])
    return best == "text/csv"


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

    try:
        drugs = query_drugs(
            symptom=symptom_filter,
            name=name_filter,
            category=category_filter,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total = len(drugs)
        if use_pagination:
            drugs = drugs[offset : offset + limit]

        out = {
            "success": True,
            "data": drugs,
            "count": len(drugs),
            "filters": {
                "symptom": symptom_filter or "",
                "category": category_filter or "",
                "name": name_filter or "",
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


@drug_bp.route("/inventory", methods=["GET"])
@require_permission(PERM_READ_INVENTORY)
def list_inventory():
    """
    拣货 / 库区视图：与 GET /drugs 相同的排序、分页与 name/category/symptom 过滤，
    但每条记录仅返回库区与补货关注点字段，并附带 needs_restock、expiring_soon 等布尔标记。

    查询参数（除与 /drugs 相同外）：
      threshold         低库存兜底阈值（无 min_stock_alert 时与 /drugs/stats 一致，默认 10）
      expiring_window   临期判定窗口天數（默认 30，与 /drugs/stats 的 expiring_soon 一致）
    """
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

    low_threshold = _parse_alert_threshold(10)
    if low_threshold is None:
        low_threshold = 10

    exp_win = _parse_expiring_days(30)
    if exp_win is None:
        exp_win = 30

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
                drugs = [
                    d for d in drugs if (d.get("category") or "") == category_filter
                ]
            if name_filter:
                drugs = [
                    d
                    for d in drugs
                    if name_filter.lower() in (d.get("name") or "").lower()
                ]

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

            data = [
                _inventory_projection(
                    d, low_threshold=low_threshold, expiring_window=exp_win
                )
                for d in drugs
            ]
            out = {
                "success": True,
                "data": data,
                "count": len(data),
                "filters": {
                    "view": "inventory",
                    "symptom": symptom_filter,
                    "category": category_filter or "",
                    "name": name_filter or "",
                    "sort_by": sort_by,
                    "order": sort_order,
                    "threshold": low_threshold,
                    "expiring_window": exp_win,
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
        _attach_indications_inplace(conn, drugs)

        data = [
            _inventory_projection(d, low_threshold=low_threshold, expiring_window=exp_win)
            for d in drugs
        ]

        out = {
            "success": True,
            "data": data,
            "count": len(data),
            "filters": {
                "view": "inventory",
                "name": name_filter or "",
                "category": category_filter or "",
                "sort_by": sort_by,
                "order": sort_order,
                "threshold": low_threshold,
                "expiring_window": exp_win,
            },
            "pagination": _pagination_dict(page, limit, total) if use_pagination else None,
            "error": None,
        }
        return jsonify(out)

    except Exception as e:
        print(f"Database error in list_inventory: {e}")
        return internal_error_response("Database error while fetching inventory")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/search", methods=["GET"])
@require_permission(PERM_READ_DRUG)
def search_drugs():
    """
    综合搜索：在未提供 keyword/q 时行为与 GET /api/drugs（list_drugs）完全一致。

    提供 keyword 或 q 时：
      在未软删的药品中，对 name、generic_name、description、适应症（drug_indications）
      做子串模糊匹配（LIKE）；可叠加 category；分页与排序规则与列表接口相同。
    """
    raw_kw = request.args.get("keyword") or request.args.get("q")
    kw = (raw_kw or "").strip()
    if not kw:
        return list_drugs()

    if len(kw) > 100:
        return bad_request_response("keyword too long (max 100 characters)")
    if re.search(r'[;\\\'"`]', kw):
        return bad_request_response("Invalid characters in keyword")

    category_filter = request.args.get("category")
    sort_by = request.args.get("sort_by") or "drug_id"
    sort_order = (request.args.get("order") or "asc").lower()
    if sort_order not in ("asc", "desc"):
        return bad_request_response("order must be asc or desc")
    if sort_by not in _SORT_SQL:
        return bad_request_response(
            f"sort_by must be one of: {', '.join(sorted(_SORT_SQL))}"
        )

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

    if category_filter is not None and len(category_filter) > 200:
        return bad_request_response("category filter too long")

    pattern = f"%{kw}%"
    order_sql = f"ORDER BY {_SORT_SQL[sort_by]} {sort_order.upper()}"

    where_parts = [
        "COALESCE(is_deleted, 0) = 0",
        """(
            name LIKE ?
            OR IFNULL(generic_name, '') LIKE ?
            OR IFNULL(description, '') LIKE ?
            OR drug_id IN (
                SELECT DISTINCT drug_id FROM drug_indications WHERE indication LIKE ?
            )
        )""",
    ]
    params: list = [pattern, pattern, pattern, pattern]
    if category_filter:
        where_parts.append("category = ?")
        params.append(category_filter)

    where_sql = "WHERE " + " AND ".join(where_parts)
    tuple_params = tuple(params)

    conn = None
    try:
        conn = get_db_connection()

        if use_pagination:
            cur = conn.execute(
                f"SELECT COUNT(*) FROM inventory {where_sql}",
                tuple_params,
            )
            total = cur.fetchone()[0]
            list_sql = (
                f"SELECT * FROM inventory {where_sql} {order_sql} LIMIT ? OFFSET ?"
            )
            cur = conn.execute(list_sql, tuple_params + (limit, offset))
        else:
            total = 0
            list_sql = f"SELECT * FROM inventory {where_sql} {order_sql}"
            cur = conn.execute(list_sql, tuple_params)

        drugs = [dict(row) for row in cur.fetchall()]
        drug_ids = [d["drug_id"] for d in drugs]
        if drug_ids:
            ph = ",".join("?" for _ in drug_ids)
            cur = conn.execute(
                f"SELECT drug_id, indication FROM drug_indications WHERE drug_id IN ({ph})",
                drug_ids,
            )
            imap: dict[int, list] = {}
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
                "keyword": kw,
                "q": kw,
                "category": category_filter or "",
                "sort_by": sort_by,
                "order": sort_order,
            },
            "pagination": _pagination_dict(page, limit, total) if use_pagination else None,
            "error": None,
        }
        return jsonify(out)
    except Exception as e:
        print(f"Database error in search_drugs: {e}")
        return internal_error_response("Database error while searching drugs")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/low-stock", methods=["GET"])
@require_permission(PERM_READ_INVENTORY)
def list_low_stock_drugs():
    """
    低库存列表：每条若配置了 min_stock_alert，则 quantity <= min_stock_alert 视为预警；
    未配置时与 /drugs/stats 一致：quantity < threshold（默认 10）。
    """
    threshold = _parse_alert_threshold(10)
    if threshold is None:
        return bad_request_response("threshold must be integer 0..1000000")
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

    where_sql = (
        "WHERE COALESCE(is_deleted, 0) = 0 AND ("
        "(min_stock_alert IS NOT NULL AND quantity <= min_stock_alert) OR "
        "(min_stock_alert IS NULL AND quantity < ?))"
    )
    order_sql = "ORDER BY quantity ASC, drug_id ASC"

    conn = None
    try:
        conn = get_db_connection()
        if use_pagination:
            cur = conn.execute(f"SELECT COUNT(*) FROM inventory {where_sql}", (threshold,))
            total = cur.fetchone()[0]
            cur = conn.execute(
                f"SELECT * FROM inventory {where_sql} {order_sql} LIMIT ? OFFSET ?",
                (threshold, limit, offset),
            )
        else:
            total = 0
            cur = conn.execute(
                f"SELECT * FROM inventory {where_sql} {order_sql}",
                (threshold,),
            )
        drugs = [dict(row) for row in cur.fetchall()]
        _attach_indications_inplace(conn, drugs)

        out = {
            "success": True,
            "data": drugs,
            "count": len(drugs),
            "filters": {
                "threshold": threshold,
                "rule": (
                    "per-drug min_stock_alert if set; else quantity < threshold "
                    "(aligned with GET /drugs/stats)"
                ),
            },
            "pagination": _pagination_dict(page, limit, total) if use_pagination else None,
            "error": None,
        }
        return jsonify(out)
    except Exception as e:
        print(f"Database error in list_low_stock_drugs: {e}")
        return internal_error_response("Database error while fetching low-stock drugs")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/expiring-soon", methods=["GET"])
@require_permission(PERM_READ_INVENTORY)
def list_expiring_soon_drugs():
    """
    临期列表：0 < expiry_date <= days（默认 30），与 GET /drugs/stats 的 expiring_soon_count 一致。
    expiry_date <= 0 视为已过期，不在此列表。
    """
    days = _parse_expiring_days(30)
    if days is None:
        return bad_request_response("days must be integer 1..3650")
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

    where_sql = (
        "WHERE COALESCE(is_deleted, 0) = 0 AND expiry_date > 0 "
        "AND expiry_date <= ?"
    )
    order_sql = "ORDER BY expiry_date ASC, drug_id ASC"

    conn = None
    try:
        conn = get_db_connection()
        if use_pagination:
            cur = conn.execute(f"SELECT COUNT(*) FROM inventory {where_sql}", (days,))
            total = cur.fetchone()[0]
            cur = conn.execute(
                f"SELECT * FROM inventory {where_sql} {order_sql} LIMIT ? OFFSET ?",
                (days, limit, offset),
            )
        else:
            total = 0
            cur = conn.execute(
                f"SELECT * FROM inventory {where_sql} {order_sql}",
                (days,),
            )
        drugs = [dict(row) for row in cur.fetchall()]
        _attach_indications_inplace(conn, drugs)

        out = {
            "success": True,
            "data": drugs,
            "count": len(drugs),
            "filters": {"days": days},
            "pagination": _pagination_dict(page, limit, total) if use_pagination else None,
            "error": None,
        }
        return jsonify(out)
    except Exception as e:
        print(f"Database error in list_expiring_soon_drugs: {e}")
        return internal_error_response("Database error while fetching expiring drugs")
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>", methods=["GET"])
@require_permission(PERM_READ_DRUG)
def get_drug(drug_id):
    try:
        drug = load_drug_detail(drug_id)
        if drug is None:
            return not_found_response(f"Drug not found: id={drug_id}")
        return success_response(drug)
    except Exception as e:
        print(f"Database error in get_drug: {e}")
        return internal_error_response("Database error while fetching drug")


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


def _insert_drug_row(conn, data: dict, *, now: str | None = None) -> int:
    """
    插入一行完整 inventory（41 列，含组件1 Week1 扩展列）。
    调用方须已通过 validate_drug(data, is_update=False)。
    不写 commit。
    """
    if now is None:
        now = _utc_now_iso()

    name = data["name"].strip()
    quantity = int(data["quantity"])
    expiry_date = int(data["expiry_date"])
    shelf_x = int(data["shelf_x"])
    shelf_y = int(data["shelf_y"])
    shelve_id = int(data["shelve_id"])
    indications = data.get("indications") or []

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
    return drug_id


@drug_bp.route("/drugs", methods=["POST"])
@require_permission(PERM_CREATE_DRUG)
def create_drug():
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return bad_request_response("Request body must be a JSON object")

    ok, val_errors = validate_drug(data, is_update=False)
    if not ok:
        return error_response("VALIDATION_ERROR", f"参数错误: {val_errors}", 400)

    conn = None
    try:
        conn = get_db_connection()
        drug_id = _insert_drug_row(conn, data)
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
    """
    调整库存并在 inventory_transactions 记一笔账。

    三种写法（任选其一）：
    1) 规范：`quantity_change`（非零整数）+ `transaction_type`（in/out/adjust/expire）
       可选：`reason`、`operator`。由 validate_inventory_transaction 校验。
    2) 兼容：`quantity` 设为绝对库存；可选 `transaction_type`，默认 adjust。
    3) 兼容：`delta` 相对增减；可选 `transaction_type`，默认 adjust。

    quantity_change（或等价变化）为 0 时不更新库存、不写流水。
    """
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

        before = int(row["quantity"])
        now = _utc_now_iso()
        reason = str(data.get("reason") or "")[:500]
        operator = str(data.get("operator") or "")[:100]

        has_canonical = ("quantity_change" in data) or ("transaction_type" in data)
        qc: int
        after: int
        tt: str

        if has_canonical:
            if "quantity_change" not in data or "transaction_type" not in data:
                return error_response(
                    "MISSING_FIELDS",
                    "quantity_change and transaction_type must both be provided",
                    400,
                )
            ok, val_errors = validate_inventory_transaction(data)
            if not ok:
                return error_response(
                    "VALIDATION_ERROR", f"参数错误: {val_errors}", 400
                )
            qc = int(data["quantity_change"])
            tt = str(data["transaction_type"]).strip().lower()
            reason = str(data.get("reason") or "")[:500]
            operator = str(data.get("operator") or "")[:100]
            after = before + qc
            if after < 0:
                return error_response(
                    "INVALID_ADJUST",
                    "Insufficient quantity for this adjustment",
                    400,
                )
        elif "quantity" in data:
            try:
                q = int(data["quantity"])
            except (TypeError, ValueError):
                return error_response(
                    "INVALID_TYPE", "quantity must be an integer", 400
                )
            if q < 0:
                return error_response("INVALID_INPUT", "quantity must be >= 0", 400)
            after = q
            qc = after - before
            tt = str(data.get("transaction_type") or "adjust").strip().lower()
            if tt not in TRANSACTION_TYPE_CHOICES:
                return bad_request_response(
                    f"transaction_type must be one of: {', '.join(TRANSACTION_TYPE_CHOICES)}"
                )
        elif "delta" in data:
            try:
                d = int(data["delta"])
            except (TypeError, ValueError):
                return error_response("INVALID_TYPE", "delta must be an integer", 400)
            qc = d
            after = before + qc
            if after < 0:
                return error_response(
                    "INVALID_ADJUST",
                    "Insufficient quantity for delta adjustment",
                    400,
                )
            tt = str(data.get("transaction_type") or "adjust").strip().lower()
            if tt not in TRANSACTION_TYPE_CHOICES:
                return bad_request_response(
                    f"transaction_type must be one of: {', '.join(TRANSACTION_TYPE_CHOICES)}"
                )
        else:
            return error_response(
                "MISSING_FIELDS",
                "Provide quantity_change+transaction_type, quantity, or delta",
                400,
            )

        transaction_id = None
        if qc != 0:
            conn.execute(
                "UPDATE inventory SET quantity = ?, updated_at = ? WHERE drug_id = ?",
                (after, now, drug_id),
            )
            tx_cur = conn.execute(
                """
                INSERT INTO inventory_transactions (
                    drug_id, quantity_change, transaction_type,
                    before_quantity, after_quantity, reason, operator, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    drug_id,
                    qc,
                    tt,
                    before,
                    after,
                    reason,
                    operator,
                    now,
                ),
            )
            transaction_id = tx_cur.lastrowid

        conn.commit()
        final_row = conn.execute(
            "SELECT quantity FROM inventory WHERE drug_id = ?", (drug_id,)
        ).fetchone()
        final_qty = int(final_row["quantity"]) if final_row else before
        payload = {
            "drug_id": drug_id,
            "quantity": final_qty,
            "quantity_change": qc,
            "transaction_id": transaction_id,
        }
        return success_response(payload, "Inventory adjusted")
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
    """
    批量创建药品：请求体为非空 JSON 数组，每项与 POST /api/drugs 字段一致，
    经 validate_drug 校验后写入完整 inventory 列并同步 indications。
    """
    items = request.get_json(silent=True)
    if not isinstance(items, list) or not items:
        return error_response(
            "INVALID_JSON",
            "Request body must be a non-empty JSON array",
            400,
        )

    now = _utc_now_iso()
    conn = None
    try:
        conn = get_db_connection()
        created_ids: list[int] = []
        for idx, data in enumerate(items):
            if not isinstance(data, dict):
                return error_response(
                    "INVALID_TYPE", f"Item {idx} must be an object", 400
                )

            ok, val_errors = validate_drug(data, is_update=False)
            if not ok:
                return error_response(
                    "VALIDATION_ERROR",
                    f"Item {idx}: {val_errors}",
                    400,
                )

            drug_id = _insert_drug_row(conn, data, now=now)
            created_ids.append(drug_id)

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


def _drug_row_for_csv_value(v):
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


@drug_bp.route("/drugs/export", methods=["GET"])
@require_permission(PERM_READ_DRUG)
def export_drugs():
    """
    导出所有未软删药品（结构与列表接口单条记录一致，含 indications）。
    默认 JSON；?format=csv 或 Accept: text/csv 返回 CSV。
    """
    conn = None
    try:
        conn = get_db_connection()
        drugs = _fetch_drugs_with_indications(
            conn,
            "WHERE COALESCE(is_deleted, 0) = 0 ORDER BY drug_id",
            (),
        )

        if _wants_csv_export():
            if not drugs:
                fieldnames = [
                    "drug_id", "name", "quantity", "expiry_date", "category", "indications"
                ]
                buf = StringIO()
                csv.writer(buf).writerow(fieldnames)
                return Response(
                    "\ufeff" + buf.getvalue(),
                    mimetype="text/csv; charset=utf-8",
                    headers={
                        "Content-Disposition": 'attachment; filename="drugs_export.csv"',
                    },
                )
            keys_sorted = sorted(k for k in drugs[0].keys() if k != "indications")
            fieldnames = keys_sorted + ["indications"]
            buf = StringIO()
            writer = csv.DictWriter(
                buf,
                fieldnames=fieldnames,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            for d in drugs:
                row = {k: _drug_row_for_csv_value(d.get(k)) for k in keys_sorted}
                row["indications"] = "|".join(d.get("indications") or [])
                writer.writerow(row)
            return Response(
                "\ufeff" + buf.getvalue(),
                mimetype="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": 'attachment; filename="drugs_export.csv"',
                },
            )

        return success_response({"drugs": drugs, "count": len(drugs)}, "Export OK")
    except Exception as e:
        print(f"Database error in export_drugs: {e}")
        return internal_error_response("Database error during export")
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

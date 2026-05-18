"""
Category Controller
药品分类管理：列表查询（含树形结构）与新建分类。
categories 表由组件1 建立，name 与 inventory.category 字符串匹配。
"""

from datetime import datetime, timezone

from flask import Blueprint, request

from auth.constants import PERM_CREATE_DRUG, PERM_READ_DRUG
from auth.middleware import require_permission
from common.utils.database import get_db_connection
from common.utils.validation import validate_category
from database.models.category import Category
from common.utils import (
    success_response,
    created_response,
    paginated_response,
    error_response,
    bad_request_response,
    internal_error_response,
    not_found_response,
    parse_pagination,
)

category_bp = Blueprint("category", __name__, url_prefix="/api")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_tree(categories: list[dict]) -> list[dict]:
    """将平铺的分类列表组装成树形结构（children 嵌套）。"""
    by_id = {c["id"]: {**c, "children": []} for c in categories}
    roots = []
    for c in by_id.values():
        pid = c.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(c)
        else:
            roots.append(c)
    return roots


@category_bp.route("/categories", methods=["GET"])
@require_permission(PERM_READ_DRUG)
def list_categories():
    """
    获取分类列表。

    查询参数：
      tree=1        返回树形结构（默认平铺）
      page / limit  启用分页（不传则全量返回）
    """
    want_tree = request.args.get("tree") in ("1", "true")
    use_pagination = (
        request.args.get("page") is not None
        or request.args.get("limit") is not None
    )

    conn = None
    try:
        conn = get_db_connection()

        if use_pagination:
            params = parse_pagination(request.args)
            page, limit, offset = params["page"], params["limit"], params["offset"]

            total = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]

            rows = conn.execute(
                "SELECT * FROM categories ORDER BY sort_order, id LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            categories = [Category.from_dict(dict(r)).to_dict() for r in rows]

            for cat in categories:
                cat["drug_count"] = conn.execute(
                    "SELECT COUNT(*) FROM inventory WHERE category = ? AND COALESCE(is_deleted, 0) = 0",
                    (cat["name"],),
                ).fetchone()[0]

            if want_tree:
                categories = _build_tree(categories)

            return paginated_response(categories, page, limit, total)

        else:
            rows = conn.execute(
                "SELECT * FROM categories ORDER BY sort_order, id"
            ).fetchall()
            categories = [Category.from_dict(dict(r)).to_dict() for r in rows]

            for cat in categories:
                cat["drug_count"] = conn.execute(
                    "SELECT COUNT(*) FROM inventory WHERE category = ? AND COALESCE(is_deleted, 0) = 0",
                    (cat["name"],),
                ).fetchone()[0]

            if want_tree:
                categories = _build_tree(categories)

            return success_response(categories)

    except Exception as e:
        print(f"Database error in list_categories: {e}")
        return internal_error_response("Database error while listing categories")
    finally:
        if conn:
            conn.close()


@category_bp.route("/categories", methods=["POST"])
@require_permission(PERM_CREATE_DRUG)
def create_category():
    """
    新建分类。

    请求体 JSON：
      name        (必填) 分类名称，≤50 字符，不可重复
      description (可选) 分类描述，≤500 字符
      parent_id   (可选) 父分类 ID（NULL 表示顶级）
      sort_order  (可选) 排序权重，默认 0
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return bad_request_response("Request body must be a JSON object")

    ok, val_errors = validate_category(data, is_update=False)
    if not ok:
        return error_response("VALIDATION_ERROR", f"参数错误: {val_errors}", 400)

    name = str(data["name"]).strip()
    description = str(data.get("description") or "").strip()[:500]
    parent_id = data.get("parent_id")
    sort_order = int(data.get("sort_order", 0))

    conn = None
    try:
        conn = get_db_connection()

        existing = conn.execute(
            "SELECT id FROM categories WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            return error_response(
                "DUPLICATE_NAME",
                f"分类名称已存在: '{name}'",
                409,
            )

        if parent_id is not None:
            parent_id = int(parent_id)
            parent = conn.execute(
                "SELECT id FROM categories WHERE id = ?", (parent_id,)
            ).fetchone()
            if not parent:
                return not_found_response(f"父分类不存在: id={parent_id}")

        now = _utc_now_iso()
        cur = conn.execute(
            """
            INSERT INTO categories (name, description, parent_id, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, description, parent_id, sort_order, now),
        )
        conn.commit()

        new_id = cur.lastrowid
        return created_response(
            {
                "id": new_id,
                "name": name,
                "description": description,
                "parent_id": parent_id,
                "sort_order": sort_order,
                "created_at": now,
            },
            "分类创建成功",
        )
    except Exception as e:
        print(f"Database error in create_category: {e}")
        if conn:
            conn.rollback()
        return internal_error_response("Database error while creating category")
    finally:
        if conn:
            conn.close()

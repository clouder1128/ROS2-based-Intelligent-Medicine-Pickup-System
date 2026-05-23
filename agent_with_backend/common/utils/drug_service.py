"""
药品查询服务层 — 供 HTTP 控制器和内部工具共享使用
消除同进程内的 HTTP 回环调用，直接访问数据库。
"""

from typing import Any, Dict, List, Optional

from common.utils.database import get_db_connection

# ORDER BY 白名单 — 与 drug_controller 保持一致
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


def _fetch_with_indications(conn, where_clause: str, params: tuple) -> List[dict]:
    """SELECT * FROM inventory + 拼接 indications"""
    cur = conn.execute(f"SELECT * FROM inventory {where_clause}", params)
    drugs = [dict(row) for row in cur.fetchall()]

    drug_ids = [d["drug_id"] for d in drugs]
    if drug_ids:
        placeholders = ",".join("?" for _ in drug_ids)
        cur = conn.execute(
            f"SELECT drug_id, indication FROM drug_indications WHERE drug_id IN ({placeholders})",
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

    return drugs


def _deduplicate(drugs: List[dict]) -> List[dict]:
    seen = set()
    result = []
    for d in drugs:
        if d["drug_id"] not in seen:
            seen.add(d["drug_id"])
            result.append(d)
    return result


def query_drugs(
    symptom: Optional[str] = None,
    name: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: str = "drug_id",
    sort_order: str = "asc",
) -> List[Dict[str, Any]]:
    """
    查询药品列表（支持症状/名称/分类过滤），返回带 indications 的完整药品字典。
    对应 drug_controller.list_drugs() 的核心查询逻辑。
    """
    sort_by = sort_by if sort_by in _SORT_SQL else "drug_id"
    sort_order = sort_order if sort_order in ("asc", "desc") else "asc"
    order_sql = f"ORDER BY {_SORT_SQL[sort_by]} {sort_order.upper()}"

    conn = get_db_connection()
    try:
        # ---- 症状查询路径 ----
        if symptom is not None:
            base_where = (
                "WHERE drug_id IN (SELECT DISTINCT drug_id FROM drug_indications "
                "WHERE indication LIKE ?) AND quantity > 0 AND COALESCE(is_deleted, 0) = 0"
            )
            drugs = _fetch_with_indications(conn, base_where, (f"%{symptom}%",))

            if not drugs:
                cur = conn.execute(
                    "SELECT DISTINCT standard_term FROM symptom_synonyms WHERE synonym LIKE ?",
                    (f"%{symptom}%",),
                )
                standard_terms = [row["standard_term"] for row in cur.fetchall()]
                for term in standard_terms:
                    matched = _fetch_with_indications(conn, base_where, (f"%{term}%",))
                    drugs.extend(matched)
                drugs = _deduplicate(drugs)

            if category:
                drugs = [d for d in drugs if (d.get("category") or "") == category]
            if name:
                drugs = [d for d in drugs if name.lower() in (d.get("name") or "").lower()]

            reverse = sort_order == "desc"
            if sort_by in ("name", "category"):
                drugs.sort(
                    key=lambda d: ((d.get(sort_by) or "").lower(), d["drug_id"]),
                    reverse=reverse,
                )
            else:
                drugs.sort(key=lambda d: d.get(sort_by, 0), reverse=reverse)

            return drugs

        # ---- 名称 / 分类查询路径 ----
        where_parts = ["COALESCE(is_deleted, 0) = 0"]
        params: list = []

        if category:
            where_parts.append("category = ?")
            params.append(category)
        if name:
            where_parts.append("name LIKE ?")
            params.append(f"%{name}%")

        where_sql = "WHERE " + " AND ".join(where_parts) if where_parts else ""
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

        return drugs
    finally:
        conn.close()


def get_drug(drug_id: int) -> Optional[Dict[str, Any]]:
    """查询单个药品（含 indications），不存在或已删除返回 None。"""
    conn = get_db_connection()
    try:
        cur = conn.execute("SELECT * FROM inventory WHERE drug_id = ?", (drug_id,))
        row = cur.fetchone()
        if row is None:
            return None
        drug = dict(row)
        if drug.get("is_deleted"):
            return None

        cur = conn.execute(
            "SELECT indication FROM drug_indications WHERE drug_id = ?", (drug_id,)
        )
        drug["indications"] = [r["indication"] for r in cur.fetchall()]
        return drug
    finally:
        conn.close()

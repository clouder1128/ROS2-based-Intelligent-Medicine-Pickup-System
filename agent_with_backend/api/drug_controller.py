"""
Drug Controller
Handles drug inventory management and queries
"""

from flask import Blueprint, jsonify, request
from common.utils.database import get_db_connection

drug_bp = Blueprint("drug", __name__, url_prefix="/api")


def _query_drugs_base(conn, where_clause, params):
    """执行药品查询并返回统一格式的结果"""
    cur = conn.execute(f"""
        SELECT drug_id, name, quantity, expiry_date,
               shelf_x, shelf_y, shelve_id, category,
               is_prescription, retail_price
        FROM inventory
        {where_clause}
    """, params)
    drugs = [dict(row) for row in cur.fetchall()]

    # 对每种药查询适应症
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
            if di not in indications_map:
                indications_map[di] = []
            indications_map[di].append(row["indication"])
        for d in drugs:
            d["indications"] = indications_map.get(d["drug_id"], [])

    return drugs


def _deduplicate_drugs(drugs):
    """按 drug_id 去重"""
    seen = set()
    result = []
    for d in drugs:
        if d["drug_id"] not in seen:
            seen.add(d["drug_id"])
            result.append(d)
    return result


@drug_bp.route("/drugs", methods=["GET"])
def list_drugs():
    name_filter = request.args.get("name")
    symptom_filter = request.args.get("symptom")

    # 防止过长的输入
    if name_filter is not None and len(name_filter) > 100:
        return (jsonify({
            "success": False, "ok": False,
            "error": "Name filter too long (max 100 characters)",
            "code": "INVALID_INPUT",
        }), 400)

    if symptom_filter is not None and len(symptom_filter) > 100:
        return (jsonify({
            "success": False, "ok": False,
            "error": "Symptom filter too long (max 100 characters)",
            "code": "INVALID_INPUT",
        }), 400)

    import re
    for f in [name_filter, symptom_filter]:
        if f is not None and re.search(r'[;\\\'"`]', f):
            return (jsonify({
                "success": False, "ok": False,
                "error": "Invalid characters in filter",
                "code": "INVALID_INPUT",
            }), 400)

    conn = None
    try:
        conn = get_db_connection()

        if symptom_filter is not None:
            # 第一层：直接用症状匹配适应症
            drugs = _query_drugs_base(conn,
                "WHERE drug_id IN (SELECT DISTINCT drug_id FROM drug_indications WHERE indication LIKE ?) AND quantity > 0",
                (f"%{symptom_filter}%",))

            # 第二层：如果没找到，查同义词表获取标准术语再匹配
            if not drugs:
                cur = conn.execute(
                    "SELECT DISTINCT standard_term FROM symptom_synonyms WHERE synonym LIKE ?",
                    (f"%{symptom_filter}%",),
                )
                standard_terms = [row["standard_term"] for row in cur.fetchall()]
                for term in standard_terms:
                    matched = _query_drugs_base(conn,
                        "WHERE drug_id IN (SELECT DISTINCT drug_id FROM drug_indications WHERE indication LIKE ?) AND quantity > 0",
                        (f"%{term}%",))
                    drugs.extend(matched)
                drugs = _deduplicate_drugs(drugs)

            response_data = {
                "success": True, "ok": True,
                "drugs": drugs, "data": drugs,
                "count": len(drugs),
                "filters": {"symptom": symptom_filter},
            }
            return jsonify(response_data)

        if name_filter is not None:
            drugs = _query_drugs_base(conn,
                "WHERE name LIKE ?", (f"%{name_filter}%",))
        else:
            drugs = _query_drugs_base(conn, "", [])

        response_data = {
            "success": True, "ok": True,
            "drugs": drugs, "data": drugs,
            "count": len(drugs),
            "filters": {"name": name_filter if name_filter is not None else ""},
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"Database error in list_drugs: {e}")
        return (jsonify({
            "success": False, "ok": False,
            "error": "Database error while fetching drugs",
            "code": "DB_ERROR",
        }), 500)
    finally:
        if conn:
            conn.close()


@drug_bp.route("/drugs/<int:drug_id>", methods=["GET"])
def get_drug(drug_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute(
            "SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id, category, is_prescription, retail_price FROM inventory WHERE drug_id = ?",
            (drug_id,),
        )
        row = cur.fetchone()
        if row is None:
            return (jsonify({
                "success": False, "ok": False,
                "error": f"Drug not found: id={drug_id}",
                "code": "DRUG_NOT_FOUND",
            }), 404)

        drug = dict(row)

        # 查询适应症
        cur = conn.execute(
            "SELECT indication FROM drug_indications WHERE drug_id = ?", (drug_id,))
        drug["indications"] = [r["indication"] for r in cur.fetchall()]

        return jsonify({"success": True, "drug": drug})
    except Exception as e:
        print(f"Database error in get_drug: {e}")
        return (jsonify({
            "success": False, "ok": False,
            "error": "Database error while fetching drug",
            "code": "DB_ERROR",
        }), 500)
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

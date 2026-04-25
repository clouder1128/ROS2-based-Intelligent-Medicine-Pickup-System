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

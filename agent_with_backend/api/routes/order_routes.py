"""
Order Controller
Handles drug ordering, pickup, dispensing, and order history
"""

from flask import Blueprint, jsonify, request
from database.connection import get_db_connection
from ros_integration.bridge import publish_task
from database.helpers import validate_and_get_drug, find_drug_id_by_name

order_bp = Blueprint("order", __name__, url_prefix="/api")


def create_order_for_drug(conn, drug_id: int, quantity: int, drug: dict, publish_now: bool = True) -> tuple:
    try:
        cur = conn.execute(
            "UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?",
            (quantity, drug_id, quantity),
        )
        if cur.rowcount == 0:
            return None, f'Insufficient stock: {drug["name"]}, please refresh and retry'
        cur = conn.execute(
            "INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)",
            ("pending", drug_id, quantity),
        )
        task_id = cur.lastrowid
        if publish_now:
            publish_task(task_id, drug, quantity)
        return task_id, ""
    except Exception as e:
        return None, f"Failed to create order: {str(e)}"


@order_bp.route("/order", methods=["POST", "OPTIONS"])
def order():
    if request.method == "OPTIONS":
        return "", 204
    data = request.get_json(silent=True)
    if not data:
        return (jsonify({"success": False, "ok": False, "error": "Request body must be JSON", "code": "INVALID_JSON"}), 400)
    if not isinstance(data, list):
        data = [data]
    order_data = []
    for item in data:
        drug_id = item.get("id")
        num = item.get("num")
        if drug_id is None or num is None:
            return (jsonify({"success": False, "ok": False, "error": "Each item must include id and num", "code": "MISSING_FIELDS"}), 400)
        try:
            order_data.append((int(drug_id), int(num)))
        except (TypeError, ValueError):
            return (jsonify({"success": False, "ok": False, "error": "id and num must be integers", "code": "INVALID_TYPE"}), 400)
    if not order_data:
        return (jsonify({"success": False, "ok": False, "error": "Order is empty", "code": "EMPTY_ORDER"}), 400)
    tasks = []
    for drug_id, num in order_data:
        if num <= 0:
            return (jsonify({"success": False, "ok": False, "error": f"Drug {drug_id} quantity must be > 0", "code": "INVALID_QUANTITY"}), 400)
        drug, err = validate_and_get_drug(drug_id, num)
        if err:
            return (jsonify({"success": False, "ok": False, "error": err, "code": "DRUG_VALIDATION_FAILED"}), 400)
        tasks.append((drug_id, num, drug))
    conn = None
    try:
        conn = get_db_connection()
        task_ids = []
        for drug_id, num, drug in tasks:
            task_id, err = create_order_for_drug(conn, drug_id, num, drug, publish_now=False)
            if task_id is None:
                conn.rollback()
                return (jsonify({"success": False, "ok": False, "error": err, "code": "INSUFFICIENT_INVENTORY"}), 400)
            task_ids.append(task_id)
        conn.commit()
        for (drug_id, num, drug), task_id in zip(tasks, task_ids):
            publish_task(task_id, drug, num)
        return jsonify({"success": True, "ok": True, "task_ids": task_ids, "message": f"Dispatched {len(task_ids)} pickup tasks, inventory deducted"})
    except Exception as e:
        print(f"Database error in order function: {e}")
        if conn:
            conn.rollback()
        return (jsonify({"success": False, "ok": False, "error": "Database error while processing order", "code": "DB_ERROR"}), 500)
    finally:
        if conn:
            conn.close()


@order_bp.route("/pickup", methods=["POST"])
def pickup():
    data = request.get_json(silent=True)
    if not data:
        return (jsonify({"success": False, "ok": False, "error": "Request body must be JSON", "code": "INVALID_JSON"}), 400)
    drug_id = data.get("id")
    num = data.get("num")
    if drug_id is None or num is None:
        return (jsonify({"success": False, "ok": False, "error": "Missing id or num", "code": "MISSING_FIELDS"}), 400)
    try:
        drug_id, num = int(drug_id), int(num)
    except (TypeError, ValueError):
        return (jsonify({"success": False, "ok": False, "error": "id and num must be integers", "code": "INVALID_TYPE"}), 400)
    if num <= 0:
        return (jsonify({"success": False, "ok": False, "error": "num must be > 0", "code": "INVALID_QUANTITY"}), 400)
    drug, err = validate_and_get_drug(drug_id, num)
    if err:
        return (jsonify({"success": False, "ok": False, "error": err, "code": "DRUG_VALIDATION_FAILED"}), 400)
    conn = None
    try:
        conn = get_db_connection()
        task_id, err = create_order_for_drug(conn, drug_id, num, drug, publish_now=True)
        if task_id is None:
            conn.rollback()
            return (jsonify({"success": False, "ok": False, "error": err, "code": "INSUFFICIENT_INVENTORY"}), 400)
        conn.commit()
        return jsonify({"success": True, "ok": True, "task_id": task_id, "drug_id": drug_id, "name": drug["name"], "quantity": num, "shelve_id": drug["shelve_id"], "x": drug["shelf_x"], "y": drug["shelf_y"]})
    except Exception as e:
        print(f"Database error in pickup function: {e}")
        if conn:
            conn.rollback()
        return (jsonify({"success": False, "ok": False, "error": "Database error while processing pickup", "code": "DB_ERROR"}), 500)
    finally:
        if conn:
            conn.close()


@order_bp.route("/dispense", methods=["POST"])
def dispense():
    data = request.get_json(silent=True)
    if not data:
        return (jsonify({"success": False, "ok": False, "error": "Request body must be JSON", "code": "INVALID_JSON"}), 400)
    prescription_id = data.get("prescription_id")
    patient_name = data.get("patient_name")
    drugs = data.get("drugs")
    if not prescription_id or not patient_name or not drugs:
        return (jsonify({"success": False, "ok": False, "error": "Missing required fields: prescription_id, patient_name, drugs", "code": "MISSING_REQUIRED_FIELDS"}), 400)
    if not isinstance(drugs, list):
        return (jsonify({"success": False, "ok": False, "error": "drugs must be an array", "code": "INVALID_TYPE"}), 400)
    order_items = []
    for drug_item in drugs:
        drug_name = drug_item.get("name")
        quantity = drug_item.get("quantity", 1)
        if not drug_name:
            return (jsonify({"success": False, "ok": False, "error": "Drug missing name field", "code": "MISSING_FIELD"}), 400)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return (jsonify({"success": False, "ok": False, "error": f"Drug quantity must be > 0: {drug_name}", "code": "INVALID_QUANTITY"}), 400)
        except (TypeError, ValueError):
            return (jsonify({"success": False, "ok": False, "error": f"Drug quantity must be integer: {drug_name}", "code": "INVALID_TYPE"}), 400)
        drug_id = find_drug_id_by_name(drug_name)
        if not drug_id:
            return (jsonify({"success": False, "ok": False, "error": f"Drug not found: {drug_name}", "code": "DRUG_NOT_FOUND"}), 400)
        order_items.append((drug_id, quantity, drug_name))
    conn = None
    try:
        conn = get_db_connection()
        task_ids = []
        for drug_id, quantity, drug_name in order_items:
            drug, err = validate_and_get_drug(drug_id, quantity)
            if err:
                conn.rollback()
                return (jsonify({"success": False, "ok": False, "error": err, "code": "DRUG_VALIDATION_FAILED"}), 400)
            task_id, err = create_order_for_drug(conn, drug_id, quantity, drug, publish_now=False)
            if task_id is None:
                conn.rollback()
                return (jsonify({"success": False, "ok": False, "error": f"Insufficient stock: {drug_name}", "code": "INSUFFICIENT_INVENTORY"}), 400)
            task_ids.append(task_id)
        conn.commit()
        for (drug_id, quantity, drug_name), task_id in zip(order_items, task_ids):
            drug, _ = validate_and_get_drug(drug_id, quantity)
            if drug:
                publish_task(task_id, drug, quantity)
        return jsonify({"success": True, "ok": True, "prescription_id": prescription_id, "patient_name": patient_name, "task_ids": task_ids, "message": f"Prescription dispensed, created {len(task_ids)} pickup tasks", "mode": "real_api"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "ok": False, "error": f"Dispense failed: {str(e)}", "code": "DISPENSE_ERROR", "mode": "error"})
    finally:
        if conn:
            conn.close()


@order_bp.route("/orders", methods=["GET"])
def list_orders():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.execute("""
            SELECT o.task_id, o.status, o.target_drug_id, o.quantity, o.created_at, i.name
            FROM order_log o
            LEFT JOIN inventory i ON o.target_drug_id = i.drug_id
            ORDER BY o.task_id DESC
            LIMIT 50
        """)
        rows = cur.fetchall()
        orders = [{"task_id": r[0], "status": r[1], "target_drug_id": r[2], "quantity": r[3], "created_at": r[4], "drug_name": r[5]} for r in rows]
        return jsonify({"success": True, "ok": True, "data": orders})
    except Exception as e:
        print(f"Database error in list_orders: {e}")
        return (jsonify({"success": False, "ok": False, "error": "Database error while fetching orders", "code": "DB_ERROR"}), 500)
    finally:
        if conn:
            conn.close()

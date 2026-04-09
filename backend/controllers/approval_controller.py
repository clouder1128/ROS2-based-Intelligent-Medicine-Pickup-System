"""
Approval Controller
Handles approval request creation, retrieval, and management
"""

from datetime import datetime
from flask import Blueprint, jsonify, request
from utils.database import get_db_connection
from utils.ros2_bridge import publish_task
from utils.drug_helpers import validate_and_get_drug, find_drug_id_by_name

# Create blueprint for approval routes
approval_bp = Blueprint('approval', __name__, url_prefix='/api')


@approval_bp.route('/approvals', methods=['POST'])
def create_approval():
    """Create a new approval request"""
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"success": False, "ok": False, "error": "Invalid JSON data provided", "code": "INVALID_JSON"}), 400

        # Validate required fields
        required_fields = ['patient_name', 'advice']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "ok": False,
                    "error": f"Missing required field: {field}",
                    "code": "MISSING_FIELD"
                }), 400

        # Import ApprovalManager
        from approval import get_approval_manager

        # Create approval
        manager = get_approval_manager()
        # Handle quantity field, ensure it's an integer, default to 1
        quantity = data.get('quantity', 1)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                quantity = 1  # Quantity must be > 0, otherwise use default
        except (TypeError, ValueError):
            quantity = 1  # Use default if conversion fails

        approval_id = manager.create(
            patient_name=data['patient_name'],
            advice=data['advice'],
            patient_age=data.get('patient_age'),
            patient_weight=data.get('patient_weight'),
            symptoms=data.get('symptoms'),
            drug_name=data.get('drug_name'),
            drug_type=data.get('drug_type'),
            quantity=quantity
        )

        return jsonify({
            "success": True,
            "approval_id": approval_id,
            "message": "Approval created successfully",
            "created_at": datetime.now().isoformat()
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "ok": False,
            "error": f"Failed to create approval: {str(e)}",
            "code": "CREATION_ERROR"
        }), 500


@approval_bp.route('/approvals/<approval_id>', methods=['GET'])
def get_approval(approval_id):
    """Get approval details by ID"""
    try:
        from approval import get_approval_manager

        manager = get_approval_manager()
        approval = manager.get(approval_id)

        if not approval:
            return jsonify({
                "success": False,
                "ok": False,
                "error": f"Approval not found: {approval_id}",
                "code": "NOT_FOUND"
            }), 404

        # Convert SQLite Row to dict if needed
        if hasattr(approval, 'keys'):
            approval = dict(approval)

        # Rename 'id' to 'approval_id' for API consistency
        if 'id' in approval:
            approval['approval_id'] = approval.pop('id')

        return jsonify({
            "success": True,
            "approval": approval
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "ok": False,
            "error": f"Failed to get approval: {str(e)}",
            "code": "RETRIEVAL_ERROR"
        }), 500


@approval_bp.route('/approvals/pending', methods=['GET'])
def get_pending_approvals():
    """Get list of pending approvals"""
    try:
        from approval import get_approval_manager

        manager = get_approval_manager()
        limit = request.args.get('limit', default=100, type=int)
        pending = manager.list_pending(limit=limit)

        # Convert SQLite Rows to dicts
        approvals = []
        for item in pending:
            if hasattr(item, 'keys'):
                approvals.append(dict(item))
            else:
                approvals.append(item)

        # Rename 'id' to 'approval_id' for API consistency
        for approval in approvals:
            if 'id' in approval:
                approval['approval_id'] = approval.pop('id')

        return jsonify({
            "success": True,
            "approvals": approvals,
            "count": len(approvals),
            "limit": limit
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "ok": False,
            "error": f"Failed to get pending approvals: {str(e)}",
            "code": "RETRIEVAL_ERROR"
        }), 500


@approval_bp.route('/approvals/<approval_id>/approve', methods=['POST'])
def approve_approval(approval_id):
    """Approve an approval request"""
    try:
        data = request.get_json()
        if not data or 'doctor_id' not in data:
            return jsonify({
                "success": False,
                "ok": False,
                "error": "Missing doctor_id in request",
                "code": "MISSING_DOCTOR_ID"
            }), 400

        from approval import get_approval_manager

        manager = get_approval_manager()
        notes = data.get('notes')
        success = manager.approve(approval_id, data['doctor_id'], notes=notes)

        if not success:
            return jsonify({
                "success": False,
                "ok": False,
                "error": f"Cannot approve approval {approval_id}. It may not exist or not be pending.",
                "code": "APPROVAL_FAILED"
            }), 400

        # Automatically create order after successful approval
        order_created = False
        order_message = ""
        task_id = None
        try:
            # Get approval details
            approval = manager.get(approval_id)
            if approval and approval.get('drug_name'):
                drug_name = approval['drug_name']
                quantity = approval.get('quantity', 1)

                # Use multi-level matching strategy to find drug ID
                drug_id = find_drug_id_by_name(drug_name)

                if drug_id:
                    # Validate drug
                    drug, err = validate_and_get_drug(drug_id, quantity)
                    if not err:
                        conn = None
                        try:
                            conn = get_db_connection()
                            # Atomic inventory deduction
                            cur = conn.execute(
                                'UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?',
                                (quantity, drug_id, quantity)
                            )
                            if cur.rowcount > 0:
                                # Write to order_log
                                cur = conn.execute(
                                    'INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)',
                                    ('pending', drug_id, quantity)
                                )
                                task_id = cur.lastrowid
                                conn.commit()
                                # Publish ROS2 task
                                publish_task(task_id, drug, quantity)
                                order_created = True
                                order_message = f"订单创建成功，任务ID: {task_id}，数量: {quantity}"
                            else:
                                order_message = f"库存不足，需要{quantity}个，库存不足"
                        except Exception as db_error:
                            order_message = f"数据库错误: {str(db_error)}"
                            if conn:
                                conn.rollback()
                        finally:
                            if conn:
                                conn.close()
                    else:
                        order_message = f"药品验证失败: {err}"
                else:
                    order_message = f"未找到药品: {drug_name}"
            else:
                order_message = "审批单未指定药品名称"
        except Exception as e:
            order_message = f"订单创建过程中出错: {str(e)}"
            # Doesn't affect approval success, just log error

        # Return approval success, including order creation status
        response_data = {
            "success": True,
            "message": "Approval approved successfully",
            "approval_id": approval_id,
            "doctor_id": data['doctor_id'],
            "approved_at": datetime.now().isoformat(),
            "order_created": order_created,
            "order_message": order_message
        }
        if notes:
            response_data['notes'] = notes
        if task_id:
            response_data["task_id"] = task_id
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "ok": False,
            "error": f"Failed to approve approval: {str(e)}",
            "code": "APPROVAL_ERROR"
        }), 500


@approval_bp.route('/approvals/<approval_id>/reject', methods=['POST'])
def reject_approval(approval_id):
    """Reject an approval request"""
    try:
        data = request.get_json()
        if not data or 'doctor_id' not in data:
            return jsonify({
                "success": False,
                "ok": False,
                "error": "Missing doctor_id in request",
                "code": "MISSING_DOCTOR_ID"
            }), 400

        if 'reason' not in data:
            return jsonify({
                "success": False,
                "ok": False,
                "error": "Missing rejection reason",
                "code": "MISSING_REASON"
            }), 400

        from approval import get_approval_manager

        manager = get_approval_manager()
        success = manager.reject(approval_id, data['doctor_id'], data['reason'])

        if not success:
            return jsonify({
                "success": False,
                "ok": False,
                "error": f"Cannot reject approval {approval_id}. It may not exist or not be pending.",
                "code": "REJECTION_FAILED"
            }), 400

        return jsonify({
            "success": True,
            "message": "Approval rejected successfully",
            "approval_id": approval_id,
            "doctor_id": data['doctor_id'],
            "reason": data['reason'],
            "rejected_at": datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "ok": False,
            "error": f"Failed to reject approval: {str(e)}",
            "code": "REJECTION_ERROR"
        }), 500
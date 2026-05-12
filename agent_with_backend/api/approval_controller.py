"""
Approval Controller
Handles approval request creation, retrieval, and management
"""

from datetime import datetime
from flask import Blueprint, jsonify, request
from common.utils.database import get_db_connection
from ros_integration.bridge import publish_task
from common.utils.drug_helpers import validate_and_get_drug, find_drug_id_by_name
from database.approval_manager import get_approval_manager

from auth.constants import (
    PERM_APPROVE_APPROVAL,
    PERM_READ_APPROVAL,
    PERM_REJECT_APPROVAL,
)
from auth.middleware import require_auth, require_permission
from common.config import Config
from agent.session.manager import SessionManager

_session_manager = SessionManager()

approval_bp = Blueprint("approval", __name__, url_prefix="/api")


@approval_bp.route("/approvals", methods=["POST"])
@require_auth
def create_approval():
    try:
        data = request.get_json(silent=True)
        if data is None:
            return (jsonify({"success": False, "ok": False, "error": "Invalid JSON data provided", "code": "INVALID_JSON"}), 400)

        required_fields = ["patient_name", "advice"]
        for field in required_fields:
            if field not in data:
                return (jsonify({"success": False, "ok": False, "error": f"Missing required field: {field}", "code": "MISSING_FIELD"}), 400)

        manager = get_approval_manager()
        quantity = data.get("quantity", 1)
        try:
            quantity = int(quantity)
            if quantity <= 0:
                quantity = 1
        except (TypeError, ValueError):
            quantity = 1

        approval_id = manager.create(
            patient_name=data["patient_name"],
            advice=data["advice"],
            patient_age=data.get("patient_age"),
            patient_weight=data.get("patient_weight"),
            symptoms=data.get("symptoms"),
            drug_name=data.get("drug_name"),
            drug_type=data.get("drug_type"),
            quantity=quantity,
        )

        return (jsonify({"success": True, "approval_id": approval_id, "message": "Approval created successfully", "created_at": datetime.now().isoformat()}), 201)

    except Exception as e:
        return (jsonify({"success": False, "ok": False, "error": f"Failed to create approval: {str(e)}", "code": "CREATION_ERROR"}), 500)


@approval_bp.route("/approvals/<approval_id>", methods=["GET"])
@require_auth
def get_approval(approval_id):
    try:
        manager = get_approval_manager()
        approval = manager.get(approval_id)

        if not approval:
            return (jsonify({"success": False, "ok": False, "error": f"Approval not found: {approval_id}", "code": "NOT_FOUND"}), 404)

        # 权限：有 read:approval 的（医生/管理员）可查看任意审批
        #       患者只能查看自己的审批（patient_name 匹配当前用户的 display_name）
        user = request.auth_user
        if PERM_READ_APPROVAL not in user.get("permissions", []):
            conn = get_db_connection()
            try:
                row = conn.execute(
                    "SELECT display_name FROM auth_users WHERE id = ?", (user["id"],)
                ).fetchone()
                if not row:
                    return (jsonify({"success": False, "error": "用户不存在", "code": "AUTH_003"}), 401)
                display_name = (row["display_name"] or "").strip() or user["username"]
                if str(approval.get("patient_name", "")).strip() != display_name:
                    return (jsonify({"success": False, "error": "权限不足", "code": "AUTH_403"}), 403)
            finally:
                conn.close()

        if hasattr(approval, "keys"):
            approval = dict(approval)

        if "id" in approval:
            approval["approval_id"] = approval.pop("id")

        return jsonify({"success": True, "approval": approval}), 200

    except Exception as e:
        return (jsonify({"success": False, "ok": False, "error": f"Failed to get approval: {str(e)}", "code": "RETRIEVAL_ERROR"}), 500)


@approval_bp.route("/approvals/pending", methods=["GET"])
@require_permission(PERM_READ_APPROVAL)
def get_pending_approvals():
    try:
        manager = get_approval_manager()
        limit = request.args.get("limit", default=100, type=int)
        pending = manager.list_pending(limit=limit)

        approvals = []
        for item in pending:
            if hasattr(item, "keys"):
                approvals.append(dict(item))
            else:
                approvals.append(item)

        for approval in approvals:
            if "id" in approval:
                approval["approval_id"] = approval.pop("id")

        return (jsonify({"success": True, "approvals": approvals, "count": len(approvals), "limit": limit}), 200)

    except Exception as e:
        return (jsonify({"success": False, "ok": False, "error": f"Failed to get pending approvals: {str(e)}", "code": "RETRIEVAL_ERROR"}), 500)


@approval_bp.route("/approvals/<approval_id>/approve", methods=["POST"])
@require_permission(PERM_APPROVE_APPROVAL)
def approve_approval(approval_id):
    try:
        data = request.get_json()
        if not data or "doctor_id" not in data:
            return (jsonify({"success": False, "ok": False, "error": "Missing doctor_id in request", "code": "MISSING_DOCTOR_ID"}), 400)

        manager = get_approval_manager()
        notes = data.get("notes")
        success = manager.approve(approval_id, data["doctor_id"], notes=notes)

        if not success:
            return (jsonify({"success": False, "ok": False, "error": f"Cannot approve approval {approval_id}. It may not exist or not be pending.", "code": "APPROVAL_FAILED"}), 400)

        order_created = False
        order_message = ""
        task_id = None
        try:
            approval = manager.get(approval_id)
            if approval and approval.get("drug_name"):
                drug_name = approval["drug_name"]
                quantity = approval.get("quantity", 1)

                drug_id = find_drug_id_by_name(drug_name)

                if drug_id:
                    drug, err = validate_and_get_drug(drug_id, quantity)
                    if not err:
                        conn = None
                        try:
                            conn = get_db_connection()
                            cur = conn.execute(
                                "UPDATE inventory SET quantity = quantity - ? WHERE drug_id = ? AND quantity >= ?",
                                (quantity, drug_id, quantity),
                            )
                            if cur.rowcount > 0:
                                cur = conn.execute(
                                    "INSERT INTO order_log (status, target_drug_id, quantity) VALUES (?, ?, ?)",
                                    ("pending", drug_id, quantity),
                                )
                                task_id = cur.lastrowid
                                conn.commit()
                                publish_task(task_id, drug, quantity)
                                manager.set_task_id(approval_id, str(task_id))
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

        response_data = {
            "success": True,
            "message": "Approval approved successfully",
            "approval_id": approval_id,
            "doctor_id": data["doctor_id"],
            "approved_at": datetime.now().isoformat(),
            "order_created": order_created,
            "order_message": order_message,
        }
        if notes:
            response_data["notes"] = notes
        if task_id:
            response_data["task_id"] = task_id
        return jsonify(response_data), 200

    except Exception as e:
        return (jsonify({"success": False, "ok": False, "error": f"Failed to approve approval: {str(e)}", "code": "APPROVAL_ERROR"}), 500)


@approval_bp.route("/approvals/<approval_id>/reject", methods=["POST"])
@require_permission(PERM_REJECT_APPROVAL)
def reject_approval(approval_id):
    try:
        data = request.get_json()
        if not data or "doctor_id" not in data:
            return (jsonify({"success": False, "ok": False, "error": "Missing doctor_id in request", "code": "MISSING_DOCTOR_ID"}), 400)

        if "reason" not in data:
            return (jsonify({"success": False, "ok": False, "error": "Missing rejection reason", "code": "MISSING_REASON"}), 400)

        manager = get_approval_manager()
        success = manager.reject(approval_id, data["doctor_id"], data["reason"])

        if not success:
            return (jsonify({"success": False, "ok": False, "error": f"Cannot reject approval {approval_id}. It may not exist or not be pending.", "code": "REJECTION_FAILED"}), 400)

        return (jsonify({"success": True, "message": "Approval rejected successfully", "approval_id": approval_id, "doctor_id": data["doctor_id"], "reason": data["reason"], "rejected_at": datetime.now().isoformat()}), 200)

    except Exception as e:
        return (jsonify({"success": False, "ok": False, "error": f"Failed to reject approval: {str(e)}", "code": "REJECTION_ERROR"}), 500)


# ────────────────────────────────────────────
#  AI 医疗咨询（由 MedicalAgent 驱动）
# ────────────────────────────────────────────


def _check_llm_ready():
    """检查 LLM 是否已配置，未配置时返回 (False, 错误信息)"""
    if Config.LLM_PROVIDER == "claude" and not Config.ANTHROPIC_API_KEY:
        return False, "ANTHROPIC_API_KEY 未配置，AI 咨询不可用。请在 .env 中设置 API Key。"
    if Config.LLM_PROVIDER == "openai" and not Config.OPENAI_API_KEY:
        return False, "OPENAI_API_KEY 未配置，AI 咨询不可用。请在 .env 中设置 API Key。"
    return True, ""


@approval_bp.route("/consultation", methods=["POST"])
@require_auth
def consultation():
    """
    POST /api/consultation
    多轮 AI 医疗咨询。由 MedicalAgent 驱动完整流程：
      症状提取 → 药品查询 → 过敏检查 → 剂量计算 → 生成建议 → 提交审批

    Request:  { "message": "我头痛发热", "patient_id": "optional" }
    Response: { "success": true, "reply": "...", "approval_id": "AP-xxx" | null,
                "workflow_completed": false }

    多轮对话：同一 patient_id 自动保持会话上下文。
    当 workflow_completed=true 且 approval_id 不为空时，审批已自动提交。
    """
    ready, err = _check_llm_ready()
    if not ready:
        return jsonify({"success": False, "error": err, "code": "LLM_NOT_CONFIGURED"}), 400

    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"success": False, "error": "Missing 'message' field", "code": "MISSING_FIELD"}), 400

    message = data["message"]
    user = request.auth_user
    patient_id = data.get("patient_id") or user.get("username") or str(user.get("id"))

    try:
        agent = _session_manager.get_agent(patient_id)
        # 从 auth_users 查询 display_name，用于覆写 submit_approval 的 patient_name
        _conn = get_db_connection()
        try:
            _row = _conn.execute(
                "SELECT display_name FROM auth_users WHERE id = ?", (user["id"],)
            ).fetchone()
            agent.patient_display_name = (
                (_row["display_name"] or "").strip() if _row else ""
            ) or user.get("username", "")
        finally:
            _conn.close()
        reply, steps = agent.run(message, patient_id)
        approval_id = agent.get_approval_id()

        return jsonify({
            "success": True,
            "reply": reply,
            "approval_id": approval_id,
            "drug_name": getattr(agent, "drug_name", None),
            "quantity": getattr(agent, "quantity", None),
            "workflow_completed": agent.workflow_completed,
            "steps_count": len(steps),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"咨询处理异常: {str(e)}",
            "code": "CONSULTATION_ERROR",
        }), 500


@approval_bp.route("/consultation/reset", methods=["POST"])
@require_auth
def reset_consultation():
    """重置当前患者的对话会话"""
    user = request.auth_user
    patient_id = user.get("username") or str(user.get("id"))
    _session_manager.delete_session(patient_id)
    return jsonify({"success": True, "message": "会话已重置"})


@approval_bp.route("/approvals/<approval_id>/complete", methods=["POST"])
@require_auth
def complete_approval(approval_id):
    """患者确认取药后，标记审批单为已完成"""
    try:
        manager = get_approval_manager()
        success = manager.mark_completed(approval_id)

        if not success:
            return jsonify({
                "success": False,
                "error": f"无法完成审批 {approval_id}，它可能不存在或状态不是 approved",
                "code": "COMPLETE_FAILED",
            }), 400

        return jsonify({
            "success": True,
            "message": "审批单已标记为已完成",
            "approval_id": approval_id,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"标记审批完成失败: {str(e)}",
            "code": "COMPLETE_ERROR",
        }), 500

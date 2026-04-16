"""
主要API路由 - 患者咨询、医生审批、处方查询等
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# 导入P1的MedicalAgent
try:
    from P1.core.agent import MedicalAgent
    P1_AVAILABLE = True
except ImportError:
    P1_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("P1 MedicalAgent模块不可用，使用Mock模式")

# 导入P6的审批模块
try:
    from test.backend.approval import get_approval_manager
    P6_AVAILABLE = True
except ImportError:
    P6_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("P6审批模块不可用，使用Mock模式")

# 导入P2的配药工具
try:
    from P1.tools.medical import fill_prescription_sync as fill_prescription
    P2_AVAILABLE = True
except ImportError:
    P2_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("P2配药工具不可用，使用Mock模式")

router = APIRouter()

# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="患者描述的症状或问题")
    patient_id: str = Field("anonymous", description="患者ID，默认为anonymous")
    patient_name: Optional[str] = Field(None, description="患者姓名")

class ChatResponse(BaseModel):
    """聊天响应模型"""
    reply: str = Field(..., description="AI助手的回复")
    steps: List[dict] = Field([], description="AI执行的步骤记录")
    approval_id: Optional[str] = Field(None, description="如果提交了审批，返回审批ID")
    conversation_id: Optional[str] = Field(None, description="会话ID，用于多轮对话")

class ApprovalRequest(BaseModel):
    """审批请求模型"""
    approval_id: str = Field(..., description="审批单ID")
    doctor_id: str = Field(..., description="医生ID")
    action: str = Field(..., description="审批动作：approve或reject")
    reject_reason: Optional[str] = Field(None, description="拒绝原因（如果action为reject）")

class ApprovalResponse(BaseModel):
    """审批响应模型"""
    status: str = Field(..., description="审批结果状态")
    dispense_result: Optional[str] = Field(None, description="配药结果（如果审批通过）")
    message: str = Field(..., description="操作结果描述")

class PendingApproval(BaseModel):
    """待审批项模型"""
    id: str = Field(..., description="审批单ID")
    patient_name: str = Field(..., description="患者姓名")
    symptoms: Optional[str] = Field(None, description="症状描述")
    advice: str = Field(..., description="AI建议文本")
    drug_name: Optional[str] = Field(None, description="药品名称")
    created_at: str = Field(..., description="创建时间")

# ==================== 聊天端点 ====================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    患者与AI医疗助手聊天
    - 调用P1的MedicalAgent处理患者咨询
    - 如果AI建议用药，会自动提交审批
    """
    if not P1_AVAILABLE:
        # Mock响应
        return ChatResponse(
            reply="[Mock] 我是AI医疗助手，当前系统正在维护中。",
            steps=[{"type": "mock", "content": "使用Mock数据"}],
            approval_id="AP-MOCK-001"
        )

    try:
        # 创建MedicalAgent实例
        agent = MedicalAgent()

        # 运行Agent处理用户消息
        reply, steps = agent.run(request.message, patient_id=request.patient_id)

        # 获取审批ID（如果Agent提交了审批）
        approval_id = agent.get_approval_id()

        return ChatResponse(
            reply=reply,
            steps=steps,
            approval_id=approval_id,
            conversation_id=request.patient_id
        )
    except Exception as e:
        logger.error(f"Agent处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"Agent处理失败: {str(e)}")

# ==================== 审批端点 ====================

@router.get("/pending", response_model=List[PendingApproval])
async def get_pending_approvals(
    doctor_id: Optional[str] = Query(None, description="医生ID，可选过滤")
):
    """获取待审批列表"""
    if not P6_AVAILABLE:
        # Mock数据
        return [
            PendingApproval(
                id="AP-MOCK-001",
                patient_name="张三",
                symptoms="头痛、发烧",
                advice="建议服用布洛芬200mg，每日3次",
                drug_name="布洛芬",
                created_at="2026-04-15T10:00:00Z"
            ),
            PendingApproval(
                id="AP-MOCK-002",
                patient_name="李四",
                symptoms="咳嗽、流鼻涕",
                advice="建议服用阿莫西林500mg，每日3次",
                drug_name="阿莫西林",
                created_at="2026-04-15T11:00:00Z"
            )
        ]

    try:
        approval_manager = get_approval_manager()
        pending_list = approval_manager.list_pending(limit=100)

        # 转换为响应模型
        result = []
        for item in pending_list:
            result.append(PendingApproval(
                id=item.get("id", ""),
                patient_name=item.get("patient_name", ""),
                symptoms=item.get("symptoms"),
                advice=item.get("advice", ""),
                drug_name=item.get("drug_name"),
                created_at=item.get("created_at", "")
            ))

        return result
    except Exception as e:
        logger.error(f"获取待审批列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取待审批列表失败: {str(e)}")

@router.post("/approve", response_model=ApprovalResponse)
async def approve_prescription(request: ApprovalRequest):
    """
    医生审批处方
    - 如果审批通过，自动调用P2的fill_prescription进行配药
    - 这是整个系统的关键集成点
    """
    if not P6_AVAILABLE:
        # Mock响应
        return ApprovalResponse(
            status="approved" if request.action == "approve" else "rejected",
            dispense_result="[Mock] 配药成功！取药码：MOCK-123456",
            message=f"[Mock] 处方已{'批准' if request.action == 'approve' else '拒绝'}"
        )

    try:
        approval_manager = get_approval_manager()

        if request.action == "approve":
            # 审批通过
            success = approval_manager.approve(request.approval_id, request.doctor_id)
            if not success:
                raise HTTPException(status_code=400, detail="审批失败，可能审批单不存在或状态不正确")

            # TODO: 获取处方数据（需要从审批单关联的处方表中查询）
            # 目前使用Mock数据
            prescription_data = {
                "id": request.approval_id.replace("AP-", "RX-"),
                "patient_name": "张三",  # 应从数据库查询
                "drugs": [
                    {"name": "布洛芬", "dosage": "200mg", "quantity": 2}
                ]
            }

            # 调用P2的配药工具
            dispense_result = ""
            if P2_AVAILABLE:
                try:
                    # 调用同步版本（fill_prescription_sync）
                    result = fill_prescription(
                        prescription_data["id"],
                        prescription_data["patient_name"],
                        prescription_data["drugs"]
                    )
                    dispense_result = result
                except Exception as e:
                    logger.error(f"配药工具调用失败: {e}")
                    dispense_result = f"配药工具调用失败: {str(e)}"
            else:
                dispense_result = "[Mock] 配药成功！取药码：MOCK-123456"

            return ApprovalResponse(
                status="approved",
                dispense_result=dispense_result,
                message="处方已批准并触发配药"
            )

        elif request.action == "reject":
            # 审批拒绝
            if not request.reject_reason:
                raise HTTPException(status_code=400, detail="拒绝审批必须提供原因")

            success = approval_manager.reject(
                request.approval_id,
                request.doctor_id,
                request.reject_reason
            )
            if not success:
                raise HTTPException(status_code=400, detail="拒绝审批失败")

            return ApprovalResponse(
                status="rejected",
                message=f"处方已拒绝：{request.reject_reason}"
            )

        else:
            raise HTTPException(status_code=400, detail="action必须是approve或reject")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"审批处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"审批处理失败: {str(e)}")

# ==================== 处方和历史查询 ====================

@router.get("/prescription/{prescription_id}")
async def get_prescription(prescription_id: str):
    """查询处方状态和取药码"""
    # TODO: 连接数据库查询处方信息
    return {
        "id": prescription_id,
        "status": "dispensed",
        "pickup_code": "PICKUP-MOCK-123456",
        "patient_name": "张三",
        "drugs": [{"name": "布洛芬", "dosage": "200mg", "quantity": 2}],
        "created_at": "2026-04-15T10:30:00Z",
        "dispensed_at": "2026-04-15T10:35:00Z"
    }

@router.get("/history")
async def get_patient_history(
    patient_name: Optional[str] = Query(None, description="患者姓名"),
    patient_id: Optional[str] = Query(None, description="患者ID")
):
    """查询患者用药历史"""
    # TODO: 连接数据库查询历史记录
    return {
        "patient": patient_name or patient_id or "unknown",
        "history": [
            {
                "prescription_id": "RX-MOCK-001",
                "drugs": "布洛芬 200mg × 2",
                "advice": "饭后服用，每日3次",
                "date": "2026-04-14",
                "status": "completed"
            }
        ]
    }

# ==================== 系统信息 ====================

@router.get("/system/info")
async def get_system_info():
    """获取系统模块状态信息"""
    return {
        "modules": {
            "P1_MedicalAgent": P1_AVAILABLE,
            "P2_PharmacyIntegration": P2_AVAILABLE,
            "P6_ApprovalManager": P6_AVAILABLE
        },
        "config": {
            "llm_provider": "claude" if P1_AVAILABLE else "unknown",
            "pharmacy_url": "http://localhost:8001" if P2_AVAILABLE else "unknown"
        }
    }
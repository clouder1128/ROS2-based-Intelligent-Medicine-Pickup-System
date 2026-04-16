"""
Pydantic 数据模型定义 - 用于API请求/响应验证
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator

# ==================== 基础模型 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")

# ==================== 聊天相关模型 ====================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=1000, description="患者描述的症状或问题")
    patient_id: str = Field("anonymous", description="患者ID，用于会话跟踪")
    patient_name: Optional[str] = Field(None, description="患者姓名")
    session_id: Optional[str] = Field(None, description="会话ID，用于恢复多轮对话")

    @validator("message")
    def validate_message(cls, v):
        """验证消息内容"""
        v = v.strip()
        if len(v) < 1:
            raise ValueError("消息不能为空")
        if len(v) > 1000:
            raise ValueError("消息过长，请简化描述")
        return v

class ChatStep(BaseModel):
    """聊天步骤模型"""
    step: int = Field(..., description="步骤序号")
    type: str = Field(..., description="步骤类型：assistant/tool_call")
    content: Optional[str] = Field(None, description="内容（如果是assistant回复）")
    tool: Optional[str] = Field(None, description="工具名称（如果是工具调用）")
    input: Optional[Dict[str, Any]] = Field(None, description="工具输入参数")
    result: Optional[str] = Field(None, description="工具执行结果")
    duration_ms: Optional[int] = Field(None, description="执行耗时（毫秒）")
    error: Optional[str] = Field(None, description="错误信息")

class ChatResponse(BaseResponse):
    """聊天响应模型"""
    reply: str = Field(..., description="AI助手的回复")
    steps: List[ChatStep] = Field([], description="AI执行的步骤记录")
    approval_id: Optional[str] = Field(None, description="如果提交了审批，返回审批ID")
    conversation_id: Optional[str] = Field(None, description="会话ID，用于后续对话")
    workflow_state: Optional[Dict[str, Any]] = Field(None, description="工作流状态")

# ==================== 审批相关模型 ====================

class ApprovalRequest(BaseModel):
    """审批请求模型"""
    approval_id: str = Field(..., description="审批单ID")
    doctor_id: str = Field(..., description="医生ID")
    action: str = Field(..., description="审批动作：approve或reject")
    reject_reason: Optional[str] = Field(None, description="拒绝原因（如果action为reject）")

    @validator("action")
    def validate_action(cls, v):
        """验证action值"""
        if v not in ["approve", "reject"]:
            raise ValueError("action必须是approve或reject")
        return v

    @validator("reject_reason")
    def validate_reject_reason(cls, v, values):
        """验证拒绝原因"""
        if values.get("action") == "reject" and not v:
            raise ValueError("拒绝审批必须提供原因")
        return v

class ApprovalResponse(BaseResponse):
    """审批响应模型"""
    status: str = Field(..., description="审批结果状态：approved/rejected")
    dispense_result: Optional[str] = Field(None, description="配药结果（如果审批通过）")
    pickup_code: Optional[str] = Field(None, description="取药码（如果配药成功）")
    prescription_id: Optional[str] = Field(None, description="处方ID")

class PendingApproval(BaseModel):
    """待审批项模型"""
    id: str = Field(..., description="审批单ID")
    patient_name: str = Field(..., description="患者姓名")
    patient_age: Optional[int] = Field(None, description="患者年龄")
    patient_weight: Optional[float] = Field(None, description="患者体重（kg）")
    symptoms: Optional[str] = Field(None, description="症状描述")
    advice: str = Field(..., description="AI建议文本")
    drug_name: Optional[str] = Field(None, description="药品名称")
    drug_type: Optional[str] = Field(None, description="药品类型：prescription/otc")
    created_at: str = Field(..., description="创建时间（ISO格式）")
    urgency: Optional[str] = Field(None, description="紧急程度：high/medium/low")

# ==================== 处方相关模型 ====================

class DrugItem(BaseModel):
    """药品项模型"""
    name: str = Field(..., description="药品名称")
    dosage: str = Field(..., description="用法用量")
    quantity: int = Field(..., ge=1, description="数量")

class PrescriptionInfo(BaseModel):
    """处方信息模型"""
    id: str = Field(..., description="处方ID")
    approval_id: str = Field(..., description="关联的审批单ID")
    patient_name: str = Field(..., description="患者姓名")
    drugs: List[DrugItem] = Field(..., description="药品列表")
    status: str = Field(..., description="状态：pending/dispensed/cancelled")
    created_at: str = Field(..., description="创建时间")
    dispensed_at: Optional[str] = Field(None, description="配药时间")
    pickup_code: Optional[str] = Field(None, description="取药码")
    pharmacy_note: Optional[str] = Field(None, description="药房备注")

class PrescriptionResponse(BaseResponse):
    """处方查询响应"""
    prescription: PrescriptionInfo = Field(..., description="处方信息")

class HistoryItem(BaseModel):
    """用药历史项"""
    prescription_id: str = Field(..., description="处方ID")
    patient_name: str = Field(..., description="患者姓名")
    drugs: List[DrugItem] = Field(..., description="药品列表")
    advice: str = Field(..., description="用药建议")
    created_at: str = Field(..., description="创建时间")
    status: str = Field(..., description="状态")
    pickup_code: Optional[str] = Field(None, description="取药码")

class HistoryResponse(BaseResponse):
    """历史查询响应"""
    patient: str = Field(..., description="患者姓名或ID")
    history: List[HistoryItem] = Field([], description="用药历史记录")

# ==================== 管理员模型 ====================

class DrugCreateRequest(BaseModel):
    """药品创建请求"""
    name: str = Field(..., min_length=1, max_length=100, description="药品名称")
    specification: str = Field(..., description="规格，如'500mg/片'")
    price: float = Field(0.0, ge=0, description="价格")
    stock: int = Field(0, ge=0, description="初始库存")
    is_prescription: bool = Field(True, description="是否为处方药")
    min_stock_threshold: int = Field(50, ge=1, description="库存下限阈值")
    indications: Optional[List[str]] = Field(None, description="适应症列表")
    contraindications: Optional[List[str]] = Field(None, description="禁忌症列表")

class DrugUpdateRequest(BaseModel):
    """药品更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="药品名称")
    specification: Optional[str] = Field(None, description="规格")
    price: Optional[float] = Field(None, ge=0, description="价格")
    stock: Optional[int] = Field(None, ge=0, description="库存")
    is_prescription: Optional[bool] = Field(None, description="是否为处方药")
    min_stock_threshold: Optional[int] = Field(None, ge=1, description="库存下限阈值")

class DrugResponse(BaseResponse):
    """药品响应"""
    drug: Optional[Dict[str, Any]] = Field(None, description="药品信息")

class TransactionRequest(BaseModel):
    """出入库请求"""
    drug_id: int = Field(..., ge=1, description="药品ID")
    type: str = Field(..., description="类型：in（入库）或out（出库）")
    quantity: int = Field(..., ge=1, description="数量")
    reason: str = Field(..., description="原因，如'医生处方'、'管理员补货'")
    note: Optional[str] = Field(None, description="备注")

    @validator("type")
    def validate_type(cls, v):
        """验证类型"""
        if v not in ["in", "out"]:
            raise ValueError("type必须是in或out")
        return v

class ReportRequest(BaseModel):
    """报告查询请求"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    drug_id: Optional[int] = Field(None, description="药品ID（可选）")

class ReportItem(BaseModel):
    """报告项"""
    drug_name: str = Field(..., description="药品名称")
    in_quantity: int = Field(0, description="入库数量")
    out_quantity: int = Field(0, description="出库数量")
    start_stock: int = Field(0, description="期初库存")
    end_stock: int = Field(0, description="期末库存")

class ReportResponse(BaseResponse):
    """报告响应"""
    report: List[ReportItem] = Field([], description="报告数据")
    period: Dict[str, str] = Field(..., description="报告期间")

class PurchaseSuggestion(BaseModel):
    """采购建议"""
    drug_name: str = Field(..., description="药品名称")
    current_stock: int = Field(..., description="当前库存")
    daily_avg_out: float = Field(..., description="日均出库量")
    suggested_quantity: int = Field(..., description="建议采购数量")
    urgency: str = Field(..., description="紧急程度：high/medium/low")
    days_until_empty: Optional[float] = Field(None, description="预计库存耗尽天数")

# ==================== 系统状态模型 ====================

class ModuleStatus(BaseModel):
    """模块状态"""
    name: str = Field(..., description="模块名称")
    available: bool = Field(..., description="是否可用")
    version: Optional[str] = Field(None, description="版本")
    health: Optional[str] = Field(None, description="健康状态：healthy/warning/error")

class SystemInfo(BaseModel):
    """系统信息"""
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="版本")
    status: str = Field(..., description="状态：running/maintenance/stopped")
    modules: List[ModuleStatus] = Field([], description="模块状态")
    config_summary: Dict[str, Any] = Field({}, description="配置摘要")
    uptime: Optional[str] = Field(None, description="运行时间")

# ==================== 错误模型 ====================

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    detail: str = Field(..., description="错误详情")
    timestamp: str = Field(..., description="时间戳")
    trace_id: Optional[str] = Field(None, description="跟踪ID")

# ==================== 分页模型 ====================

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("asc", description="排序方向：asc/desc")

    @validator("sort_order")
    def validate_sort_order(cls, v):
        """验证排序方向"""
        if v and v not in ["asc", "desc"]:
            raise ValueError("sort_order必须是asc或desc")
        return v

class PaginatedResponse(BaseResponse):
    """分页响应"""
    data: List[Any] = Field([], description="数据列表")
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")
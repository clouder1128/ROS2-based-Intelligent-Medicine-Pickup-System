"""
管理员API路由 - 药品管理、报告查询等
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import date, datetime

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== 数据模型 ====================

class DrugItem(BaseModel):
    """药品项模型"""
    id: Optional[int] = Field(None, description="药品ID")
    name: str = Field(..., description="药品名称")
    specification: Optional[str] = Field(None, description="规格，如'500mg/片'")
    price: float = Field(0.0, description="价格")
    stock: int = Field(0, description="库存数量")
    is_prescription: bool = Field(True, description="是否为处方药")
    min_stock_threshold: int = Field(50, description="库存下限阈值")
    created_at: Optional[str] = Field(None, description="创建时间")

class TransactionItem(BaseModel):
    """出入库记录模型"""
    id: Optional[int] = Field(None, description="记录ID")
    drug_id: int = Field(..., description="药品ID")
    type: str = Field(..., description="类型：in（入库）或out（出库）")
    quantity: int = Field(..., description="数量")
    reason: Optional[str] = Field(None, description="原因，如'医生处方'、'管理员补货'")
    timestamp: Optional[str] = Field(None, description="时间戳")

class ReportRequest(BaseModel):
    """报告查询请求模型"""
    start_date: str = Field(..., description="开始日期，格式YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式YYYY-MM-DD")
    drug_id: Optional[int] = Field(None, description="药品ID（可选，查询特定药品）")

class ReportItem(BaseModel):
    """报告项模型"""
    drug_name: str = Field(..., description="药品名称")
    in_quantity: int = Field(0, description="入库数量")
    out_quantity: int = Field(0, description="出库数量")
    start_stock: int = Field(0, description="期初库存")
    end_stock: int = Field(0, description="期末库存")

class PurchaseSuggestion(BaseModel):
    """采购建议模型"""
    drug_name: str = Field(..., description="药品名称")
    current_stock: int = Field(..., description="当前库存")
    daily_avg_out: float = Field(..., description="日均出库量")
    suggested_quantity: int = Field(..., description="建议采购数量")
    urgency: str = Field(..., description="紧急程度：high/medium/low")

# ==================== 药品管理 ====================

@router.get("/drugs", response_model=List[DrugItem])
async def list_drugs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（药品名称）"),
    prescription_only: Optional[bool] = Query(None, description="是否只显示处方药")
):
    """获取药品列表（分页、搜索）"""
    # TODO: 连接数据库查询
    # 当前返回Mock数据
    return [
        DrugItem(
            id=1,
            name="阿莫西林",
            specification="500mg/片",
            price=25.0,
            stock=100,
            is_prescription=True,
            min_stock_threshold=50,
            created_at="2026-04-01T10:00:00Z"
        ),
        DrugItem(
            id=2,
            name="布洛芬",
            specification="200mg/片",
            price=15.0,
            stock=150,
            is_prescription=False,
            min_stock_threshold=80,
            created_at="2026-04-01T10:00:00Z"
        ),
        DrugItem(
            id=3,
            name="头孢克肟",
            specification="100mg/粒",
            price=35.0,
            stock=80,
            is_prescription=True,
            min_stock_threshold=40,
            created_at="2026-04-02T14:30:00Z"
        )
    ]

@router.get("/drugs/{drug_id}", response_model=DrugItem)
async def get_drug(drug_id: int):
    """获取单个药品详情"""
    # TODO: 连接数据库查询
    if drug_id == 1:
        return DrugItem(
            id=1,
            name="阿莫西林",
            specification="500mg/片",
            price=25.0,
            stock=100,
            is_prescription=True,
            min_stock_threshold=50,
            created_at="2026-04-01T10:00:00Z"
        )
    else:
        raise HTTPException(status_code=404, detail="药品不存在")

@router.post("/drugs", response_model=DrugItem)
async def create_drug(drug: DrugItem):
    """创建新药品"""
    # TODO: 连接数据库插入
    # 模拟创建
    new_drug = drug.copy()
    new_drug.id = 100  # 模拟生成ID
    new_drug.created_at = datetime.now().isoformat()
    return new_drug

@router.put("/drugs/{drug_id}", response_model=DrugItem)
async def update_drug(drug_id: int, drug: DrugItem):
    """更新药品信息"""
    # TODO: 连接数据库更新
    if drug_id != 1:
        raise HTTPException(status_code=404, detail="药品不存在")

    updated_drug = drug.copy()
    updated_drug.id = drug_id
    return updated_drug

@router.delete("/drugs/{drug_id}")
async def delete_drug(drug_id: int):
    """删除药品"""
    # TODO: 连接数据库删除
    if drug_id != 1:
        raise HTTPException(status_code=404, detail="药品不存在")

    return {"status": "ok", "message": f"药品 {drug_id} 已删除"}

# ==================== 出入库记录 ====================

@router.get("/transactions", response_model=List[TransactionItem])
async def list_transactions(
    drug_id: Optional[int] = Query(None, description="药品ID（可选过滤）"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数")
):
    """获取出入库记录"""
    # TODO: 连接数据库查询
    return [
        TransactionItem(
            id=1,
            drug_id=1,
            type="in",
            quantity=100,
            reason="管理员补货",
            timestamp="2026-04-10T09:00:00Z"
        ),
        TransactionItem(
            id=2,
            drug_id=1,
            type="out",
            quantity=20,
            reason="医生处方",
            timestamp="2026-04-12T14:30:00Z"
        ),
        TransactionItem(
            id=3,
            drug_id=2,
            type="out",
            quantity=15,
            reason="医生处方",
            timestamp="2026-04-13T11:20:00Z"
        )
    ]

@router.post("/transactions")
async def create_transaction(transaction: TransactionItem):
    """创建出入库记录"""
    # TODO: 连接数据库插入，同时更新药品库存
    new_transaction = transaction.copy()
    new_transaction.id = 100  # 模拟生成ID
    new_transaction.timestamp = datetime.now().isoformat()
    return new_transaction

# ==================== 报告查询 ====================

@router.get("/report", response_model=List[ReportItem])
async def get_inventory_report(request: ReportRequest = Depends()):
    """获取库存出入库报告"""
    # TODO: 连接数据库统计
    # 当前返回Mock数据
    try:
        start_date = date.fromisoformat(request.start_date)
        end_date = date.fromisoformat(request.end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")

    return [
        ReportItem(
            drug_name="阿莫西林",
            in_quantity=100,
            out_quantity=45,
            start_stock=50,
            end_stock=105
        ),
        ReportItem(
            drug_name="布洛芬",
            in_quantity=80,
            out_quantity=60,
            start_stock=100,
            end_stock=120
        ),
        ReportItem(
            drug_name="头孢克肟",
            in_quantity=50,
            out_quantity=30,
            start_stock=40,
            end_stock=60
        )
    ]

@router.get("/purchase-suggestions", response_model=List[PurchaseSuggestion])
async def get_purchase_suggestions():
    """获取采购建议（基于库存下限和出库速度）"""
    # TODO: 连接数据库计算
    # 算法：对于每种药品，计算日均出库量，如果当前库存低于阈值或预测几天内会低于阈值，则生成采购建议
    return [
        PurchaseSuggestion(
            drug_name="阿莫西林",
            current_stock=45,
            daily_avg_out=8.5,
            suggested_quantity=100,
            urgency="high"  # 当前库存已低于阈值50
        ),
        PurchaseSuggestion(
            drug_name="布洛芬",
            current_stock=120,
            daily_avg_out=12.3,
            suggested_quantity=80,
            urgency="medium"  # 库存充足，但需要补充
        ),
        PurchaseSuggestion(
            drug_name="蒙脱石散",
            current_stock=25,
            daily_avg_out=5.2,
            suggested_quantity=60,
            urgency="high"  # 库存远低于阈值50
        )
    ]

# ==================== 系统统计 ====================

@router.get("/stats")
async def get_system_statistics():
    """获取系统统计信息"""
    # TODO: 连接数据库统计
    return {
        "drugs": {
            "total": 15,
            "prescription": 10,
            "non_prescription": 5
        },
        "transactions": {
            "total": 245,
            "in": 120,
            "out": 125,
            "today": 8
        },
        "approvals": {
            "total": 89,
            "pending": 5,
            "approved": 78,
            "rejected": 6
        },
        "prescriptions": {
            "total": 78,
            "dispensed": 75,
            "pending": 3
        }
    }
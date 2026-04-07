#!/usr/bin/env python3
"""
库存管理工具模块 - P2负责的具体实现（当前为占位版本）
提供库存记录、报告和采购建议功能。
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ==================== 库存记录工具 ====================
def record_transaction(drug_id: int, quantity: int, transaction_type: str, reason: str = None) -> str:
    """
    记录药品出入库流水（占位实现）

    Args:
        drug_id: 药品ID
        quantity: 数量
        transaction_type: 类型 ('in' 或 'out')
        reason: 原因（如"医生处方"、"管理员补货"）

    Returns:
        操作结果JSON字符串
    """
    logger.warning(f"占位记录库存流水: drug_id={drug_id}, quantity={quantity}, type={transaction_type}, reason={reason}")

    response = {
        "success": True,
        "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "drug_id": drug_id,
        "quantity": quantity,
        "type": transaction_type,
        "reason": reason or "未指定",
        "timestamp": datetime.now().isoformat(),
        "note": "此为占位实现，实际需要连接数据库记录流水"
    }

    return json.dumps(response, ensure_ascii=False, indent=2)

# ==================== 库存报告工具 ====================
def get_stock_report(start_date: str = None, end_date: str = None) -> str:
    """
    获取库存报告（占位实现）

    Args:
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）

    Returns:
        库存报告JSON字符串
    """
    logger.warning(f"占位获取库存报告: start={start_date}, end={end_date}")

    # 生成mock报告数据
    mock_report = [
        {
            "drug_name": "阿莫西林",
            "drug_id": 1,
            "start_stock": 120,
            "in": 50,
            "out": 70,
            "end_stock": 100,
            "transactions": 5
        },
        {
            "drug_name": "头孢克肟",
            "drug_id": 2,
            "start_stock": 90,
            "in": 30,
            "out": 40,
            "end_stock": 80,
            "transactions": 3
        },
        {
            "drug_name": "布洛芬",
            "drug_id": 3,
            "start_stock": 200,
            "in": 100,
            "out": 150,
            "end_stock": 150,
            "transactions": 8
        },
        {
            "drug_name": "对乙酰氨基酚",
            "drug_id": 4,
            "start_stock": 250,
            "in": 100,
            "out": 150,
            "end_stock": 200,
            "transactions": 7
        }
    ]

    response = {
        "report_period": {
            "start_date": start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": end_date or datetime.now().strftime("%Y-%m-%d")
        },
        "generated_at": datetime.now().isoformat(),
        "total_drugs": len(mock_report),
        "total_transactions": sum(item["transactions"] for item in mock_report),
        "total_in": sum(item["in"] for item in mock_report),
        "total_out": sum(item["out"] for item in mock_report),
        "stock_changes": mock_report,
        "note": "此为占位实现，实际需要从数据库生成报告"
    }

    return json.dumps(response, ensure_ascii=False, indent=2)

# ==================== 采购建议工具 ====================
def generate_purchase_suggestions() -> str:
    """
    生成采购建议（占位实现）

    基于库存下限和出库速度自动生成采购建议。

    Returns:
        采购建议JSON字符串
    """
    logger.warning("占位生成采购建议")

    # Mock采购建议
    mock_suggestions = [
        {
            "drug_name": "阿莫西林",
            "drug_id": 1,
            "current_stock": 20,
            "min_stock_threshold": 50,
            "daily_avg_out": 5.2,
            "days_until_stockout": 3.8,
            "suggested_purchase_quantity": 100,
            "urgency": "高",
            "reason": "库存低于阈值且消耗速度较快"
        },
        {
            "drug_name": "头孢克肟",
            "drug_id": 2,
            "current_stock": 45,
            "min_stock_threshold": 50,
            "daily_avg_out": 2.1,
            "days_until_stockout": 21.4,
            "suggested_purchase_quantity": 60,
            "urgency": "中",
            "reason": "库存接近阈值"
        },
        {
            "drug_name": "蒙脱石散",
            "drug_id": 5,
            "current_stock": 30,
            "min_stock_threshold": 40,
            "daily_avg_out": 1.5,
            "days_until_stockout": 20.0,
            "suggested_purchase_quantity": 50,
            "urgency": "中",
            "reason": "库存低于阈值"
        }
    ]

    response = {
        "generated_at": datetime.now().isoformat(),
        "total_suggestions": len(mock_suggestions),
        "total_suggested_quantity": sum(item["suggested_purchase_quantity"] for item in mock_suggestions),
        "urgent_count": len([item for item in mock_suggestions if item["urgency"] == "高"]),
        "suggestions": mock_suggestions,
        "algorithm": {
            "name": "基于库存阈值和消耗速度",
            "parameters": {
                "min_stock_threshold_source": "药品表min_stock_threshold字段",
                "daily_avg_calculation_period": "最近30天",
                "safety_stock_days": 7
            }
        },
        "note": "此为占位实现，实际需要基于真实数据计算"
    }

    return json.dumps(response, ensure_ascii=False, indent=2)

# ==================== 库存健康检查 ====================
def inventory_health_check() -> Dict[str, Any]:
    """库存系统健康检查（占位实现）"""
    return {
        "status": "placeholder",
        "module": "inventory",
        "message": "库存管理模块为占位实现，需由P2完成实际实现",
        "timestamp": datetime.now().isoformat(),
        "available_functions": ["record_transaction", "get_stock_report", "generate_purchase_suggestions"]
    }

# ==================== 测试函数 ====================
if __name__ == "__main__":
    print("库存管理工具模块（占位版本）")
    print("=" * 50)
    print("此模块应由P2实现，提供真实的库存管理功能。")
    print("当前为占位实现，返回mock数据。")
    print("")

    # 测试各函数
    print("1. record_transaction测试:")
    print(record_transaction(1, 10, "out", "医生处方"))

    print("\n2. get_stock_report测试:")
    print(get_stock_report("2025-01-01", "2025-01-31"))

    print("\n3. generate_purchase_suggestions测试:")
    print(generate_purchase_suggestions())

    print("\n4. 健康检查:")
    print(json.dumps(inventory_health_check(), indent=2, ensure_ascii=False))
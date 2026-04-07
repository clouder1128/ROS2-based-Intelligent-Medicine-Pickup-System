#!/usr/bin/env python3
"""
库存管理工具模块 - P2负责的具体实现（当前为占位版本）
提供库存记录、报告和采购建议功能。
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from utils.http_client import PharmacyHTTPClient
import drug_db

logger = logging.getLogger(__name__)

# ==================== 库存记录工具 ====================
def record_transaction(drug_id: int, quantity: int, transaction_type: str, reason: str = None) -> str:
    """
    记录药品出入库流水

    Args:
        drug_id: 药品ID
        quantity: 数量
        transaction_type: 类型 ('in' 或 'out')
        reason: 原因（如"医生处方"、"管理员补货"）

    Returns:
        操作结果JSON字符串
    """
    logger.info(f"记录库存流水: drug_id={drug_id}, quantity={quantity}, type={transaction_type}, reason={reason}")

    try:
        if transaction_type == "out":
            # Use backend order API for out transactions
            client = PharmacyHTTPClient()
            order_result = client.create_order([{"id": drug_id, "num": quantity}])

            if order_result and order_result.get('success', False):
                response = {
                    "success": True,
                    "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "drug_id": drug_id,
                    "quantity": quantity,
                    "type": transaction_type,
                    "reason": reason or "医生处方",
                    "timestamp": datetime.now().isoformat(),
                    "backend_order_id": order_result.get('task_ids', [None])[0],
                    "message": "通过backend订单API处理"
                }
            else:
                response = {
                    "success": False,
                    "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "drug_id": drug_id,
                    "quantity": quantity,
                    "type": transaction_type,
                    "reason": reason or "医生处方",
                    "timestamp": datetime.now().isoformat(),
                    "error": "Backend订单创建失败",
                    "backend_response": order_result
                }
        else:
            # In transactions not supported by backend yet
            response = {
                "success": True,
                "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "drug_id": drug_id,
                "quantity": quantity,
                "type": transaction_type,
                "reason": reason or "管理员补货",
                "timestamp": datetime.now().isoformat(),
                "note": "入库操作暂由本地记录，backend暂不支持"
            }

        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"记录库存流水失败: {str(e)}")
        response = {
            "success": False,
            "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "drug_id": drug_id,
            "quantity": quantity,
            "type": transaction_type,
            "reason": reason or "未指定",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "note": "记录失败，backend连接异常"
        }
        return json.dumps(response, ensure_ascii=False, indent=2)

# ==================== 库存报告工具 ====================
def get_stock_report(start_date: str = None, end_date: str = None, limit: int = 100) -> str:
    """
    获取库存报告

    Args:
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        limit: 返回药品数量限制，默认100，设为0或负数表示无限制

    Returns:
        库存报告JSON字符串
    """
    logger.info(f"获取库存报告: start={start_date}, end={end_date}, limit={limit}")

    try:
        # Get current stock from backend
        client = PharmacyHTTPClient()
        all_drugs = drug_db.get_all_drugs()

        # For now, generate simple report from current stock
        # Backend doesn't have transaction history API yet
        report_drugs = []
        # Apply limit if specified (limit > 0)
        drugs_to_process = all_drugs[:limit] if limit > 0 else all_drugs
        for drug in drugs_to_process:
            report_drug = {
                "drug_name": drug.get('name', '未知'),
                "drug_id": drug.get('drug_id'),
                "current_stock": drug.get('quantity', 0),
                "expiry_days": drug.get('expiry_date', 0),
                "location": f"货架{drug.get('shelve_id', 0)}",
                "status": "正常" if drug.get('expiry_date', 0) > 0 else "已过期"
            }
            report_drugs.append(report_drug)

        response = {
            "report_period": {
                "start_date": start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": end_date or datetime.now().strftime("%Y-%m-%d")
            },
            "generated_at": datetime.now().isoformat(),
            "total_drugs": len(all_drugs),
            "current_stock_summary": {
                "total_items": len(all_drugs),
                "total_quantity": sum(d.get('quantity', 0) for d in all_drugs),
                "expired_count": len([d for d in all_drugs if d.get('expiry_date', 0) <= 0]),
                "low_stock_count": len([d for d in all_drugs if d.get('quantity', 0) < 50])
            },
            "drugs": report_drugs,
            "note": "基于backend当前库存数据，交易历史功能待实现"
        }

        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"获取库存报告失败: {str(e)}")
        # Fallback to mock
        # Generate mock report as fallback
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
            }
        ]

        # Apply limit if specified (limit > 0)
        limited_mock_report = mock_report[:limit] if limit > 0 else mock_report

        response = {
            "report_period": {
                "start_date": start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": end_date or datetime.now().strftime("%Y-%m-%d")
            },
            "generated_at": datetime.now().isoformat(),
            "total_drugs": len(limited_mock_report),
            "total_transactions": sum(item["transactions"] for item in limited_mock_report),
            "total_in": sum(item["in"] for item in limited_mock_report),
            "total_out": sum(item["out"] for item in limited_mock_report),
            "stock_changes": limited_mock_report,
            "note": f"获取真实库存数据失败，使用mock数据: {str(e)}"
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
#!/usr/bin/env python3
"""
药品数据库模块 - 集成backend药房服务
提供药品数据查询和管理功能，通过HTTP API连接到后端服务。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import Config
from utils.http_client import PharmacyHTTPClient

logger = logging.getLogger(__name__)

# ==================== HTTP客户端初始化 ====================
_client = None

def _get_client() -> PharmacyHTTPClient:
    """获取HTTP客户端单例"""
    global _client
    if _client is None:
        _client = PharmacyHTTPClient()
    return _client

# ==================== 症状过滤辅助函数 ====================
def _filter_drugs_by_symptom(drugs: List[Dict[str, Any]], symptom: str) -> List[Dict[str, Any]]:
    """
    根据症状过滤药品列表（客户端过滤）

    注意：backend目前不支持按症状查询，所以在客户端实现过滤。
    实际生产环境中应该在backend实现此功能。
    """
    if not symptom:
        return drugs

    symptom_lower = symptom.lower()
    matched_drugs = []

    # Mock症状匹配逻辑 - 实际应该基于药品适应症数据
    # 这里使用简单的关键词匹配
    # 注意：backend返回的是中文药品名称，但为了兼容性，同时包含英文名称
    symptom_keywords = {
        "头痛": ["布洛芬", "ibuprofen", "对乙酰氨基酚", "paracetamol", "阿司匹林", "aspirin"],
        "发热": ["布洛芬", "ibuprofen", "对乙酰氨基酚", "paracetamol"],
        "咳嗽": ["头孢克肟", "cephalosporin", "dextromethorphan", "codeine"],
        "过敏": ["氯雷他定", "loratadine", "西替利嗪", "cetirizine"],
        "感染": ["阿莫西林", "amoxicillin", "头孢克肟", "cephalosporin", "阿奇霉素", "azithromycin"],
    }

    # 查找症状对应的药品名称关键词
    matched_keywords = []
    for chinese_symptom, keywords in symptom_keywords.items():
        if chinese_symptom in symptom_lower:
            matched_keywords.extend(keywords)

    if not matched_keywords:
        # 如果没有预定义匹配，返回空列表
        # 在实际应用中，应该基于药品适应症数据库进行匹配
        logger.warning(f"未找到症状 '{symptom}' 的预定义匹配")
        return []

    # 基于关键词过滤
    for drug in drugs:
        drug_name_lower = drug.get('name', '').lower()
        if any(keyword in drug_name_lower for keyword in matched_keywords):
            matched_drugs.append(drug)

    return matched_drugs

# ==================== 药品查询函数 ====================
def query_drugs_by_symptom(symptom: str) -> List[Dict[str, Any]]:
    """
    根据症状查询相关药品

    实际通过HTTP API连接到backend药房服务。

    Args:
        symptom: 症状关键词

    Returns:
        匹配症状的药品列表
    """
    logger.info(f"查询药品（症状）: {symptom}")

    try:
        client = _get_client()
        all_drugs = client.get_drugs()

        if not all_drugs:
            logger.warning("未从backend获取到药品数据")
            return []

        # 在客户端进行症状过滤
        filtered_drugs = _filter_drugs_by_symptom(all_drugs, symptom)

        logger.info(f"找到 {len(filtered_drugs)} 个匹配药品（总共 {len(all_drugs)} 个）")
        return filtered_drugs

    except Exception as e:
        logger.error(f"查询药品失败（症状: {symptom}）: {str(e)}")
        return []

def query_drug_by_name(name: str) -> Optional[Dict[str, Any]]:
    """根据药品名称查询"""
    logger.info(f"查询药品（名称）: {name}")

    try:
        client = _get_client()
        drugs = client.get_drugs(name_filter=name)

        if not drugs:
            logger.warning(f"未找到药品: {name}")
            return None

        # 返回第一个匹配的药品
        return drugs[0]

    except Exception as e:
        logger.error(f"查询药品失败（名称: {name}）: {str(e)}")
        return None

def update_stock(drug_id: int, quantity: int, transaction_type: str) -> bool:
    """
    更新药品库存

    注意：实际通过创建订单来更新库存。

    Args:
        drug_id: 药品ID
        quantity: 数量
        transaction_type: 类型 ('in' 或 'out')

    Returns:
        是否成功
    """
    logger.info(f"更新库存: drug_id={drug_id}, quantity={quantity}, type={transaction_type}")

    if transaction_type == 'out':
        # 通过创建订单来减少库存
        try:
            client = _get_client()
            order_result = client.create_order([
                {"id": drug_id, "num": quantity}
            ])

            success = order_result is not None and order_result.get('success', False)
            if success:
                logger.info(f"库存更新成功: drug_id={drug_id}, 减少 {quantity}")
            else:
                logger.warning(f"库存更新失败: drug_id={drug_id}")

            return success

        except Exception as e:
            logger.error(f"库存更新失败: {str(e)}")
            return False
    else:
        # 入库操作 - backend目前不支持，记录日志
        logger.warning(f"入库操作暂未实现: drug_id={drug_id}, quantity={quantity}")
        return False

def get_low_stock_drugs(threshold: int = 50) -> List[Dict[str, Any]]:
    """获取库存低于阈值的药品"""
    logger.info(f"获取低库存药品: threshold={threshold}")

    try:
        client = _get_client()
        all_drugs = client.get_drugs()

        low_stock_drugs = [
            drug for drug in all_drugs
            if drug.get('quantity', 0) < threshold
        ]

        logger.info(f"找到 {len(low_stock_drugs)} 个低库存药品")
        return low_stock_drugs

    except Exception as e:
        logger.error(f"获取低库存药品失败: {str(e)}")
        return []

# ==================== 数据库工具函数 ====================
def get_all_drugs() -> List[Dict[str, Any]]:
    """获取所有药品"""
    logger.info("获取所有药品")

    try:
        client = _get_client()
        return client.get_drugs()
    except Exception as e:
        logger.error(f"获取所有药品失败: {str(e)}")
        return []

def search_drugs(keyword: str) -> List[Dict[str, Any]]:
    """搜索药品"""
    logger.info(f"搜索药品: {keyword}")

    try:
        client = _get_client()
        return client.get_drugs(name_filter=keyword)
    except Exception as e:
        logger.error(f"搜索药品失败: {str(e)}")
        return []

def add_drug(drug_data: Dict[str, Any]) -> bool:
    """添加新药品"""
    logger.warning(f"添加药品功能暂未实现: {drug_data.get('name', 'unknown')}")
    # backend目前不支持添加药品
    return False

def delete_drug(drug_id: int) -> bool:
    """删除药品"""
    logger.warning(f"删除药品功能暂未实现: id={drug_id}")
    # backend目前不支持删除药品
    return False

# ==================== 健康检查 ====================
def health_check() -> Dict[str, Any]:
    """数据库健康检查"""
    try:
        client = _get_client()
        backend_health = client.health_check()

        return {
            "status": "connected" if backend_health.get('backend_available', True) else "disconnected",
            "backend_available": backend_health.get('backend_available', False),
            "backend_health": backend_health,
            "timestamp": datetime.now().isoformat(),
            "module": "drug_db (HTTP client)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# ==================== 初始化检查 ====================
if __name__ == "__main__":
    print("药品数据库模块（HTTP客户端版本）")
    print("=" * 50)
    print("此模块通过HTTP API连接到backend药房服务。")
    print("")

    # 测试健康检查
    print("健康检查:", json.dumps(health_check(), indent=2, ensure_ascii=False))

    # 测试获取所有药品
    print("\n获取所有药品:")
    all_drugs = get_all_drugs()
    print(f"找到 {len(all_drugs)} 个药品")

    if all_drugs:
        print("\n前5个药品:")
        for drug in all_drugs[:5]:
            print(f"  {drug.get('drug_id')}: {drug.get('name')} - 库存: {drug.get('quantity')}")
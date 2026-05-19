#!/usr/bin/env python3
"""
药品数据库模块 - 集成 backend 药房服务
提供药品数据查询和管理功能：同进程读路径走 drug_service，写/扩展 API 走 HTTP 客户端。
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from common.config import Config
from common.utils.drug_service import query_drugs as service_query_drugs
from common.utils.http_client import PharmacyHTTPClient

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> PharmacyHTTPClient:
    global _client
    if _client is None:
        token = getattr(Config, "PHARMACY_API_TOKEN", None) or None
        _client = PharmacyHTTPClient(bearer_token=token)
    return _client


def query_drugs_by_symptom(symptom: str) -> List[Dict[str, Any]]:
    """根据症状查询相关药品（直接数据库查询，绕过 HTTP 回环）"""
    logger.info(f"Querying drugs by symptom: {symptom}")
    try:
        drugs = service_query_drugs(symptom=symptom)
        if not drugs:
            logger.info(f"No drugs found for symptom '{symptom}'")
            return []
        logger.info(f"Found {len(drugs)} matching drugs for symptom '{symptom}'")
        return drugs
    except Exception as e:
        logger.error(f"Failed to query drugs by symptom: {str(e)}")
        return []


def get_drugs_by_symptom_or_name(query: str) -> List[Dict[str, Any]]:
    """先用症状查询，失败后用名称/关键词查询（供 query_drug 工具使用）"""
    drugs = query_drugs_by_symptom(query)
    if drugs:
        return drugs
    drugs = search_drugs(query)
    if drugs:
        return drugs
    drug = query_drug_by_name(query)
    return [drug] if drug else []


def query_drug_by_name(name: str) -> Optional[Dict[str, Any]]:
    logger.info(f"Querying drug by name: {name}")
    try:
        drugs = service_query_drugs(name=name)
        if not drugs:
            logger.warning(f"Drug not found: {name}")
            return None
        return drugs[0]
    except Exception as e:
        logger.error(f"Failed to query drug by name: {str(e)}")
        return None


def update_stock(drug_id: int, quantity: int, transaction_type: str) -> bool:
    logger.info(
        f"Updating stock: drug_id={drug_id}, quantity={quantity}, type={transaction_type}"
    )
    try:
        client = _get_client()
        if transaction_type == "out":
            order_result = client.create_order([{"id": drug_id, "num": quantity}])
            success = order_result is not None and order_result.get("success", False)
            if success:
                logger.info(f"Stock updated: drug_id={drug_id}, reduced by {quantity}")
            else:
                logger.warning(f"Stock update failed: drug_id={drug_id}")
            return success
        if transaction_type == "in":
            result = client.adjust_inventory(
                drug_id,
                quantity_change=quantity,
                transaction_type="in",
                reason="pharmacy_client inbound",
            )
            success = result is not None
            if success:
                logger.info(f"Stock updated: drug_id={drug_id}, increased by {quantity}")
            return success
        logger.warning(f"Unsupported transaction_type: {transaction_type}")
        return False
    except Exception as e:
        logger.error(f"Stock update failed: {str(e)}")
        return False


def get_low_stock_drugs(threshold: int = 10) -> List[Dict[str, Any]]:
    logger.info(f"Getting low stock drugs: threshold={threshold}")
    try:
        client = _get_client()
        drugs = client.get_low_stock_drugs(threshold=threshold)
        logger.info(f"Found {len(drugs)} low stock drugs")
        return drugs
    except Exception as e:
        logger.error(f"Failed to get low stock drugs: {str(e)}")
        return []


def get_expiring_soon_drugs(days: int = 30) -> List[Dict[str, Any]]:
    logger.info(f"Getting expiring soon drugs: days={days}")
    try:
        client = _get_client()
        drugs = client.get_expiring_soon_drugs(days=days)
        logger.info(f"Found {len(drugs)} expiring soon drugs")
        return drugs
    except Exception as e:
        logger.error(f"Failed to get expiring soon drugs: {str(e)}")
        return []


def get_all_drugs() -> List[Dict[str, Any]]:
    logger.info("Getting all drugs")
    try:
        client = _get_client()
        return client.get_drugs()
    except Exception as e:
        logger.error(f"Failed to get all drugs: {str(e)}")
        return []


def search_drugs(keyword: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    logger.info(f"Searching drugs: keyword={keyword!r}, category={category!r}")
    try:
        client = _get_client()
        drugs = client.search_drugs(keyword=keyword, category=category)
        if drugs:
            return drugs
        return client.get_drugs(name_filter=keyword, category=category)
    except Exception as e:
        logger.error(f"Failed to search drugs: {str(e)}")
        return []


def get_inventory_view(
    name: Optional[str] = None,
    category: Optional[str] = None,
    threshold: Optional[int] = None,
    expiring_window: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """GET /api/inventory 拣货向视图。"""
    logger.info("Getting inventory view")
    try:
        client = _get_client()
        return client.get_inventory(
            name_filter=name,
            category=category,
            threshold=threshold,
            expiring_window=expiring_window,
        )
    except Exception as e:
        logger.error(f"Failed to get inventory view: {str(e)}")
        return []


def get_categories(tree: bool = False) -> List[Dict[str, Any]]:
    logger.info(f"Getting categories tree={tree}")
    try:
        client = _get_client()
        return client.get_categories(tree=tree)
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        return []


def adjust_inventory(
    drug_id: int,
    quantity_change: int,
    transaction_type: str = "adjust",
    reason: Optional[str] = None,
    operator: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    logger.info(
        f"Adjust inventory: drug_id={drug_id}, change={quantity_change}, type={transaction_type}"
    )
    try:
        client = _get_client()
        return client.adjust_inventory(
            drug_id,
            quantity_change=quantity_change,
            transaction_type=transaction_type,
            reason=reason,
            operator=operator,
        )
    except Exception as e:
        logger.error(f"Failed to adjust inventory: {str(e)}")
        return None


def batch_import_drugs(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    logger.info(f"Batch import drugs: count={len(items)}")
    try:
        client = _get_client()
        return client.batch_import_drugs(items)
    except Exception as e:
        logger.error(f"Failed to batch import drugs: {str(e)}")
        return None


def export_drugs(fmt: str = "json") -> Union[Dict[str, Any], str, None]:
    logger.info(f"Export drugs format={fmt}")
    try:
        client = _get_client()
        return client.export_drugs(fmt=fmt)
    except Exception as e:
        logger.error(f"Failed to export drugs: {str(e)}")
        return None


def get_drug_stats() -> Optional[Dict[str, Any]]:
    logger.info("Getting drug stats")
    try:
        client = _get_client()
        return client.get_drug_stats()
    except Exception as e:
        logger.error(f"Failed to get drug stats: {str(e)}")
        return None


def add_drug(drug_data: Dict[str, Any]) -> bool:
    logger.info(f"Adding drug: {drug_data.get('name', 'unknown')}")
    try:
        client = _get_client()
        result = client.create_drug(drug_data)
        return result is not None
    except Exception as e:
        logger.error(f"Add drug failed: {str(e)}")
        return False


def delete_drug(drug_id: int) -> bool:
    logger.info(f"Deleting drug: id={drug_id}")
    try:
        client = _get_client()
        return client.delete_drug(drug_id)
    except Exception as e:
        logger.error(f"Delete drug failed: {str(e)}")
        return False


def health_check() -> Dict[str, Any]:
    try:
        client = _get_client()
        backend_health = client.health_check()
        return {
            "status": "connected" if backend_health.get("backend_available", True) else "disconnected",
            "backend_available": backend_health.get("backend_available", False),
            "backend_health": backend_health,
            "timestamp": datetime.now().isoformat(),
            "module": "pharmacy_client (HTTP client)",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }

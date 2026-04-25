#!/usr/bin/env python3
"""
药品数据库模块 - 集成backend药房服务
提供药品数据查询和管理功能，通过HTTP API连接到后端服务。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from common.config import Config
from common.utils.http_client import PharmacyHTTPClient

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> PharmacyHTTPClient:
    global _client
    if _client is None:
        _client = PharmacyHTTPClient()
    return _client


def _filter_drugs_by_symptom(drugs: List[Dict[str, Any]], symptom: str) -> List[Dict[str, Any]]:
    if not symptom:
        return drugs
    symptom_lower = symptom.lower()
    matched_drugs = []
    symptom_keywords = {
        "headache": ["ibuprofen", "paracetamol", "aspirin"],
        "fever": ["ibuprofen", "paracetamol"],
        "cough": ["cephalosporin", "dextromethorphan", "codeine"],
        "allergy": ["loratadine", "cetirizine"],
        "infection": ["amoxicillin", "cephalosporin", "azithromycin"],
    }
    matched_keywords = []
    for chinese_symptom, keywords in symptom_keywords.items():
        if chinese_symptom in symptom_lower:
            matched_keywords.extend(keywords)
    if not matched_keywords:
        logger.warning(f"No predefined matching found for symptom '{symptom}'")
        return []
    for drug in drugs:
        drug_name_lower = drug.get("name", "").lower()
        if any(keyword in drug_name_lower for keyword in matched_keywords):
            matched_drugs.append(drug)
    return matched_drugs


def query_drugs_by_symptom(symptom: str) -> List[Dict[str, Any]]:
    logger.info(f"Querying drugs by symptom: {symptom}")
    try:
        client = _get_client()
        all_drugs = client.get_drugs()
        if not all_drugs:
            logger.warning("No drugs retrieved from backend")
            return []
        filtered_drugs = _filter_drugs_by_symptom(all_drugs, symptom)
        logger.info(f"Found {len(filtered_drugs)} matching drugs (total {len(all_drugs)})")
        return filtered_drugs
    except Exception as e:
        logger.error(f"Failed to query drugs by symptom: {str(e)}")
        return []


def query_drug_by_name(name: str) -> Optional[Dict[str, Any]]:
    logger.info(f"Querying drug by name: {name}")
    try:
        client = _get_client()
        drugs = client.get_drugs(name_filter=name)
        if not drugs:
            logger.warning(f"Drug not found: {name}")
            return None
        return drugs[0]
    except Exception as e:
        logger.error(f"Failed to query drug by name: {str(e)}")
        return None


def update_stock(drug_id: int, quantity: int, transaction_type: str) -> bool:
    logger.info(f"Updating stock: drug_id={drug_id}, quantity={quantity}, type={transaction_type}")
    if transaction_type == "out":
        try:
            client = _get_client()
            order_result = client.create_order([{"id": drug_id, "num": quantity}])
            success = order_result is not None and order_result.get("success", False)
            if success:
                logger.info(f"Stock updated: drug_id={drug_id}, reduced by {quantity}")
            else:
                logger.warning(f"Stock update failed: drug_id={drug_id}")
            return success
        except Exception as e:
            logger.error(f"Stock update failed: {str(e)}")
            return False
    else:
        logger.warning(f"Inbound operation not implemented: drug_id={drug_id}, quantity={quantity}")
        return False


def get_low_stock_drugs(threshold: int = 50) -> List[Dict[str, Any]]:
    logger.info(f"Getting low stock drugs: threshold={threshold}")
    try:
        client = _get_client()
        all_drugs = client.get_drugs()
        low_stock_drugs = [drug for drug in all_drugs if drug.get("quantity", 0) < threshold]
        logger.info(f"Found {len(low_stock_drugs)} low stock drugs")
        return low_stock_drugs
    except Exception as e:
        logger.error(f"Failed to get low stock drugs: {str(e)}")
        return []


def get_all_drugs() -> List[Dict[str, Any]]:
    logger.info("Getting all drugs")
    try:
        client = _get_client()
        return client.get_drugs()
    except Exception as e:
        logger.error(f"Failed to get all drugs: {str(e)}")
        return []


def search_drugs(keyword: str) -> List[Dict[str, Any]]:
    logger.info(f"Searching drugs: {keyword}")
    try:
        client = _get_client()
        return client.get_drugs(name_filter=keyword)
    except Exception as e:
        logger.error(f"Failed to search drugs: {str(e)}")
        return []


def add_drug(drug_data: Dict[str, Any]) -> bool:
    logger.warning(f"Add drug not implemented: {drug_data.get('name', 'unknown')}")
    return False


def delete_drug(drug_id: int) -> bool:
    logger.warning(f"Delete drug not implemented: id={drug_id}")
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

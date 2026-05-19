"""
HTTP客户端工具，用于与智能药房后端API通信。
提供异步和同步两种调用方式，支持重试和错误处理。
"""

import asyncio
import logging
import sys
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

from common.config import Config

logger = logging.getLogger(__name__)


class PharmacyHTTPClient:
    """智能药房HTTP客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        bearer_token: Optional[str] = None,
    ):
        self.base_url = base_url or Config.PHARMACY_BASE_URL
        parsed = urlparse(self.base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                f"Invalid base_url format: {self.base_url}. Must include scheme (http/https) and hostname."
            )
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.bearer_token = bearer_token
        self.retry_decorator = retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=retry_delay, max=10),
            retry=retry_if_exception_type(
                (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
            ),
            reraise=True,
        )
        logger.debug(f"Initialized PharmacyHTTPClient, base_url={self.base_url}")

    def _run_async(self, coro):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import threading
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._run_async_in_thread, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def _run_async_in_thread(self, coro):
        return asyncio.run(coro)

    def _request_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if extra:
            headers.update(extra)
        return headers

    @staticmethod
    def _params(**kwargs) -> Dict[str, Any]:
        return {k: v for k, v in kwargs.items() if v is not None}

    @staticmethod
    def _extract_list(result: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not result or not result.get("success"):
            return []
        data = result.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if isinstance(data.get("drugs"), list):
                return data["drugs"]
        return []

    @staticmethod
    def _extract_data(result: Optional[Dict[str, Any]]) -> Any:
        if not result or not result.get("success"):
            return None
        return result.get("data")

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        extra_headers = kwargs.pop("headers", None) or {}
        kwargs["headers"] = self._request_headers(extra_headers)
        logger.debug(f"Sending request: {method} {url}")
        try:
            @self.retry_decorator
            async def _request():
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()
            result = await _request()
            logger.debug(f"Request success: {method} {url}")
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Resource not found: {method} {url}")
                return None
            else:
                logger.error(f"HTTP error {e.response.status_code}: {method} {url} - {e}")
                return None
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error(f"Network error: {method} {url} - {e}")
            return None
        except RetryError as e:
            logger.error(f"Retries exhausted: {method} {url} - {e}")
            return None
        except Exception as e:
            logger.error(f"Request exception: {method} {url} - {e}")
            return None

    async def _make_raw_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[httpx.Response]:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        extra_headers = kwargs.pop("headers", None) or {}
        kwargs["headers"] = self._request_headers(extra_headers)
        logger.debug(f"Sending raw request: {method} {url}")
        try:
            @self.retry_decorator
            async def _request():
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
            return await _request()
        except Exception as e:
            logger.error(f"Raw request failed: {method} {url} - {e}")
            return None

    # ========== Drug API ==========

    async def get_drugs_async(
        self,
        name_filter: Optional[str] = None,
        symptom_filter: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params = self._params(
            name=name_filter,
            symptom=symptom_filter,
            category=category,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
        result = await self._make_request("GET", "/api/drugs", params=params)
        return self._extract_list(result)

    def get_drugs(
        self,
        name_filter: Optional[str] = None,
        symptom_filter: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        return self._run_async(
            self.get_drugs_async(
                name_filter,
                symptom_filter,
                category,
                sort_by,
                order,
                page,
                limit,
            )
        )

    async def get_drug_by_id_async(self, drug_id: int) -> Optional[Dict[str, Any]]:
        result = await self._make_request("GET", f"/api/drugs/{drug_id}")
        data = self._extract_data(result)
        return data if isinstance(data, dict) else None

    def get_drug_by_id(self, drug_id: int) -> Optional[Dict[str, Any]]:
        return self._run_async(self.get_drug_by_id_async(drug_id))

    async def search_drugs_async(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params = self._params(
            keyword=keyword,
            q=keyword,
            category=category,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
        )
        result = await self._make_request("GET", "/api/drugs/search", params=params)
        return self._extract_list(result)

    def search_drugs(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        return self._run_async(
            self.search_drugs_async(keyword, category, sort_by, order, page, limit)
        )

    async def create_drug_async(self, drug_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = await self._make_request("POST", "/api/drugs", json=drug_data)
        return self._extract_data(result)

    def create_drug(self, drug_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._run_async(self.create_drug_async(drug_data))

    async def update_drug_async(
        self, drug_id: int, drug_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        result = await self._make_request("PUT", f"/api/drugs/{drug_id}", json=drug_data)
        return self._extract_data(result)

    def update_drug(self, drug_id: int, drug_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._run_async(self.update_drug_async(drug_id, drug_data))

    async def delete_drug_async(self, drug_id: int) -> bool:
        result = await self._make_request("DELETE", f"/api/drugs/{drug_id}")
        return bool(result and result.get("success"))

    def delete_drug(self, drug_id: int) -> bool:
        return self._run_async(self.delete_drug_async(drug_id))

    async def batch_import_drugs_async(
        self, items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        result = await self._make_request("POST", "/api/drugs/batch-import", json=items)
        return self._extract_data(result)

    def batch_import_drugs(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return self._run_async(self.batch_import_drugs_async(items))

    async def export_drugs_async(
        self, fmt: str = "json"
    ) -> Union[Dict[str, Any], str, None]:
        params = {"format": fmt} if fmt else None
        if fmt == "csv":
            resp = await self._make_raw_request(
                "GET",
                "/api/drugs/export",
                params=params,
                headers={"Accept": "text/csv"},
            )
            return resp.text if resp is not None else None
        result = await self._make_request("GET", "/api/drugs/export", params=params)
        return self._extract_data(result)

    def export_drugs(self, fmt: str = "json") -> Union[Dict[str, Any], str, None]:
        return self._run_async(self.export_drugs_async(fmt))

    async def get_drug_stats_async(self) -> Optional[Dict[str, Any]]:
        result = await self._make_request("GET", "/api/drugs/stats")
        return self._extract_data(result)

    def get_drug_stats(self) -> Optional[Dict[str, Any]]:
        return self._run_async(self.get_drug_stats_async())

    async def get_inventory_async(
        self,
        name_filter: Optional[str] = None,
        symptom_filter: Optional[str] = None,
        category: Optional[str] = None,
        threshold: Optional[int] = None,
        expiring_window: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params = self._params(
            name=name_filter,
            symptom=symptom_filter,
            category=category,
            threshold=threshold,
            expiring_window=expiring_window,
            page=page,
            limit=limit,
        )
        result = await self._make_request("GET", "/api/inventory", params=params)
        return self._extract_list(result)

    def get_inventory(
        self,
        name_filter: Optional[str] = None,
        symptom_filter: Optional[str] = None,
        category: Optional[str] = None,
        threshold: Optional[int] = None,
        expiring_window: Optional[int] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        return self._run_async(
            self.get_inventory_async(
                name_filter,
                symptom_filter,
                category,
                threshold,
                expiring_window,
                page,
                limit,
            )
        )

    async def adjust_inventory_async(
        self,
        drug_id: int,
        *,
        quantity_change: Optional[int] = None,
        transaction_type: Optional[str] = None,
        quantity: Optional[int] = None,
        delta: Optional[int] = None,
        reason: Optional[str] = None,
        operator: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        body: Dict[str, Any] = {}
        if quantity_change is not None and transaction_type is not None:
            body["quantity_change"] = quantity_change
            body["transaction_type"] = transaction_type
        elif quantity is not None:
            body["quantity"] = quantity
            if transaction_type:
                body["transaction_type"] = transaction_type
        elif delta is not None:
            body["delta"] = delta
            if transaction_type:
                body["transaction_type"] = transaction_type
        else:
            return None
        if reason is not None:
            body["reason"] = reason
        if operator is not None:
            body["operator"] = operator
        result = await self._make_request(
            "POST", f"/api/drugs/{drug_id}/adjust", json=body
        )
        return self._extract_data(result)

    def adjust_inventory(
        self,
        drug_id: int,
        *,
        quantity_change: Optional[int] = None,
        transaction_type: Optional[str] = None,
        quantity: Optional[int] = None,
        delta: Optional[int] = None,
        reason: Optional[str] = None,
        operator: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        return self._run_async(
            self.adjust_inventory_async(
                drug_id,
                quantity_change=quantity_change,
                transaction_type=transaction_type,
                quantity=quantity,
                delta=delta,
                reason=reason,
                operator=operator,
            )
        )

    async def get_low_stock_drugs_async(
        self, threshold: Optional[int] = None, page: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = self._params(threshold=threshold, page=page, limit=limit)
        result = await self._make_request("GET", "/api/drugs/low-stock", params=params)
        return self._extract_list(result)

    def get_low_stock_drugs(
        self, threshold: Optional[int] = None, page: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self._run_async(self.get_low_stock_drugs_async(threshold, page, limit))

    async def get_expiring_soon_drugs_async(
        self, days: Optional[int] = None, page: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = self._params(days=days, page=page, limit=limit)
        result = await self._make_request("GET", "/api/drugs/expiring-soon", params=params)
        return self._extract_list(result)

    def get_expiring_soon_drugs(
        self, days: Optional[int] = None, page: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self._run_async(self.get_expiring_soon_drugs_async(days, page, limit))

    # ========== Category API ==========

    async def get_categories_async(
        self, tree: bool = False, page: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = self._params(tree=1 if tree else None, page=page, limit=limit)
        result = await self._make_request("GET", "/api/categories", params=params)
        return self._extract_list(result)

    def get_categories(
        self, tree: bool = False, page: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self._run_async(self.get_categories_async(tree, page, limit))

    async def create_category_async(self, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = await self._make_request("POST", "/api/categories", json=category_data)
        return self._extract_data(result)

    def create_category(self, category_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._run_async(self.create_category_async(category_data))

    # ========== Approval API ==========

    async def create_approval_async(self, patient_name: str, advice: str, **kwargs) -> Optional[str]:
        data = {"patient_name": patient_name, "advice": advice, **kwargs}
        result = await self._make_request("POST", "/api/approvals", json=data)
        if result and result.get("success") and "approval_id" in result:
            return result["approval_id"]
        return None

    def create_approval(self, patient_name: str, advice: str, **kwargs) -> Optional[str]:
        return self._run_async(self.create_approval_async(patient_name, advice, **kwargs))

    async def get_approval_async(self, approval_id: str) -> Optional[Dict[str, Any]]:
        result = await self._make_request("GET", f"/api/approvals/{approval_id}")
        if result and result.get("success"):
            return result
        return None

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        return self._run_async(self.get_approval_async(approval_id))

    async def get_pending_approvals_async(self, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"limit": limit} if limit != 100 else {}
        result = await self._make_request("GET", "/api/approvals/pending", params=params)
        if result and result.get("success") and "approvals" in result:
            return result["approvals"]
        return []

    def get_pending_approvals(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._run_async(self.get_pending_approvals_async(limit))

    async def approve_approval_async(self, approval_id: str, doctor_id: str) -> Optional[Dict[str, Any]]:
        result = await self._make_request(
            "POST", f"/api/approvals/{approval_id}/approve", json={"doctor_id": doctor_id}
        )
        if result and result.get("success"):
            return result
        return None

    def approve_approval(self, approval_id: str, doctor_id: str) -> Optional[Dict[str, Any]]:
        return self._run_async(self.approve_approval_async(approval_id, doctor_id))

    async def reject_approval_async(self, approval_id: str, doctor_id: str, reason: str) -> Optional[Dict[str, Any]]:
        result = await self._make_request(
            "POST", f"/api/approvals/{approval_id}/reject",
            json={"doctor_id": doctor_id, "reason": reason}
        )
        if result and result.get("success"):
            return result
        return None

    def reject_approval(self, approval_id: str, doctor_id: str, reason: str) -> Optional[Dict[str, Any]]:
        return self._run_async(self.reject_approval_async(approval_id, doctor_id, reason))

    # ========== Order API ==========

    async def create_order_async(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        result = await self._make_request("POST", "/api/order", json=items)
        if result and (result.get("success") or result.get("ok")):
            if "ok" in result and "success" not in result:
                result["success"] = result["ok"]
            return result
        return None

    def create_order(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        return self._run_async(self.create_order_async(items))

    # ========== Health API ==========

    async def health_check_async(self) -> Dict[str, Any]:
        result = await self._make_request("GET", "/api/health")
        if result and result.get("success"):
            result["backend_available"] = True
            return result
        return {
            "success": False,
            "error": "Health check failed",
            "backend": "pharmacy",
            "backend_available": False,
            "ros2_connected": False,
        }

    def health_check(self) -> Dict[str, Any]:
        return self._run_async(self.health_check_async())

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

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
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

    # ========== Drug API ==========

    async def get_drugs_async(self, name_filter: Optional[str] = None, symptom_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if name_filter:
            params["name"] = name_filter
        if symptom_filter:
            params["symptom"] = symptom_filter
        result = await self._make_request("GET", "/api/drugs", params=params)
        if result and result.get("success") and "drugs" in result:
            return result["drugs"]
        return []

    def get_drugs(self, name_filter: Optional[str] = None, symptom_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._run_async(self.get_drugs_async(name_filter, symptom_filter))

    async def get_drug_by_id_async(self, drug_id: int) -> Optional[Dict[str, Any]]:
        result = await self._make_request("GET", f"/api/drugs/{drug_id}")
        if result and result.get("success") and "drug" in result:
            return result["drug"]
        return None

    def get_drug_by_id(self, drug_id: int) -> Optional[Dict[str, Any]]:
        return self._run_async(self.get_drug_by_id_async(drug_id))

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

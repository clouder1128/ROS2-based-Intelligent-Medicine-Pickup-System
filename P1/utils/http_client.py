# http_client.py
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
    RetryError
)

from core.config import Config

logger = logging.getLogger(__name__)


class PharmacyHTTPClient:
    """智能药房HTTP客户端

    提供与后端API通信的接口，支持异步和同步调用。
    自动处理重试、错误处理和日志记录。
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0
    ):
        """初始化HTTP客户端

        Args:
            base_url: 后端API基础URL，默认为Config.PHARMACY_BASE_URL
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            retry_backoff: 重试退避系数
        """
        self.base_url = base_url or Config.PHARMACY_BASE_URL

        # Validate URL format
        parsed = urlparse(self.base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid base_url format: {self.base_url}. Must include scheme (http/https) and hostname.")

        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff

        # 配置重试策略
        self.retry_decorator = retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=retry_delay, max=10),
            retry=retry_if_exception_type(
                (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)
            ),
            reraise=True
        )

        logger.debug(f"初始化PharmacyHTTPClient，base_url={self.base_url}")

    def _run_async(self, coro):
        """Run async coroutine from sync context, handling event loop properly

        This method handles the async/sync context switching properly to avoid
        RuntimeError: asyncio.run() cannot be called from a running event loop.

        Args:
            coro: The coroutine to run

        Returns:
            The result of the coroutine
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're inside a running event loop (e.g., called from async context)
                # We cannot use asyncio.run() or loop.run_until_complete()
                # The safest approach is to create a new event loop in a new thread
                import threading
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._run_async_in_thread, coro)
                    return future.result()
            else:
                # Loop exists but is not running, we can use it
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop in this thread, create a new one
            return asyncio.run(coro)

    def _run_async_in_thread(self, coro):
        """Run async coroutine in a separate thread with its own event loop

        This is used when called from within a running event loop to avoid deadlock.
        Uses asyncio.run() which handles event loop creation and cleanup safely.
        """
        return asyncio.run(coro)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """发送HTTP请求（内部方法）

        Args:
            method: HTTP方法（GET, POST等）
            endpoint: API端点路径
            **kwargs: 传递给httpx请求的参数

        Returns:
            响应JSON字典，失败时返回None
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        # 添加默认超时
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        logger.debug(f"发送请求: {method} {url}")

        try:
            # 应用重试装饰器
            @self.retry_decorator
            async def _request():
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response.json()

            result = await _request()
            logger.debug(f"请求成功: {method} {url}")
            return result

        except httpx.HTTPStatusError as e:
            # HTTP错误处理
            if e.response.status_code == 404:
                logger.debug(f"资源未找到: {method} {url}")
                return None
            else:
                logger.error(f"HTTP错误 {e.response.status_code}: {method} {url} - {e}")
                return None

        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
            # 网络错误（已由重试处理）
            logger.error(f"网络错误: {method} {url} - {e}")
            return None

        except RetryError as e:
            # 重试耗尽
            logger.error(f"重试耗尽: {method} {url} - {e}")
            return None

        except Exception as e:
            # 其他异常
            logger.error(f"请求异常: {method} {url} - {e}")
            return None

    # ========== 药物管理API ==========

    async def get_drugs_async(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取药物列表（异步）

        Args:
            name_filter: 药物名称过滤（可选）

        Returns:
            药物列表，失败时返回空列表
        """
        params = {}
        if name_filter:
            params['name'] = name_filter

        result = await self._make_request('GET', '/api/drugs', params=params)

        if result and result.get('success') and 'drugs' in result:
            return result['drugs']
        return []

    def get_drugs(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取药物列表（同步）

        Args:
            name_filter: 药物名称过滤（可选）

        Returns:
            药物列表，失败时返回空列表
        """
        return self._run_async(self.get_drugs_async(name_filter))

    async def get_drug_by_id_async(self, drug_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取药物信息（异步）

        Args:
            drug_id: 药物ID

        Returns:
            药物信息字典，未找到时返回None
        """
        result = await self._make_request('GET', f'/api/drugs/{drug_id}')

        if result and result.get('success') and 'drug' in result:
            return result['drug']
        return None

    def get_drug_by_id(self, drug_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取药物信息（同步）

        Args:
            drug_id: 药物ID

        Returns:
            药物信息字典，未找到时返回None
        """
        return self._run_async(self.get_drug_by_id_async(drug_id))

    # ========== 审批管理API ==========

    async def create_approval_async(
        self,
        patient_name: str,
        advice: str,
        **kwargs
    ) -> Optional[str]:
        """创建审批（异步）

        Args:
            patient_name: 患者姓名
            advice: 用药建议
            **kwargs: 其他审批字段

        Returns:
            审批ID，失败时返回None
        """
        data = {
            'patient_name': patient_name,
            'advice': advice,
            **kwargs
        }

        result = await self._make_request('POST', '/api/approvals', json=data)

        if result and result.get('success') and 'approval_id' in result:
            return result['approval_id']
        return None

    def create_approval(self, patient_name: str, advice: str, **kwargs) -> Optional[str]:
        """创建审批（同步）

        Args:
            patient_name: 患者姓名
            advice: 用药建议
            **kwargs: 其他审批字段

        Returns:
            审批ID，失败时返回None
        """
        return self._run_async(self.create_approval_async(patient_name, advice, **kwargs))

    async def get_approval_async(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """获取审批信息（异步）

        Args:
            approval_id: 审批ID

        Returns:
            审批信息字典，未找到时返回None
        """
        result = await self._make_request('GET', f'/api/approvals/{approval_id}')

        if result and result.get('success'):
            return result
        return None

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """获取审批信息（同步）

        Args:
            approval_id: 审批ID

        Returns:
            审批信息字典，未找到时返回None
        """
        return self._run_async(self.get_approval_async(approval_id))

    async def get_pending_approvals_async(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取待处理审批列表（异步）

        Args:
            limit: 返回数量限制，默认100

        Returns:
            待处理审批列表，失败时返回空列表
        """
        params = {'limit': limit} if limit != 100 else {}

        result = await self._make_request('GET', '/api/approvals/pending', params=params)

        if result and result.get('success') and 'approvals' in result:
            return result['approvals']
        return []

    def get_pending_approvals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取待处理审批列表（同步）

        Args:
            limit: 返回数量限制，默认100

        Returns:
            待处理审批列表，失败时返回空列表
        """
        return self._run_async(self.get_pending_approvals_async(limit))

    async def approve_approval_async(
        self,
        approval_id: str,
        doctor_id: str
    ) -> Optional[Dict[str, Any]]:
        """批准审批（异步）

        Args:
            approval_id: 审批ID
            doctor_id: 医生ID

        Returns:
            批准结果字典，失败时返回None
        """
        data = {'doctor_id': doctor_id}

        result = await self._make_request(
            'POST',
            f'/api/approvals/{approval_id}/approve',
            json=data
        )

        if result and result.get('success'):
            return result
        return None

    def approve_approval(self, approval_id: str, doctor_id: str) -> Optional[Dict[str, Any]]:
        """批准审批（同步）

        Args:
            approval_id: 审批ID
            doctor_id: 医生ID

        Returns:
            批准结果字典，失败时返回None
        """
        return self._run_async(self.approve_approval_async(approval_id, doctor_id))

    async def reject_approval_async(
        self,
        approval_id: str,
        doctor_id: str,
        reason: str
    ) -> Optional[Dict[str, Any]]:
        """拒绝审批（异步）

        Args:
            approval_id: 审批ID
            doctor_id: 医生ID
            reason: 拒绝原因

        Returns:
            拒绝结果字典，失败时返回None
        """
        data = {
            'doctor_id': doctor_id,
            'reason': reason
        }

        result = await self._make_request(
            'POST',
            f'/api/approvals/{approval_id}/reject',
            json=data
        )

        if result and result.get('success'):
            return result
        return None

    def reject_approval(
        self,
        approval_id: str,
        doctor_id: str,
        reason: str
    ) -> Optional[Dict[str, Any]]:
        """拒绝审批（同步）

        Args:
            approval_id: 审批ID
            doctor_id: 医生ID
            reason: 拒绝原因

        Returns:
            拒绝结果字典，失败时返回None
        """
        return self._run_async(self.reject_approval_async(approval_id, doctor_id, reason))

    # ========== 订单管理API ==========

    async def create_order_async(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """创建订单（异步）

        Args:
            items: 订单项列表，格式：[{"id": 1, "num": 2}, ...]

        Returns:
            订单结果字典，失败时返回None
        """
        result = await self._make_request('POST', '/api/order', json=items)

        if result and (result.get('success') or result.get('ok')):
            # Normalize response to always have 'success' field
            if 'ok' in result and 'success' not in result:
                result['success'] = result['ok']
            return result
        return None

    def create_order(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """创建订单（同步）

        Args:
            items: 订单项列表，格式：[{"id": 1, "num": 2}, ...]

        Returns:
            订单结果字典，失败时返回None
        """
        return self._run_async(self.create_order_async(items))

    # ========== 健康检查API ==========

    async def health_check_async(self) -> Dict[str, Any]:
        """健康检查（异步）

        Returns:
            健康状态字典，失败时返回{"success": False, "error": "检查失败"}
        """
        result = await self._make_request('GET', '/api/health')

        if result and result.get('success'):
            # 确保返回的字典包含backend_available字段供P1使用
            result['backend_available'] = True
            return result

        return {
            'success': False,
            'error': '健康检查失败',
            'backend': 'pharmacy',
            'backend_available': False,
            'ros2_connected': False
        }

    def health_check(self) -> Dict[str, Any]:
        """健康检查（同步）

        Returns:
            健康状态字典，失败时返回{"success": False, "error": "检查失败"}
        """
        return self._run_async(self.health_check_async())
# test_http_client.py
"""
测试HTTP客户端工具。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, List, Any
import httpx
from tenacity import RetryError

from utils.http_client import PharmacyHTTPClient


class TestPharmacyHTTPClient:
    """测试PharmacyHTTPClient类"""

    @pytest.fixture
    def client(self):
        """创建测试客户端实例"""
        return PharmacyHTTPClient(base_url="http://test-server:8001")

    @pytest.fixture
    def mock_response_success(self):
        """创建成功的模拟响应"""
        return {
            "success": True,
            "message": "操作成功"
        }

    @pytest.fixture
    def mock_drugs_response(self):
        """创建药物列表模拟响应"""
        return {
            "success": True,
            "drugs": [
                {"id": 1, "name": "布洛芬", "description": "止痛药"},
                {"id": 2, "name": "阿莫西林", "description": "抗生素"}
            ],
            "count": 2,
            "filters": {}
        }

    @pytest.fixture
    def mock_drug_response(self):
        """创建单个药物模拟响应"""
        return {
            "success": True,
            "drug": {
                "id": 1,
                "name": "布洛芬",
                "description": "止痛药",
                "dosage": "200mg",
                "side_effects": "胃部不适"
            }
        }

    @pytest.fixture
    def mock_approval_response(self):
        """创建审批模拟响应"""
        return {
            "success": True,
            "approval_id": "AP-123456",
            "message": "审批创建成功",
            "created_at": "2024-01-01T12:00:00Z"
        }

    @pytest.fixture
    def mock_approval_detail_response(self):
        """创建审批详情模拟响应"""
        return {
            "success": True,
            "id": "AP-123456",
            "patient_name": "张三",
            "advice": "建议使用布洛芬",
            "status": "pending",
            "created_at": "2024-01-01T12:00:00Z"
        }

    @pytest.fixture
    def mock_pending_approvals_response(self):
        """创建待处理审批模拟响应"""
        return {
            "success": True,
            "approvals": [
                {"id": "AP-123456", "patient_name": "张三", "status": "pending"},
                {"id": "AP-123457", "patient_name": "李四", "status": "pending"}
            ],
            "count": 2,
            "limit": 100
        }

    @pytest.fixture
    def mock_order_response(self):
        """创建订单模拟响应"""
        return {
            "success": True,
            "task_ids": ["task-1", "task-2"],
            "message": "订单创建成功"
        }

    @pytest.fixture
    def mock_health_response(self):
        """创建健康检查模拟响应"""
        return {
            "success": True,
            "backend": "pharmacy",
            "ros2_connected": True,
            "timestamp": "2024-01-01T12:00:00Z"
        }

    # ========== 测试初始化 ==========

    def test_init_default_base_url(self):
        """测试使用默认base_url初始化"""
        with patch('config.Config.PHARMACY_BASE_URL', 'http://default:8001'):
            client = PharmacyHTTPClient()
            assert client.base_url == 'http://default:8001'

    def test_init_custom_base_url(self):
        """测试使用自定义base_url初始化"""
        client = PharmacyHTTPClient(base_url='http://custom:8001')
        assert client.base_url == 'http://custom:8001'

    def test_init_custom_timeout_and_retries(self):
        """测试自定义超时和重试参数"""
        client = PharmacyHTTPClient(
            base_url='http://test:8001',
            timeout=60.0,
            max_retries=5,
            retry_delay=2.0,
            retry_backoff=3.0
        )
        assert client.timeout == 60.0
        assert client.max_retries == 5

    # ========== 测试药物管理API ==========

    @pytest.mark.asyncio
    async def test_get_drugs_async_success(self, client, mock_drugs_response):
        """测试异步获取药物列表成功"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_drugs_response)):
            result = await client.get_drugs_async()
            assert len(result) == 2
            assert result[0]['name'] == '布洛芬'
            assert result[1]['name'] == '阿莫西林'

    @pytest.mark.asyncio
    async def test_get_drugs_async_with_filter(self, client, mock_drugs_response):
        """测试异步获取药物列表带过滤"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_drugs_response)):
            result = await client.get_drugs_async(name_filter='布洛')
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_drugs_async_failure(self, client):
        """测试异步获取药物列表失败"""
        with patch.object(client, '_make_request', AsyncMock(return_value=None)):
            result = await client.get_drugs_async()
            assert result == []

    def test_get_drugs_sync(self, client, mock_drugs_response):
        """测试同步获取药物列表"""
        with patch.object(client, 'get_drugs_async', AsyncMock(return_value=mock_drugs_response['drugs'])):
            result = client.get_drugs()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_drug_by_id_async_success(self, client, mock_drug_response):
        """测试异步根据ID获取药物成功"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_drug_response)):
            result = await client.get_drug_by_id_async(1)
            assert result['name'] == '布洛芬'
            assert result['dosage'] == '200mg'

    @pytest.mark.asyncio
    async def test_get_drug_by_id_async_not_found(self, client):
        """测试异步根据ID获取药物未找到"""
        with patch.object(client, '_make_request', AsyncMock(return_value=None)):
            result = await client.get_drug_by_id_async(999)
            assert result is None

    def test_get_drug_by_id_sync(self, client, mock_drug_response):
        """测试同步根据ID获取药物"""
        with patch.object(client, 'get_drug_by_id_async', AsyncMock(return_value=mock_drug_response['drug'])):
            result = client.get_drug_by_id(1)
            assert result['name'] == '布洛芬'

    # ========== 测试审批管理API ==========

    @pytest.mark.asyncio
    async def test_create_approval_async_success(self, client, mock_approval_response):
        """测试异步创建审批成功"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_approval_response)):
            result = await client.create_approval_async(
                patient_name='张三',
                advice='建议使用布洛芬'
            )
            assert result == 'AP-123456'

    @pytest.mark.asyncio
    async def test_create_approval_async_with_kwargs(self, client, mock_approval_response):
        """测试异步创建审批带额外参数"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_approval_response)):
            result = await client.create_approval_async(
                patient_name='张三',
                advice='建议使用布洛芬',
                doctor_id='DR-001',
                priority='high'
            )
            assert result == 'AP-123456'

    @pytest.mark.asyncio
    async def test_create_approval_async_failure(self, client):
        """测试异步创建审批失败"""
        with patch.object(client, '_make_request', AsyncMock(return_value=None)):
            result = await client.create_approval_async('张三', '建议')
            assert result is None

    def test_create_approval_sync(self, client, mock_approval_response):
        """测试同步创建审批"""
        with patch.object(client, 'create_approval_async', AsyncMock(return_value='AP-123456')):
            result = client.create_approval('张三', '建议使用布洛芬')
            assert result == 'AP-123456'

    @pytest.mark.asyncio
    async def test_get_approval_async_success(self, client, mock_approval_detail_response):
        """测试异步获取审批成功"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_approval_detail_response)):
            result = await client.get_approval_async('AP-123456')
            assert result['patient_name'] == '张三'
            assert result['status'] == 'pending'

    @pytest.mark.asyncio
    async def test_get_approval_async_not_found(self, client):
        """测试异步获取审批未找到"""
        with patch.object(client, '_make_request', AsyncMock(return_value=None)):
            result = await client.get_approval_async('AP-999999')
            assert result is None

    def test_get_approval_sync(self, client, mock_approval_detail_response):
        """测试同步获取审批"""
        with patch.object(client, 'get_approval_async', AsyncMock(return_value=mock_approval_detail_response)):
            result = client.get_approval('AP-123456')
            assert result['patient_name'] == '张三'

    @pytest.mark.asyncio
    async def test_get_pending_approvals_async_success(self, client, mock_pending_approvals_response):
        """测试异步获取待处理审批成功"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_pending_approvals_response)):
            result = await client.get_pending_approvals_async()
            assert len(result) == 2
            assert result[0]['id'] == 'AP-123456'

    @pytest.mark.asyncio
    async def test_get_pending_approvals_async_with_limit(self, client, mock_pending_approvals_response):
        """测试异步获取待处理审批带限制"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_pending_approvals_response)):
            result = await client.get_pending_approvals_async(limit=50)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_pending_approvals_async_failure(self, client):
        """测试异步获取待处理审批失败"""
        with patch.object(client, '_make_request', AsyncMock(return_value=None)):
            result = await client.get_pending_approvals_async()
            assert result == []

    def test_get_pending_approvals_sync(self, client, mock_pending_approvals_response):
        """测试同步获取待处理审批"""
        with patch.object(client, 'get_pending_approvals_async', AsyncMock(return_value=mock_pending_approvals_response['approvals'])):
            result = client.get_pending_approvals()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_approve_approval_async_success(self, client, mock_response_success):
        """测试异步批准审批成功"""
        mock_response_success.update({
            'approval_id': 'AP-123456',
            'doctor_id': 'DR-001',
            'approved_at': '2024-01-01T12:00:00Z'
        })
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_response_success)):
            result = await client.approve_approval_async('AP-123456', 'DR-001')
            assert result['success'] is True
            assert result['approval_id'] == 'AP-123456'

    @pytest.mark.asyncio
    async def test_reject_approval_async_success(self, client, mock_response_success):
        """测试异步拒绝审批成功"""
        mock_response_success.update({
            'approval_id': 'AP-123456',
            'doctor_id': 'DR-001',
            'reason': '药物过敏',
            'rejected_at': '2024-01-01T12:00:00Z'
        })
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_response_success)):
            result = await client.reject_approval_async('AP-123456', 'DR-001', '药物过敏')
            assert result['success'] is True
            assert result['reason'] == '药物过敏'

    # ========== 测试订单管理API ==========

    @pytest.mark.asyncio
    async def test_create_order_async_success(self, client, mock_order_response):
        """测试异步创建订单成功"""
        items = [{"id": 1, "num": 2}, {"id": 2, "num": 1}]
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_order_response)):
            result = await client.create_order_async(items)
            assert result['success'] is True
            assert 'task_ids' in result

    @pytest.mark.asyncio
    async def test_create_order_async_failure(self, client):
        """测试异步创建订单失败"""
        items = [{"id": 1, "num": 2}]
        with patch.object(client, '_make_request', AsyncMock(return_value=None)):
            result = await client.create_order_async(items)
            assert result is None

    def test_create_order_sync(self, client, mock_order_response):
        """测试同步创建订单"""
        items = [{"id": 1, "num": 2}]
        with patch.object(client, 'create_order_async', AsyncMock(return_value=mock_order_response)):
            result = client.create_order(items)
            assert result['success'] is True

    # ========== 测试健康检查API ==========

    @pytest.mark.asyncio
    async def test_health_check_async_success(self, client, mock_health_response):
        """测试异步健康检查成功"""
        with patch.object(client, '_make_request', AsyncMock(return_value=mock_health_response)):
            result = await client.health_check_async()
            assert result['success'] is True
            assert result['backend'] == 'pharmacy'

    @pytest.mark.asyncio
    async def test_health_check_async_failure(self, client):
        """测试异步健康检查失败"""
        with patch.object(client, '_make_request', AsyncMock(return_value=None)):
            result = await client.health_check_async()
            assert result['success'] is False
            assert 'error' in result

    def test_health_check_sync(self, client, mock_health_response):
        """测试同步健康检查"""
        with patch.object(client, 'health_check_async', AsyncMock(return_value=mock_health_response)):
            result = client.health_check()
            assert result['success'] is True

    # ========== 测试错误处理 ==========

    @pytest.mark.asyncio
    async def test_make_request_http_404(self, client):
        """测试HTTP 404错误处理"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        with patch('httpx.AsyncClient', return_value=AsyncMock(request=AsyncMock(return_value=mock_response))):
            result = await client._make_request('GET', '/api/drugs/999')
            assert result is None

    @pytest.mark.asyncio
    async def test_make_request_http_500(self, client):
        """测试HTTP 500错误处理"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error", request=Mock(), response=mock_response
        )

        with patch('httpx.AsyncClient', return_value=AsyncMock(request=AsyncMock(return_value=mock_response))):
            result = await client._make_request('GET', '/api/drugs')
            assert result is None

    @pytest.mark.asyncio
    async def test_make_request_network_error(self, client):
        """测试网络错误处理"""
        with patch('httpx.AsyncClient', side_effect=httpx.ConnectError("Connection failed")):
            result = await client._make_request('GET', '/api/drugs')
            assert result is None

    @pytest.mark.asyncio
    async def test_make_request_timeout(self, client):
        """测试超时错误处理"""
        with patch('httpx.AsyncClient', side_effect=httpx.TimeoutException("Request timed out")):
            result = await client._make_request('GET', '/api/drugs')
            assert result is None

    @pytest.mark.asyncio
    async def test_make_request_retry_exhausted(self, client):
        """测试重试耗尽"""
        # 创建一个会连续失败的mock
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.ConnectError("Connection failed")

        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await client._make_request('GET', '/api/drugs')
            assert result is None

    @pytest.mark.asyncio
    async def test_make_request_unexpected_exception(self, client):
        """测试意外异常处理"""
        with patch('httpx.AsyncClient', side_effect=Exception("Unexpected error")):
            result = await client._make_request('GET', '/api/drugs')
            assert result is None

    # ========== 测试边缘情况 ==========

    def test_empty_response_handling(self, client):
        """测试空响应处理"""
        # 测试get_drugs返回空列表
        with patch.object(client, 'get_drugs_async', AsyncMock(return_value=[])):
            result = client.get_drugs()
            assert result == []

    def test_invalid_json_response(self, client):
        """测试无效JSON响应"""
        # 模拟_make_request返回无效数据
        with patch.object(client, 'get_drugs_async', AsyncMock(return_value={'success': False})):
            result = client.get_drugs()
            assert result == []

    def test_client_reuse(self, client):
        """测试客户端重用"""
        # 测试同一个客户端可以多次调用
        with patch.object(client, 'get_drugs_async', AsyncMock(return_value=[])):
            result1 = client.get_drugs()
            result2 = client.get_drugs()
            assert result1 == []
            assert result2 == []

    # ========== 测试配置集成 ==========

    def test_config_integration(self):
        """测试与Config类的集成"""
        with patch('config.Config.PHARMACY_BASE_URL', 'http://config-test:8001'):
            client = PharmacyHTTPClient()
            assert client.base_url == 'http://config-test:8001'

    def test_config_override(self):
        """测试配置覆盖"""
        with patch('config.Config.PHARMACY_BASE_URL', 'http://config-default:8001'):
            client = PharmacyHTTPClient(base_url='http://override:8001')
            assert client.base_url == 'http://override:8001'
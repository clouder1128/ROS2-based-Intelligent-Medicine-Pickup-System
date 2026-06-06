import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from common.utils.http_client import PharmacyHTTPClient


def run(coro):
    return asyncio.run(coro)


def make_client():
    return PharmacyHTTPClient(
        base_url="http://pharmacy.test",
        max_retries=1,
        bearer_token="token",
    )


def test_client_validation_headers_extractors_and_async_runner():
    with pytest.raises(ValueError):
        PharmacyHTTPClient(base_url="invalid")

    client = make_client()
    assert client._request_headers({"X-Test": "1"}) == {
        "Authorization": "Bearer token",
        "X-Test": "1",
    }
    assert client._params(a=1, b=None) == {"a": 1}
    assert client._extract_list({"success": True, "data": [{"id": 1}]}) == [
        {"id": 1}
    ]
    assert client._extract_list(
        {"success": True, "data": {"drugs": [{"id": 2}]}}
    ) == [{"id": 2}]
    assert client._extract_list({"success": False}) == []
    assert client._extract_data({"success": True, "data": {"id": 1}}) == {
        "id": 1
    }
    assert client._extract_data(None) is None

    async def value():
        return 7

    assert client._run_async(value()) == 7
    assert client._run_async_in_thread(value()) == 7


def test_make_request_success_http_and_network_errors(monkeypatch):
    client = make_client()

    response = MagicMock()
    response.json.return_value = {"success": True, "data": {"id": 1}}
    response.raise_for_status.return_value = None
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=async_client)
    async_client.__aexit__ = AsyncMock(return_value=None)
    async_client.request = AsyncMock(return_value=response)
    monkeypatch.setattr(
        "common.utils.http_client.httpx.AsyncClient",
        MagicMock(return_value=async_client),
    )
    result = run(
        client._make_request(
            "GET", "/api/test", headers={"X-Test": "yes"}, params={"q": "x"}
        )
    )
    assert result["success"] is True
    kwargs = async_client.request.call_args.kwargs
    assert kwargs["headers"]["Authorization"] == "Bearer token"
    assert kwargs["headers"]["X-Test"] == "yes"
    assert kwargs["timeout"] == client.timeout

    request = httpx.Request("GET", "http://pharmacy.test/missing")
    not_found = httpx.Response(404, request=request)
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "missing", request=request, response=not_found
    )
    assert run(client._make_request("GET", "/missing")) is None

    response.raise_for_status.side_effect = httpx.ConnectError(
        "offline", request=request
    )
    assert run(client._make_request("GET", "/offline")) is None

    response.raise_for_status.side_effect = ValueError("bad json")
    assert run(client._make_request("GET", "/bad")) is None


def test_make_raw_request_success_and_failure(monkeypatch):
    client = make_client()
    response = MagicMock(text="csv")
    response.raise_for_status.return_value = None
    async_client = MagicMock()
    async_client.__aenter__ = AsyncMock(return_value=async_client)
    async_client.__aexit__ = AsyncMock(return_value=None)
    async_client.request = AsyncMock(return_value=response)
    monkeypatch.setattr(
        "common.utils.http_client.httpx.AsyncClient",
        MagicMock(return_value=async_client),
    )
    assert run(client._make_raw_request("GET", "/export")) is response

    async_client.request.side_effect = RuntimeError("offline")
    assert run(client._make_raw_request("GET", "/export")) is None


def test_drug_inventory_and_category_async_methods():
    client = make_client()
    client._make_request = AsyncMock(
        side_effect=[
            {"success": True, "data": [{"id": 1}]},
            {"success": True, "data": {"id": 1}},
            {"success": True, "data": {"drugs": [{"id": 2}]}},
            {"success": True, "data": {"id": 3}},
            {"success": True, "data": {"id": 3}},
            {"success": True},
            {"success": True, "data": {"imported": 2}},
            {"success": True, "data": {"rows": 2}},
            {"success": True, "data": {"total": 3}},
            {"success": True, "data": [{"id": 1}]},
            {"success": True, "data": {"after": 8}},
            {"success": True, "data": {"after": 5}},
            {"success": True, "data": {"after": 7}},
            {"success": True, "data": [{"id": 1}]},
            {"success": True, "data": [{"id": 2}]},
            {"success": True, "data": [{"id": 3}]},
            {"success": True, "data": {"id": 4}},
        ]
    )

    async def scenario():
        assert await client.get_drugs_async(name_filter="A", page=1) == [{"id": 1}]
        assert await client.get_drug_by_id_async(1) == {"id": 1}
        assert await client.search_drugs_async("pain") == [{"id": 2}]
        assert await client.create_drug_async({"name": "A"}) == {"id": 3}
        assert await client.update_drug_async(3, {"name": "B"}) == {"id": 3}
        assert await client.delete_drug_async(3) is True
        assert await client.batch_import_drugs_async([{"name": "A"}]) == {
            "imported": 2
        }
        assert await client.export_drugs_async("json") == {"rows": 2}
        assert await client.get_drug_stats_async() == {"total": 3}
        assert await client.get_inventory_async(threshold=5) == [{"id": 1}]
        assert await client.adjust_inventory_async(
            1, quantity_change=-2, transaction_type="out", reason="rx"
        ) == {"after": 8}
        assert await client.adjust_inventory_async(
            1, quantity=5, transaction_type="adjust"
        ) == {"after": 5}
        assert await client.adjust_inventory_async(1, delta=2) == {"after": 7}
        assert await client.adjust_inventory_async(1) is None
        assert await client.get_low_stock_drugs_async(5) == [{"id": 1}]
        assert await client.get_expiring_soon_drugs_async(30) == [{"id": 2}]
        assert await client.get_categories_async(True) == [{"id": 3}]
        assert await client.create_category_async({"name": "OTC"}) == {"id": 4}

    run(scenario())
    adjust_bodies = [
        call.kwargs["json"]
        for call in client._make_request.call_args_list
        if "/adjust" in call.args[1]
    ]
    assert adjust_bodies == [
        {"quantity_change": -2, "transaction_type": "out", "reason": "rx"},
        {"quantity": 5, "transaction_type": "adjust"},
        {"delta": 2},
    ]


def test_export_csv_and_approval_order_health_methods():
    client = make_client()
    client._make_raw_request = AsyncMock(return_value=SimpleNamespace(text="a,b"))
    client._make_request = AsyncMock(
        side_effect=[
            {"success": True, "approval_id": "ap-1"},
            {"success": True, "approval": {"id": "ap-1"}},
            {"success": True, "approvals": [{"id": "ap-1"}]},
            {"success": True, "status": "approved"},
            {"success": True, "status": "rejected"},
            {"ok": True, "task_ids": [1]},
            {"success": True, "status": "ok"},
            None,
        ]
    )

    async def scenario():
        assert await client.export_drugs_async("csv") == "a,b"
        assert await client.create_approval_async("Alice", "Advice") == "ap-1"
        approval = await client.get_approval_async("ap-1")
        assert approval["success"] is True
        assert await client.get_pending_approvals_async(5) == [{"id": "ap-1"}]
        assert await client.approve_approval_async("ap-1", "doctor")
        assert await client.reject_approval_async("ap-1", "doctor", "reason")
        order = await client.create_order_async([{"id": 1, "num": 1}])
        assert order["success"] is True
        assert (await client.health_check_async())["backend_available"] is True
        assert (await client.health_check_async())["backend_available"] is False

    run(scenario())


def test_sync_wrappers_delegate_to_run_async(monkeypatch):
    client = make_client()
    monkeypatch.setattr(client, "_run_async", lambda coro: (coro.close(), "done")[1])

    assert client.get_drugs() == "done"
    assert client.get_drug_by_id(1) == "done"
    assert client.search_drugs("A") == "done"
    assert client.create_drug({}) == "done"
    assert client.update_drug(1, {}) == "done"
    assert client.delete_drug(1) == "done"
    assert client.batch_import_drugs([]) == "done"
    assert client.export_drugs() == "done"
    assert client.get_drug_stats() == "done"
    assert client.get_inventory() == "done"
    assert client.adjust_inventory(1, delta=1) == "done"
    assert client.get_low_stock_drugs() == "done"
    assert client.get_expiring_soon_drugs() == "done"
    assert client.get_categories() == "done"
    assert client.create_category({}) == "done"
    assert client.create_approval("A", "B") == "done"
    assert client.get_approval("ap") == "done"
    assert client.get_pending_approvals() == "done"
    assert client.approve_approval("ap", "d") == "done"
    assert client.reject_approval("ap", "d", "r") == "done"
    assert client.create_order([]) == "done"
    assert client.health_check() == "done"

import pytest
from unittest.mock import Mock, patch
import tools.inventory as inventory
import json


def test_record_transaction_integrated():
    """Test record_transaction uses HTTP client for out transactions"""
    with patch('utils.http_client.PharmacyHTTPClient') as mock_client_class:
        mock_client = Mock()
        mock_client.create_order.return_value = {
            "success": True,
            "task_ids": [1],
            "message": "Order created"
        }
        mock_client_class.return_value = mock_client

        result_json = inventory.record_transaction(
            drug_id=1,
            quantity=2,
            transaction_type="out",
            reason="医生处方"
        )

        result = json.loads(result_json)
        assert result["success"] == True
        assert "transaction_id" in result
        mock_client.create_order.assert_called_once_with([{"id": 1, "num": 2}])
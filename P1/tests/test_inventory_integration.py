import pytest
from unittest.mock import Mock, patch
import tools.inventory as inventory
import json


def test_record_transaction_integrated():
    """Test record_transaction uses HTTP client for out transactions"""
    with patch('tools.inventory.PharmacyHTTPClient') as mock_client_class:
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


def test_get_stock_report_integrated():
    """Test get_stock_report uses get_all_drugs()"""
    # Mock drug data
    mock_drugs = [
        {
            "drug_id": 1,
            "name": "阿莫西林",
            "quantity": 100,
            "expiry_date": 30,
            "shelve_id": 1
        },
        {
            "drug_id": 2,
            "name": "头孢克肟",
            "quantity": 50,
            "expiry_date": 15,
            "shelve_id": 2
        },
        {
            "drug_id": 3,
            "name": "布洛芬",
            "quantity": 200,
            "expiry_date": 0,  # Expired
            "shelve_id": 3
        }
    ]

    with patch('tools.inventory.get_all_drugs') as mock_get_all_drugs:
        mock_get_all_drugs.return_value = mock_drugs

        # Test with default limit
        result_json = inventory.get_stock_report(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        result = json.loads(result_json)

        # Verify basic structure
        assert "report_period" in result
        assert "generated_at" in result
        assert "total_drugs" in result
        assert "current_stock_summary" in result
        assert "drugs" in result
        assert "note" in result

        # Verify report period
        assert result["report_period"]["start_date"] == "2025-01-01"
        assert result["report_period"]["end_date"] == "2025-01-31"

        # Verify summary data
        assert result["total_drugs"] == 3
        assert result["current_stock_summary"]["total_items"] == 3
        assert result["current_stock_summary"]["total_quantity"] == 350  # 100+50+200
        assert result["current_stock_summary"]["expired_count"] == 1  # drug_id 3 has expiry_date 0
        assert result["current_stock_summary"]["low_stock_count"] == 0  # all above 50

        # Verify drugs list (should include all 3 with default limit 100)
        assert len(result["drugs"]) == 3

        # Verify first drug details
        drug1 = result["drugs"][0]
        assert drug1["drug_name"] == "阿莫西林"
        assert drug1["drug_id"] == 1
        assert drug1["current_stock"] == 100
        assert drug1["expiry_days"] == 30
        assert drug1["location"] == "货架1"
        assert drug1["status"] == "正常"

        # Verify expired drug
        drug3 = result["drugs"][2]
        assert drug3["status"] == "已过期"

        # Verify mock was called
        mock_get_all_drugs.assert_called_once()


def test_get_stock_report_with_limit():
    """Test get_stock_report with limit parameter"""
    # Create more mock drugs to test limit
    mock_drugs = [
        {
            "drug_id": i,
            "name": f"Drug {i}",
            "quantity": 100,
            "expiry_date": 30,
            "shelve_id": i
        }
        for i in range(1, 21)  # 20 drugs
    ]

    with patch('tools.inventory.get_all_drugs') as mock_get_all_drugs:
        mock_get_all_drugs.return_value = mock_drugs

        # Test with limit=5
        result_json = inventory.get_stock_report(
            start_date="2025-01-01",
            end_date="2025-01-31",
            limit=5
        )

        result = json.loads(result_json)

        # Should only include 5 drugs due to limit
        assert len(result["drugs"]) == 5
        assert result["total_drugs"] == 20  # Total drugs available
        assert result["current_stock_summary"]["total_items"] == 20

        # Verify drugs are limited to first 5
        for i, drug in enumerate(result["drugs"], 1):
            assert drug["drug_id"] == i
            assert drug["drug_name"] == f"Drug {i}"

        # Test with limit=0 (no limit)
        result_json = inventory.get_stock_report(
            start_date="2025-01-01",
            end_date="2025-01-31",
            limit=0
        )

        result = json.loads(result_json)
        assert len(result["drugs"]) == 20  # All drugs included when limit=0


def test_get_stock_report_fallback():
    """Test get_stock_report fallback to mock data when drug_db fails"""
    with patch('tools.inventory.get_all_drugs') as mock_get_all_drugs:
        mock_get_all_drugs.side_effect = Exception("Database error")

        result_json = inventory.get_stock_report(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )

        result = json.loads(result_json)

        # Should fall back to mock data
        assert "stock_changes" in result  # Mock response has different structure
        assert "note" in result
        assert "获取真实库存数据失败" in result["note"]
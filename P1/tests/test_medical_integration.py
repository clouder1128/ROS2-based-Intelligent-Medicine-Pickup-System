import pytest
from unittest.mock import Mock, patch
import tools.medical as medical
import json


def test_submit_approval_integrated():
    """Test submit_approval uses HTTP client"""
    # Test with new function signature
    # Need to patch the import inside the function
    # The function imports: from utils.http_client import PharmacyHTTPClient
    with patch('utils.http_client.PharmacyHTTPClient') as mock_client_class:
        mock_client = Mock()
        mock_client.create_approval.return_value = "AP-20260407-ABCD1234"
        mock_client_class.return_value = mock_client

        approval_id = medical.submit_approval(
            patient_name="John Doe",
            advice="Take ibuprofen 200mg twice daily",
            patient_age=30,
            patient_weight=70.5,
            symptoms="Headache, fever",
            drug_name="Ibuprofen",
            drug_type="NSAID"
        )

        assert approval_id == "AP-20260407-ABCD1234"
        mock_client.create_approval.assert_called_once_with(
            patient_name="John Doe",
            advice="Take ibuprofen 200mg twice daily",
            patient_age=30,
            patient_weight=70.5,
            symptoms="Headache, fever",
            drug_name="Ibuprofen",
            drug_type="NSAID"
        )


def test_query_drug_integrated():
    """Test query_drug uses drug_db module"""
    # Mock drug_db module functions
    with patch('services.pharmacy_client.query_drug_by_name') as mock_query_by_name, \
         patch('services.pharmacy_client.query_drugs_by_symptom') as mock_query_by_symptom:

        # Test name query
        mock_drug = {
            "name": "Ibuprofen",
            "quantity": 100,
            "expiry_date": 365,
            "shelve_id": 1,
            "shelf_x": 2,
            "shelf_y": 3
        }
        mock_query_by_name.return_value = mock_drug
        mock_query_by_symptom.return_value = []

        result = medical.query_drug("Ibuprofen")
        data = json.loads(result)

        assert data["status"] == "success"
        assert len(data["drugs"]) == 1
        assert data["drugs"][0]["name"] == "Ibuprofen"
        assert data["drugs"][0]["stock"] == 100

        mock_query_by_name.assert_called_once_with("Ibuprofen")

    # Test symptom query
    with patch('services.pharmacy_client.query_drug_by_name') as mock_query_by_name, \
         patch('services.pharmacy_client.query_drugs_by_symptom') as mock_query_by_symptom:

        mock_drugs = [
            {
                "name": "Ibuprofen",
                "quantity": 100,
                "expiry_date": 365,
                "shelve_id": 1,
                "shelf_x": 2,
                "shelf_y": 3
            }
        ]
        mock_query_by_symptom.return_value = mock_drugs
        mock_query_by_name.return_value = None

        result = medical.query_drug("头痛")
        data = json.loads(result)

        assert data["status"] == "success"
        mock_query_by_symptom.assert_called_once_with("头痛")
"""
Mocked integration tests for CI environments
"""
import pytest
from unittest.mock import Mock, patch
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_pharmacy_client():
    """Fixture to mock PharmacyHTTPClient"""
    with patch('utils.http_client.PharmacyHTTPClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client

class TestMockedIntegration:
    """Integration tests with mocked backend"""

    def test_mocked_drug_queries(self, mock_pharmacy_client):
        """Test drug queries with mocked backend"""
        mock_pharmacy_client.get_drugs.return_value = [
            {"drug_id": 1, "name": "Mock Drug A", "quantity": 10},
            {"drug_id": 2, "name": "Mock Drug B", "quantity": 20}
        ]

        # Reload drug_db module to use the mocked client
        import importlib
        import services.pharmacy_client as drug_db
        importlib.reload(drug_db)

        drugs = drug_db.get_all_drugs()

        assert len(drugs) == 2
        assert drugs[0]['name'] == "Mock Drug A"

    def test_mocked_approval_workflow(self):
        """Test approval workflow with mocked backend"""
        with patch('utils.http_client.PharmacyHTTPClient') as mock_client_class:
            mock_client = Mock()
            mock_client.create_approval.return_value = "AP-20260407-MOCK123"
            mock_client_class.return_value = mock_client

            import tools.medical
            approval_id = tools.medical.submit_approval(
                patient_name="Mock Patient",
                advice="Mock advice"
            )

            assert approval_id == "AP-20260407-MOCK123"

    def test_mocked_inventory_functions(self, mock_pharmacy_client):
        """Test inventory functions with mocked backend"""
        mock_pharmacy_client.get_drugs.return_value = [
            {"drug_id": 1, "name": "Mock Drug A", "quantity": 10},
            {"drug_id": 2, "name": "Mock Drug B", "quantity": 20}
        ]

        # Reload drug_db module to use the mocked client
        import importlib
        import services.pharmacy_client as drug_db
        importlib.reload(drug_db)

        import tools.inventory
        import json

        # Test stock report
        report_json = tools.inventory.get_stock_report()
        report = json.loads(report_json)

        assert 'current_stock_summary' in report
        assert 'drugs' in report
        assert len(report['drugs']) == 2

    def test_complete_medical_consultation_flow(self):
        """Test complete medical consultation flow with mocks"""
        # Mock drug_db functions
        with patch('services.pharmacy_client.query_drug_by_name') as mock_query_by_name, \
             patch('services.pharmacy_client.query_drugs_by_symptom') as mock_query_by_symptom, \
             patch('utils.http_client.PharmacyHTTPClient') as mock_client_class:

            mock_client = Mock()
            mock_client.create_approval.return_value = "AP-20260407-MOCK456"
            mock_client_class.return_value = mock_client

            mock_drug = {
                "name": "Mock Drug",
                "quantity": 100,
                "expiry_date": 365,
                "shelve_id": 1,
                "shelf_x": 2,
                "shelf_y": 3
            }
            mock_query_by_name.return_value = mock_drug
            mock_query_by_symptom.return_value = [mock_drug]

            import tools.medical
            import json

            # Test drug query
            result = tools.medical.query_drug("Mock Drug")
            data = json.loads(result)
            assert data["status"] == "success"
            assert len(data["drugs"]) == 1

            # Test approval submission
            approval_id = tools.medical.submit_approval(
                patient_name="Test Patient",
                advice="Test advice",
                patient_age=30,
                symptoms="Test symptoms"
            )
            assert approval_id == "AP-20260407-MOCK456"
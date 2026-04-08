import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_pharmacy_client():
    """Fixture to mock PharmacyHTTPClient"""
    with patch('services.pharmacy_client.PharmacyHTTPClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client

def test_query_drugs_by_symptom_integrated(mock_pharmacy_client):
    """Test query_drugs_by_symptom uses HTTP client"""
    # Reload drug_db module to use the mocked client
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    mock_pharmacy_client.get_drugs.return_value = [
        {"drug_id": 1, "name": "Ibuprofen", "quantity": 50, "expiry_date": 100},
        {"drug_id": 2, "name": "Paracetamol", "quantity": 30, "expiry_date": 200}
    ]

    # Mock the symptom filtering logic
    with patch('services.pharmacy_client._filter_drugs_by_symptom') as mock_filter:
        mock_filter.return_value = [
            {"drug_id": 1, "name": "Ibuprofen", "quantity": 50, "expiry_date": 100}
        ]

        result = drug_db.query_drugs_by_symptom("headache")

        assert len(result) == 1
        assert result[0]['name'] == "Ibuprofen"
        mock_pharmacy_client.get_drugs.assert_called_once()

def test_query_drug_by_name_integrated(mock_pharmacy_client):
    """Test query_drug_by_name uses HTTP client"""
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    mock_pharmacy_client.get_drugs.return_value = [
        {"drug_id": 1, "name": "Ibuprofen", "quantity": 50, "expiry_date": 100}
    ]

    result = drug_db.query_drug_by_name("Ibuprofen")

    assert result is not None
    assert result['name'] == "Ibuprofen"
    mock_pharmacy_client.get_drugs.assert_called_once_with(name_filter="Ibuprofen")

def test_get_all_drugs_integrated(mock_pharmacy_client):
    """Test get_all_drugs uses HTTP client"""
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    mock_pharmacy_client.get_drugs.return_value = [
        {"drug_id": 1, "name": "Ibuprofen", "quantity": 50},
        {"drug_id": 2, "name": "Paracetamol", "quantity": 30}
    ]

    result = drug_db.get_all_drugs()

    assert len(result) == 2
    mock_pharmacy_client.get_drugs.assert_called_once()

def test_search_drugs_integrated(mock_pharmacy_client):
    """Test search_drugs uses HTTP client"""
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    mock_pharmacy_client.get_drugs.return_value = [
        {"drug_id": 1, "name": "Ibuprofen", "quantity": 50}
    ]

    result = drug_db.search_drugs("ibu")

    assert len(result) == 1
    assert result[0]['name'] == "Ibuprofen"
    mock_pharmacy_client.get_drugs.assert_called_once_with(name_filter="ibu")

def test_get_low_stock_drugs_integrated(mock_pharmacy_client):
    """Test get_low_stock_drugs uses HTTP client"""
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    mock_pharmacy_client.get_drugs.return_value = [
        {"drug_id": 1, "name": "Ibuprofen", "quantity": 40},
        {"drug_id": 2, "name": "Paracetamol", "quantity": 60},
        {"drug_id": 3, "name": "Aspirin", "quantity": 20}
    ]

    result = drug_db.get_low_stock_drugs(threshold=50)

    # Should return drugs with quantity < 50
    assert len(result) == 2
    drug_names = {drug['name'] for drug in result}
    assert "Ibuprofen" in drug_names
    assert "Aspirin" in drug_names
    assert "Paracetamol" not in drug_names
    mock_pharmacy_client.get_drugs.assert_called_once()

def test_update_stock_integrated(mock_pharmacy_client):
    """Test update_stock uses HTTP client for 'out' transactions"""
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    mock_pharmacy_client.create_order.return_value = {"success": True, "order_id": "123"}

    result = drug_db.update_stock(drug_id=1, quantity=5, transaction_type='out')

    assert result is True
    mock_pharmacy_client.create_order.assert_called_once_with([{"id": 1, "num": 5}])

def test_update_stock_integration_not_implemented(mock_pharmacy_client):
    """Test update_stock returns False for 'in' transactions (not implemented)"""
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    result = drug_db.update_stock(drug_id=1, quantity=5, transaction_type='in')

    # 'in' transactions are not implemented yet
    assert result is False
    mock_pharmacy_client.create_order.assert_not_called()

def test_health_check_integrated(mock_pharmacy_client):
    """Test health_check uses HTTP client"""
    import importlib
    import services.pharmacy_client as drug_db
    importlib.reload(drug_db)

    mock_pharmacy_client.health_check.return_value = {
        "backend_available": True,
        "ros2_connected": True,
        "success": True
    }

    result = drug_db.health_check()

    assert result["status"] == "connected"
    assert result["backend_available"] is True
    mock_pharmacy_client.health_check.assert_called_once()
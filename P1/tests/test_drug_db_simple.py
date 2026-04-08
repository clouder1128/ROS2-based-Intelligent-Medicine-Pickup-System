#!/usr/bin/env python3
"""
Simple tests for drug_db integration without complex mocking.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch
import services.pharmacy_client as drug_db

def test_drug_db_structure():
    """Test that drug_db has the expected functions"""
    # Check that drug_db has the expected functions
    expected_functions = [
        'query_drugs_by_symptom',
        'query_drug_by_name',
        'update_stock',
        'get_low_stock_drugs',
        'get_all_drugs',
        'search_drugs',
        'add_drug',
        'delete_drug',
        'health_check',
        '_filter_drugs_by_symptom',
        '_get_client'
    ]

    for func_name in expected_functions:
        assert hasattr(drug_db, func_name), f"drug_db missing function: {func_name}"

    print("✓ All expected functions exist in drug_db")

def test_mock_integration():
    """Test that drug_db uses PharmacyHTTPClient"""
    # Create a mock client
    mock_client = Mock()

    # Mock the get_drugs method
    mock_client.get_drugs.return_value = [
        {"drug_id": 1, "name": "Test Drug", "quantity": 100}
    ]

    # Mock the health_check method
    mock_client.health_check.return_value = {
        "success": True,
        "backend_available": True
    }

    # Patch the _get_client function to return our mock
    with patch.object(drug_db, '_get_client', return_value=mock_client):
        # Test get_all_drugs
        result = drug_db.get_all_drugs()
        assert len(result) == 1
        assert result[0]['name'] == "Test Drug"
        mock_client.get_drugs.assert_called_once()

        # Reset mock
        mock_client.get_drugs.reset_mock()

        # Test health_check
        result = drug_db.health_check()
        assert result["status"] == "connected"
        assert result["backend_available"] is True
        mock_client.health_check.assert_called_once()

    print("✓ Mock integration test passed")

def test_filter_drugs_by_symptom():
    """Test the symptom filtering function"""
    test_drugs = [
        {"name": "Ibuprofen", "quantity": 50},
        {"name": "Paracetamol", "quantity": 30},
        {"name": "Amoxicillin", "quantity": 20}
    ]

    # Test with headache symptom (should match Ibuprofen and Paracetamol based on keywords)
    result = drug_db._filter_drugs_by_symptom(test_drugs, "头痛")
    # Since the function looks for Chinese symptoms and English drug names,
    # and "头痛" maps to ["ibuprofen", "paracetamol", "aspirin"]
    # It should match Ibuprofen (contains "ibuprofen") and Paracetamol (contains "paracetamol")
    drug_names = [drug['name'] for drug in result]
    assert "Ibuprofen" in drug_names
    assert "Paracetamol" in drug_names
    assert "Amoxicillin" not in drug_names

    print("✓ Symptom filtering test passed")

def test_update_stock_logic():
    """Test update_stock function logic"""
    mock_client = Mock()

    # Test 'out' transaction
    mock_client.create_order.return_value = {"success": True}
    with patch.object(drug_db, '_get_client', return_value=mock_client):
        result = drug_db.update_stock(drug_id=1, quantity=5, transaction_type='out')
        assert result is True
        mock_client.create_order.assert_called_once_with([{"id": 1, "num": 5}])

    # Test 'in' transaction (not implemented)
    mock_client.create_order.reset_mock()
    with patch.object(drug_db, '_get_client', return_value=mock_client):
        result = drug_db.update_stock(drug_id=1, quantity=5, transaction_type='in')
        assert result is False  # Should return False for 'in' transactions
        mock_client.create_order.assert_not_called()

    print("✓ Update stock logic test passed")

if __name__ == "__main__":
    print("Running drug_db integration tests...")
    print("=" * 50)

    test_drug_db_structure()
    test_mock_integration()
    test_filter_drugs_by_symptom()
    test_update_stock_logic()

    print("=" * 50)
    print("All tests passed!")
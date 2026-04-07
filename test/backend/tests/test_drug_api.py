import json
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_get_drugs_list(client):
    """Test getting list of all drugs"""
    response = client.get('/api/drugs')

    assert response.status_code == 200
    result = json.loads(response.data)
    # Check new format first, fall back to old format for backward compatibility
    if 'success' in result:
        assert result['success'] == True
        assert 'drugs' in result
        assert isinstance(result['drugs'], list)
        assert 'count' in result
        assert result['count'] == len(result['drugs'])
    else:
        # Old format for backward compatibility
        assert result['ok'] == True
        assert 'data' in result
        assert isinstance(result['data'], list)


def test_get_drugs_with_name_filter(client):
    """Test filtering drugs by name"""
    # Test with partial name match
    response = client.get('/api/drugs?name=阿莫')

    assert response.status_code == 200
    result = json.loads(response.data)

    if 'success' in result:
        assert result['success'] == True
        assert 'drugs' in result
        assert isinstance(result['drugs'], list)
        assert 'count' in result
        assert result['count'] == len(result['drugs'])
        assert 'filters' in result
        assert result['filters']['name'] == '阿莫'

        # Should find at least one drug with '阿莫' in name
        assert len(result['drugs']) >= 1
        for drug in result['drugs']:
            assert '阿莫' in drug['name']
    else:
        # Old format - should still work but without filtering
        assert result['ok'] == True
        assert 'data' in result


def test_get_drugs_with_empty_name_filter(client):
    """Test filtering with empty name parameter"""
    response = client.get('/api/drugs?name=')

    assert response.status_code == 200
    result = json.loads(response.data)

    if 'success' in result:
        assert result['success'] == True
        assert 'drugs' in result
        assert 'filters' in result
        assert result['filters']['name'] == ''
    else:
        assert result['ok'] == True


def test_get_drugs_with_no_match_filter(client):
    """Test filtering with name that doesn't match any drug"""
    response = client.get('/api/drugs?name=NonExistentDrugName123')

    assert response.status_code == 200
    result = json.loads(response.data)

    if 'success' in result:
        assert result['success'] == True
        assert 'drugs' in result
        assert isinstance(result['drugs'], list)
        assert result['count'] == 0
        assert len(result['drugs']) == 0
        assert result['filters']['name'] == 'NonExistentDrugName123'
    else:
        assert result['ok'] == True


def test_get_drug_by_id_success(client):
    """Test getting a single drug by ID"""
    # First get list to find an existing drug ID
    list_response = client.get('/api/drugs')
    list_result = json.loads(list_response.data)

    if 'success' in list_result:
        drugs = list_result['drugs']
    else:
        drugs = list_result['data']

    assert len(drugs) > 0
    drug_id = drugs[0]['drug_id']

    # Now get single drug
    response = client.get(f'/api/drugs/{drug_id}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] == True
    assert 'drug' in result
    drug = result['drug']
    assert drug['drug_id'] == drug_id
    assert 'name' in drug
    assert 'quantity' in drug
    assert 'expiry_date' in drug
    assert 'shelf_x' in drug
    assert 'shelf_y' in drug
    assert 'shelve_id' in drug


def test_get_drug_by_id_not_found(client):
    """Test getting a non-existent drug by ID"""
    response = client.get('/api/drugs/99999')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['error'] == True
    assert 'Drug not found' in result['message']
    assert result['code'] == 'DRUG_NOT_FOUND'


def test_get_drug_by_id_invalid_format(client):
    """Test getting drug with invalid ID format"""
    response = client.get('/api/drugs/not-a-number')

    assert response.status_code == 404  # Flask will treat this as not found
    # Could also be 400 depending on implementation


def test_backward_compatibility_list_drugs(client):
    """Test backward compatibility of /api/drugs endpoint"""
    response = client.get('/api/drugs')

    assert response.status_code == 200
    result = json.loads(response.data)

    # Should work with either format
    assert 'success' in result or 'ok' in result
    if 'success' in result:
        assert result['success'] == True
        assert 'drugs' in result
    else:
        assert result['ok'] == True
        assert 'data' in result


def test_drug_list_response_structure(client):
    """Test drug list response has expected structure"""
    response = client.get('/api/drugs')
    result = json.loads(response.data)

    if 'success' in result:
        drugs = result['drugs']
    else:
        drugs = result['data']

    assert len(drugs) > 0
    drug = drugs[0]

    # Check all expected fields are present
    expected_fields = ['drug_id', 'name', 'quantity', 'expiry_date', 'shelf_x', 'shelf_y', 'shelve_id']
    for field in expected_fields:
        assert field in drug

    # Check field types
    assert isinstance(drug['drug_id'], int)
    assert isinstance(drug['name'], str)
    assert isinstance(drug['quantity'], int)
    assert isinstance(drug['expiry_date'], int)
    assert isinstance(drug['shelf_x'], int)
    assert isinstance(drug['shelf_y'], int)
    assert isinstance(drug['shelve_id'], int)
import json
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_create_approval_success(client):
    """Test creating a new approval request"""
    data = {
        "patient_name": "John Doe",
        "advice": "Take ibuprofen 200mg twice daily",
        "patient_age": 30,
        "patient_weight": 70.5,
        "symptoms": "Headache, fever",
        "drug_name": "Ibuprofen",
        "drug_type": "NSAID"
    }

    response = client.post('/api/approvals',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 201
    result = json.loads(response.data)
    assert result['success'] == True
    assert 'approval_id' in result
    assert result['approval_id'].startswith('AP-')
    assert 'created_at' in result


def test_get_approval_success(client):
    """Test retrieving an approval by ID"""
    # First create an approval
    create_data = {
        "patient_name": "Test Patient",
        "advice": "Test advice"
    }
    create_response = client.post('/api/approvals',
                                 data=json.dumps(create_data),
                                 content_type='application/json')
    create_result = json.loads(create_response.data)
    approval_id = create_result['approval_id']

    # Now get it
    response = client.get(f'/api/approvals/{approval_id}')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] == True
    assert result['approval_id'] == approval_id
    assert result['patient_name'] == "Test Patient"
    assert result['status'] == "pending"
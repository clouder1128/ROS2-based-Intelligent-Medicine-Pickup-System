import json
import pytest
from main import app


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
    assert 'approval' in result
    approval = result['approval']
    assert approval['approval_id'] == approval_id
    assert approval['patient_name'] == "Test Patient"
    assert approval['status'] == "pending"


def test_create_approval_missing_required_fields(client):
    """Test creating approval with missing required fields"""
    # Test missing patient_name
    data = {
        "advice": "Take medication"
    }
    response = client.post('/api/approvals',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['success'] == False
    assert result['ok'] == False
    assert 'Missing required field' in result['error']
    assert 'patient_name' in result['error']

    # Test missing advice
    data = {
        "patient_name": "John Doe"
    }
    response = client.post('/api/approvals',
                          data=json.dumps(data),
                          content_type='application/json')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['success'] == False
    assert result['ok'] == False
    assert 'Missing required field' in result['error']
    assert 'advice' in result['error']


def test_get_approval_not_found(client):
    """Test retrieving a non-existent approval"""
    response = client.get('/api/approvals/NONEXISTENT-123')

    assert response.status_code == 404
    result = json.loads(response.data)
    assert result['success'] == False
    assert result['ok'] == False
    assert 'Approval not found' in result['error']
    assert result['code'] == 'NOT_FOUND'


def test_create_approval_invalid_json(client):
    """Test creating approval with invalid JSON"""
    # Test with empty body
    response = client.post('/api/approvals',
                          data='',
                          content_type='application/json')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['success'] == False
    assert result['ok'] == False
    assert 'Invalid JSON data provided' in result['error']
    assert result['code'] == 'INVALID_JSON'

    # Test with malformed JSON
    response = client.post('/api/approvals',
                          data='{invalid json',
                          content_type='application/json')

    assert response.status_code == 400
    result = json.loads(response.data)
    assert result['success'] == False
    assert result['ok'] == False
    assert 'Invalid JSON data provided' in result['error']
    assert result['code'] == 'INVALID_JSON'


def test_get_pending_approvals(client):
    """Test retrieving pending approvals list"""
    # Create a pending approval
    create_data = {
        "patient_name": "Pending Test",
        "advice": "Pending advice"
    }
    client.post('/api/approvals',
               data=json.dumps(create_data),
               content_type='application/json')

    # Get pending list
    response = client.get('/api/approvals/pending')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] == True
    assert 'approvals' in result
    assert isinstance(result['approvals'], list)
    # Should have at least our pending approval
    assert len(result['approvals']) >= 1
    assert result['approvals'][0]['status'] == 'pending'


def test_approve_approval(client):
    """Test approving an approval"""
    # Create a pending approval
    create_data = {
        "patient_name": "Approve Test",
        "advice": "Approve this"
    }
    create_response = client.post('/api/approvals',
                                 data=json.dumps(create_data),
                                 content_type='application/json')
    create_result = json.loads(create_response.data)
    approval_id = create_result['approval_id']

    # Approve it
    approve_data = {
        "doctor_id": "dr_smith",
        "notes": "Approved with dosage adjustment"
    }
    response = client.post(f'/api/approvals/{approval_id}/approve',
                          data=json.dumps(approve_data),
                          content_type='application/json')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] == True
    assert result['message'] == "Approval approved successfully"

    # Verify status changed
    get_response = client.get(f'/api/approvals/{approval_id}')
    get_result = json.loads(get_response.data)
    assert get_result['approval']['status'] == 'approved'
    assert get_result['approval']['doctor_id'] == 'dr_smith'


def test_reject_approval(client):
    """Test rejecting an approval"""
    # Create a pending approval
    create_data = {
        "patient_name": "Reject Test",
        "advice": "Reject this"
    }
    create_response = client.post('/api/approvals',
                                 data=json.dumps(create_data),
                                 content_type='application/json')
    create_result = json.loads(create_response.data)
    approval_id = create_result['approval_id']

    # Reject it
    reject_data = {
        "doctor_id": "dr_jones",
        "reason": "Patient has contraindication"
    }
    response = client.post(f'/api/approvals/{approval_id}/reject',
                          data=json.dumps(reject_data),
                          content_type='application/json')

    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['success'] == True
    assert result['message'] == "Approval rejected successfully"

    # Verify status changed
    get_response = client.get(f'/api/approvals/{approval_id}')
    get_result = json.loads(get_response.data)
    assert get_result['approval']['status'] == 'rejected'
    assert get_result['approval']['doctor_id'] == 'dr_jones'
    assert get_result['approval']['reject_reason'] == "Patient has contraindication"
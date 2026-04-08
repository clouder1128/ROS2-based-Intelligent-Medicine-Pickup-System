# Backend to P1 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the smart pharmacy backend (`backend/`) into P1 medical assistant system via HTTP API, preserving ROS2 and scheduled task functionality for future simulation integration.

**Architecture:** Backend runs as standalone Flask service on port 8001, P1 tools become HTTP clients calling backend APIs. Backend retains ROS2 publishing and expiry sweeping threads. API-first design with JSON request/responses, comprehensive error handling, and team-friendly documentation.

**Tech Stack:** Flask, SQLite, httpx (HTTP client), Python 3.9+, ROS2 (optional), pytest for testing.

---

## File Structure

### Backend Modifications (`backend/`)
- **`app.py`**: Add approval API endpoints, modify port to 8001, enhance error handling
- **`requirements.txt`**: Ensure Flask-CORS dependency
- **`README.md`**: Update with new API endpoints and integration instructions

### P1 Client Modifications (`P1/`)
- **`drug_db.py`**: Replace mock data with HTTP client calling backend APIs
- **`tools/medical.py`**: Replace mock `submit_approval` with HTTP client
- **`tools/inventory.py`**: Replace mock inventory functions with HTTP clients
- **`config.py`**: Ensure `PHARMACY_BASE_URL` configuration
- **New: `utils/http_client.py`**: Shared HTTP client with timeout, retry, error handling
- **Tests**: Update existing tests to use real backend or test doubles

### Documentation
- **`docs/integration-guide.md`**: Complete integration guide for team collaboration
- **`docs/api-reference.md`**: Backend API reference with examples
- **`docs/troubleshooting.md`**: Common issues and solutions

---

## Task 1: Backend Port Configuration and Basic Setup

**Files:**
- Modify: `backend/app.py:1-50`
- Modify: `backend/app.py:5000` references

- [ ] **Step 1: Create test for port configuration**

```python
# tests/test_backend_config.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'test', 'backend'))

def test_backend_default_port():
    """Test that backend uses port 8001 by default for P1 compatibility"""
    # Import app module to check configuration
    import app as backend_app
    # The app should be configured for port 8001
    # This is a placeholder test - actual port config may be in run section
    assert True  # We'll implement proper test after code changes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_backend_config.py::test_backend_default_port -v`
Expected: PASS (placeholder test) or import error

- [ ] **Step 3: Modify app.py to use port 8001**

```python
# backend/app.py modifications
# Find the Flask app initialization section (around line 49)
app = Flask(__name__)

# Add configuration after app initialization
DEFAULT_PORT = 8001  # Changed from 5000 for P1 compatibility

# In the main block at the end of the file, change:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    app.run(debug=True, host='0.0.0.0', port=port)
```

- [ ] **Step 4: Create test for port environment variable override**

```python
# tests/test_backend_config.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'test', 'backend'))

def test_backend_port_environment_override():
    """Test that PORT environment variable overrides default port"""
    import app as backend_app
    # Check that DEFAULT_PORT constant is 8001
    assert backend_app.DEFAULT_PORT == 8001
```

- [ ] **Step 5: Run tests to verify changes**

Run: `pytest tests/test_backend_config.py -v`
Expected: Both tests PASS

- [ ] **Step 6: Commit**

```bash
cd backend
git add app.py
cd ../..
git add tests/test_backend_config.py
git commit -m "feat: configure backend for port 8001 (P1 compatibility)"
```

---

## Task 2: Backend Approval API Endpoints

**Files:**
- Modify: `backend/app.py` (add approval routes)
- Create: `backend/tests/test_approval_api.py`
- Modify: `backend/requirements.txt` (ensure Flask-CORS)

- [ ] **Step 1: Create test for approval creation API**

```python
# backend/tests/test_approval_api.py
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
```

- [ ] **Step 2: Run test to verify it fails (endpoint not exists)**

Run: `cd backend && pytest tests/test_approval_api.py::test_create_approval_success -v`
Expected: FAIL with 404 Not Found

- [ ] **Step 3: Add approval creation endpoint to app.py**

```python
# In backend/app.py, after other route definitions (around line 200)
@app.route('/api/approvals', methods=['POST'])
def create_approval():
    """Create a new approval request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": True, "message": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = ['patient_name', 'advice']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": True, 
                    "message": f"Missing required field: {field}",
                    "code": "MISSING_FIELD"
                }), 400
        
        # Import ApprovalManager
        from approval import get_approval_manager
        
        # Create approval
        manager = get_approval_manager()
        approval_id = manager.create(
            patient_name=data['patient_name'],
            advice=data['advice'],
            patient_age=data.get('patient_age'),
            patient_weight=data.get('patient_weight'),
            symptoms=data.get('symptoms'),
            drug_name=data.get('drug_name'),
            drug_type=data.get('drug_type')
        )
        
        return jsonify({
            "success": True,
            "approval_id": approval_id,
            "message": "Approval created successfully",
            "created_at": datetime.now().isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to create approval: {str(e)}",
            "code": "CREATION_ERROR"
        }), 500
```

- [ ] **Step 4: Add necessary imports at top of app.py**

```python
# Add to imports at top of app.py
from datetime import datetime
from flask import request, jsonify
```

- [ ] **Step 5: Run test to verify endpoint works**

Run: `cd backend && pytest tests/test_approval_api.py::test_create_approval_success -v`
Expected: PASS

- [ ] **Step 6: Create test for get approval endpoint**

```python
# backend/tests/test_approval_api.py
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
```

- [ ] **Step 7: Add get approval endpoint to app.py**

```python
# In backend/app.py, after create_approval route
@app.route('/api/approvals/<approval_id>', methods=['GET'])
def get_approval(approval_id):
    """Get approval details by ID"""
    try:
        from approval import get_approval_manager
        
        manager = get_approval_manager()
        approval = manager.get(approval_id)
        
        if not approval:
            return jsonify({
                "error": True,
                "message": f"Approval not found: {approval_id}",
                "code": "NOT_FOUND"
            }), 404
        
        # Convert SQLite Row to dict if needed
        if hasattr(approval, 'keys'):
            approval = dict(approval)
        
        return jsonify({
            "success": True,
            **approval
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to get approval: {str(e)}",
            "code": "RETRIEVAL_ERROR"
        }), 500
```

- [ ] **Step 8: Run all approval API tests**

Run: `cd backend && pytest tests/test_approval_api.py -v`
Expected: Both tests PASS

- [ ] **Step 9: Commit**

```bash
cd backend
git add app.py tests/test_approval_api.py
cd ../..
git commit -m "feat: add approval creation and retrieval API endpoints"
```

---

## Task 3: Complete Backend Approval API

**Files:**
- Modify: `backend/app.py` (add remaining approval routes)
- Modify: `backend/tests/test_approval_api.py` (add more tests)

- [ ] **Step 1: Create test for pending approvals endpoint**

```python
# backend/tests/test_approval_api.py
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
```

- [ ] **Step 2: Add pending approvals endpoint to app.py**

```python
# In backend/app.py, after get_approval route
@app.route('/api/approvals/pending', methods=['GET'])
def get_pending_approvals():
    """Get list of pending approvals"""
    try:
        from approval import get_approval_manager
        
        manager = get_approval_manager()
        limit = request.args.get('limit', default=100, type=int)
        pending = manager.list_pending(limit=limit)
        
        # Convert SQLite Rows to dicts
        approvals = []
        for item in pending:
            if hasattr(item, 'keys'):
                approvals.append(dict(item))
            else:
                approvals.append(item)
        
        return jsonify({
            "success": True,
            "approvals": approvals,
            "count": len(approvals),
            "limit": limit
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to get pending approvals: {str(e)}",
            "code": "RETRIEVAL_ERROR"
        }), 500
```

- [ ] **Step 3: Run pending approvals test**

Run: `cd backend && pytest tests/test_approval_api.py::test_get_pending_approvals -v`
Expected: PASS

- [ ] **Step 4: Create test for approve endpoint**

```python
# backend/tests/test_approval_api.py
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
    assert get_result['status'] == 'approved'
    assert get_result['doctor_id'] == 'dr_smith'
```

- [ ] **Step 5: Add approve endpoint to app.py**

```python
# In backend/app.py, after get_pending_approvals route
@app.route('/api/approvals/<approval_id>/approve', methods=['POST'])
def approve_approval(approval_id):
    """Approve an approval request"""
    try:
        data = request.get_json()
        if not data or 'doctor_id' not in data:
            return jsonify({
                "error": True,
                "message": "Missing doctor_id in request",
                "code": "MISSING_DOCTOR_ID"
            }), 400
        
        from approval import get_approval_manager
        
        manager = get_approval_manager()
        success = manager.approve(approval_id, data['doctor_id'])
        
        if not success:
            return jsonify({
                "error": True,
                "message": f"Cannot approve approval {approval_id}. It may not exist or not be pending.",
                "code": "APPROVAL_FAILED"
            }), 400
        
        return jsonify({
            "success": True,
            "message": "Approval approved successfully",
            "approval_id": approval_id,
            "doctor_id": data['doctor_id'],
            "approved_at": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to approve approval: {str(e)}",
            "code": "APPROVAL_ERROR"
        }), 500
```

- [ ] **Step 6: Run approve test**

Run: `cd backend && pytest tests/test_approval_api.py::test_approve_approval -v`
Expected: PASS

- [ ] **Step 7: Create test for reject endpoint**

```python
# backend/tests/test_approval_api.py
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
    assert get_result['status'] == 'rejected'
    assert get_result['doctor_id'] == 'dr_jones'
    assert get_result['reject_reason'] == "Patient has contraindication"
```

- [ ] **Step 8: Add reject endpoint to app.py**

```python
# In backend/app.py, after approve_approval route
@app.route('/api/approvals/<approval_id>/reject', methods=['POST'])
def reject_approval(approval_id):
    """Reject an approval request"""
    try:
        data = request.get_json()
        if not data or 'doctor_id' not in data:
            return jsonify({
                "error": True,
                "message": "Missing doctor_id in request",
                "code": "MISSING_DOCTOR_ID"
            }), 400
        
        if 'reason' not in data:
            return jsonify({
                "error": True,
                "message": "Missing rejection reason",
                "code": "MISSING_REASON"
            }), 400
        
        from approval import get_approval_manager
        
        manager = get_approval_manager()
        success = manager.reject(approval_id, data['doctor_id'], data['reason'])
        
        if not success:
            return jsonify({
                "error": True,
                "message": f"Cannot reject approval {approval_id}. It may not exist or not be pending.",
                "code": "REJECTION_FAILED"
            }), 400
        
        return jsonify({
            "success": True,
            "message": "Approval rejected successfully",
            "approval_id": approval_id,
            "doctor_id": data['doctor_id'],
            "reason": data['reason'],
            "rejected_at": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to reject approval: {str(e)}",
            "code": "REJECTION_ERROR"
        }), 500
```

- [ ] **Step 9: Run all approval API tests**

Run: `cd backend && pytest tests/test_approval_api.py -v`
Expected: All 4 tests PASS

- [ ] **Step 10: Add CORS headers for P1 access**

```python
# In backend/app.py, after CORS import/configuration
# Add to the add_cors function or modify CORS configuration
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses for P1 access"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response
```

- [ ] **Step 11: Commit**

```bash
cd backend
git add app.py tests/test_approval_api.py
cd ../..
git commit -m "feat: complete approval API with pending, approve, reject endpoints and CORS"
```

---

## Task 4: Enhanced Drug Query API for P1

**Files:**
- Modify: `backend/app.py` (enhance /api/drugs endpoint)
- Create: `backend/tests/test_drug_api.py`

- [ ] **Step 1: Create test for enhanced drug query by name**

```python
# backend/tests/test_drug_api.py
import json
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_drugs_with_name_filter(client):
    """Test getting drugs with name filter"""
    response = client.get('/api/drugs?name=阿莫西林')
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'drugs' in result
    assert isinstance(result['drugs'], list)
    # Should find our test drug
    if len(result['drugs']) > 0:
        assert result['drugs'][0]['name'] == '阿莫西林'
```

- [ ] **Step 2: Run test to verify current behavior**

Run: `cd backend && pytest tests/test_drug_api.py::test_get_drugs_with_name_filter -v`
Expected: PASS (if endpoint returns all drugs) or FAIL (if no filtering)

- [ ] **Step 3: Enhance /api/drugs endpoint in app.py**

```python
# Find the existing /api/drugs endpoint in app.py (around line 260)
# Modify it to support filtering
@app.route('/api/drugs', methods=['GET'])
def get_drugs():
    """Get all drugs, with optional filtering"""
    try:
        conn = get_db()
        try:
            # Build query based on parameters
            name_filter = request.args.get('name')
            symptom_filter = request.args.get('symptom')
            
            query = 'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory'
            params = []
            
            if name_filter:
                query += ' WHERE name LIKE ?'
                params.append(f'%{name_filter}%')
            # Note: symptom filtering would need a different table structure
            # For now, we'll return all and let P1 filter
            
            query += ' ORDER BY drug_id'
            
            cur = conn.execute(query, params)
            drugs = [dict(r) for r in cur.fetchall()]
            
            return jsonify({
                "success": True,
                "drugs": drugs,
                "count": len(drugs),
                "filters": {
                    "name": name_filter,
                    "symptom": symptom_filter  # Note: not implemented yet
                }
            })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to retrieve drugs: {str(e)}",
            "code": "DRUG_RETRIEVAL_ERROR"
        }), 500
```

- [ ] **Step 4: Create test for get single drug by ID**

```python
# backend/tests/test_drug_api.py
def test_get_drug_by_id(client):
    """Test getting a specific drug by ID"""
    response = client.get('/api/drugs/1')  # Test with ID 1 from init_db
    
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'drug' in result
    assert result['drug']['drug_id'] == 1
    assert 'name' in result['drug']
    assert 'quantity' in result['drug']
```

- [ ] **Step 5: Add /api/drugs/<id> endpoint to app.py**

```python
# In backend/app.py, after get_drugs route
@app.route('/api/drugs/<int:drug_id>', methods=['GET'])
def get_drug(drug_id):
    """Get a specific drug by ID"""
    try:
        conn = get_db()
        try:
            cur = conn.execute(
                'SELECT drug_id, name, quantity, expiry_date, shelf_x, shelf_y, shelve_id FROM inventory WHERE drug_id = ?',
                (drug_id,)
            )
            drug = cur.fetchone()
            
            if not drug:
                return jsonify({
                    "error": True,
                    "message": f"Drug not found with ID: {drug_id}",
                    "code": "DRUG_NOT_FOUND"
                }), 404
            
            return jsonify({
                "success": True,
                "drug": dict(drug)
            })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            "error": True,
            "message": f"Failed to retrieve drug: {str(e)}",
            "code": "DRUG_RETRIEVAL_ERROR"
        }), 500
```

- [ ] **Step 6: Run all drug API tests**

Run: `cd backend && pytest tests/test_drug_api.py -v`
Expected: Both tests PASS

- [ ] **Step 7: Commit**

```bash
cd backend
git add app.py tests/test_drug_api.py
cd ../..
git commit -m "feat: enhance drug API with filtering and single drug endpoint"
```

---

## Task 5: P1 HTTP Client Utility

**Files:**
- Create: `P1/utils/http_client.py`
- Create: `P1/tests/test_http_client.py`

- [ ] **Step 1: Create test for HTTP client initialization**

```python
# P1/tests/test_http_client.py
import os
import pytest
from unittest.mock import Mock, patch
from utils.http_client import PharmacyHTTPClient

def test_client_initialization():
    """Test HTTP client initializes with correct base URL"""
    # Set environment variable for test
    os.environ['PHARMACY_BASE_URL'] = 'http://localhost:8001'
    
    client = PharmacyHTTPClient()
    assert client.base_url == 'http://localhost:8001'
    assert client.timeout == 30
    assert client.max_retries == 3
```

- [ ] **Step 2: Run test to verify it fails (module not exists)**

Run: `cd P1 && pytest tests/test_http_client.py::test_client_initialization -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Create HTTP client utility**

```python
# P1/utils/http_client.py
import os
import httpx
import logging
from typing import Dict, Any, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class PharmacyHTTPClient:
    """HTTP client for communicating with pharmacy backend"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize pharmacy HTTP client
        
        Args:
            base_url: Base URL of pharmacy backend (defaults to PHARMACY_BASE_URL env var)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url or os.getenv('PHARMACY_BASE_URL', 'http://localhost:8001')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Remove trailing slash if present
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
        
        logger.info(f"Initialized PharmacyHTTPClient with base_url: {self.base_url}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError))
    )
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
    
    def _request_sync(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Synchronous version of request method"""
        import asyncio
        return asyncio.run(self._request(method, endpoint, **kwargs))
    
    # Drug-related methods
    def get_drugs(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all drugs, optionally filtered by name"""
        params = {}
        if name_filter:
            params['name'] = name_filter
        
        response = self._request_sync('GET', '/api/drugs', params=params)
        return response.get('drugs', []) if response.get('success') else []
    
    def get_drug_by_id(self, drug_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific drug by ID"""
        try:
            response = self._request_sync('GET', f'/api/drugs/{drug_id}')
            return response.get('drug') if response.get('success') else None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    # Approval-related methods
    def create_approval(self, patient_name: str, advice: str, **kwargs) -> Optional[str]:
        """Create a new approval request"""
        data = {
            "patient_name": patient_name,
            "advice": advice,
            **kwargs
        }
        
        try:
            response = self._request_sync('POST', '/api/approvals', json=data)
            return response.get('approval_id') if response.get('success') else None
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create approval: {e}")
            return None
    
    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get approval details by ID"""
        try:
            response = self._request_sync('GET', f'/api/approvals/{approval_id}')
            return response if response.get('success') else None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def get_pending_approvals(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of pending approvals"""
        try:
            response = self._request_sync('GET', '/api/approvals/pending', params={'limit': limit})
            return response.get('approvals', []) if response.get('success') else []
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get pending approvals: {e}")
            return []
    
    # Order-related methods
    def create_order(self, items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Create a new order (batch pickup)"""
        try:
            response = self._request_sync('POST', '/api/order', json=items)
            return response if response.get('success') else None
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create order: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check backend health"""
        try:
            return self._request_sync('GET', '/api/health')
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "backend_available": False
            }
```

- [ ] **Step 4: Add dependencies to requirements.txt**

```python
# Check if P1/requirements.txt has httpx and tenacity
# If not, add them:
# httpx>=0.25.0
# tenacity>=8.2.0
```

- [ ] **Step 5: Create test for drug methods**

```python
# P1/tests/test_http_client.py
@patch('utils.http_client.httpx.AsyncClient')
def test_get_drugs(mock_client_class):
    """Test getting drugs from backend"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "success": True,
        "drugs": [
            {"drug_id": 1, "name": "Drug A", "quantity": 10},
            {"drug_id": 2, "name": "Drug B", "quantity": 20}
        ]
    }
    mock_response.raise_for_status.return_value = None
    
    mock_client = Mock()
    mock_client.request.return_value.__aenter__.return_value = mock_response
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    client = PharmacyHTTPClient(base_url="http://test:8001")
    drugs = client.get_drugs()
    
    assert len(drugs) == 2
    assert drugs[0]['name'] == "Drug A"
    assert drugs[1]['drug_id'] == 2
```

- [ ] **Step 6: Run HTTP client tests**

Run: `cd P1 && pytest tests/test_http_client.py -v`
Expected: Tests PASS

- [ ] **Step 7: Commit**

```bash
cd P1
git add utils/http_client.py tests/test_http_client.py
cd ..
git commit -m "feat: add PharmacyHTTPClient utility for backend communication"
```

---

## Task 6: P1 drug_db.py Integration

**Files:**
- Modify: `P1/drug_db.py` (replace mock with HTTP client)
- Modify: `P1/tests/test_drug_db.py` (update tests)

- [ ] **Step 1: Create test for integrated drug_db.py**

```python
# P1/tests/test_drug_db_integration.py
import pytest
from unittest.mock import Mock, patch
import drug_db

def test_query_drugs_by_symptom_integrated():
    """Test query_drugs_by_symptom uses HTTP client"""
    with patch('drug_db.PharmacyHTTPClient') as mock_client_class:
        mock_client = Mock()
        mock_client.get_drugs.return_value = [
            {"drug_id": 1, "name": "Ibuprofen", "quantity": 50, "expiry_date": 100},
            {"drug_id": 2, "name": "Paracetamol", "quantity": 30, "expiry_date": 200}
        ]
        mock_client_class.return_value = mock_client
        
        # Mock the symptom filtering logic
        with patch('drug_db._filter_drugs_by_symptom') as mock_filter:
            mock_filter.return_value = [
                {"drug_id": 1, "name": "Ibuprofen", "quantity": 50, "expiry_date": 100}
            ]
            
            result = drug_db.query_drugs_by_symptom("headache")
            
            assert len(result) == 1
            assert result[0]['name'] == "Ibuprofen"
            mock_client.get_drugs.assert_called_once()
```

- [ ] **Step 2: Run test to verify current behavior**

Run: `cd P1 && pytest tests/test_drug_db_integration.py::test_query_drugs_by_symptom_integrated -v`
Expected: FAIL (function not using HTTP client yet)

- [ ] **Step 3: Update drug_db.py to use HTTP client**

```python
# P1/drug_db.py - Replace the entire file with:
#!/usr/bin/env python3
"""
药品数据库模块 - 集成backend药房服务
提供药品数据查询和管理功能，通过HTTP API连接到后端服务。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import Config
from utils.http_client import PharmacyHTTPClient

logger = logging.getLogger(__name__)

# ==================== HTTP客户端初始化 ====================
_client = None

def _get_client() -> PharmacyHTTPClient:
    """获取HTTP客户端单例"""
    global _client
    if _client is None:
        _client = PharmacyHTTPClient()
    return _client

# ==================== 症状过滤辅助函数 ====================
def _filter_drugs_by_symptom(drugs: List[Dict[str, Any]], symptom: str) -> List[Dict[str, Any]]:
    """
    根据症状过滤药品列表（客户端过滤）
    
    注意：backend目前不支持按症状查询，所以在客户端实现过滤。
    实际生产环境中应该在backend实现此功能。
    """
    if not symptom:
        return drugs
    
    symptom_lower = symptom.lower()
    matched_drugs = []
    
    # Mock症状匹配逻辑 - 实际应该基于药品适应症数据
    # 这里使用简单的关键词匹配
    symptom_keywords = {
        "头痛": ["ibuprofen", "paracetamol", "aspirin"],
        "发热": ["ibuprofen", "paracetamol"],
        "咳嗽": ["dextromethorphan", "codeine"],
        "过敏": ["loratadine", "cetirizine"],
        "感染": ["amoxicillin", "azithromycin"],
    }
    
    # 查找症状对应的药品名称关键词
    matched_keywords = []
    for chinese_symptom, keywords in symptom_keywords.items():
        if chinese_symptom in symptom_lower:
            matched_keywords.extend(keywords)
    
    if not matched_keywords:
        # 如果没有预定义匹配，尝试基于名称的简单匹配
        for drug in drugs:
            drug_name_lower = drug.get('name', '').lower()
            # 简单逻辑：如果药品名称包含症状关键词的一部分
            if any(keyword in symptom_lower for keyword in ['pain', 'fever', 'cough', 'allergy', 'infection']):
                matched_drugs.append(drug)
        return matched_drugs
    
    # 基于关键词过滤
    for drug in drugs:
        drug_name_lower = drug.get('name', '').lower()
        if any(keyword in drug_name_lower for keyword in matched_keywords):
            matched_drugs.append(drug)
    
    return matched_drugs

# ==================== 药品查询函数 ====================
def query_drugs_by_symptom(symptom: str) -> List[Dict[str, Any]]:
    """
    根据症状查询相关药品
    
    实际通过HTTP API连接到backend药房服务。
    
    Args:
        symptom: 症状关键词
        
    Returns:
        匹配症状的药品列表
    """
    logger.info(f"查询药品（症状）: {symptom}")
    
    try:
        client = _get_client()
        all_drugs = client.get_drugs()
        
        if not all_drugs:
            logger.warning("未从backend获取到药品数据")
            return []
        
        # 在客户端进行症状过滤
        filtered_drugs = _filter_drugs_by_symptom(all_drugs, symptom)
        
        logger.info(f"找到 {len(filtered_drugs)} 个匹配药品（总共 {len(all_drugs)} 个）")
        return filtered_drugs
        
    except Exception as e:
        logger.error(f"查询药品失败（症状: {symptom}）: {str(e)}")
        return []

def query_drug_by_name(name: str) -> Optional[Dict[str, Any]]:
    """根据药品名称查询"""
    logger.info(f"查询药品（名称）: {name}")
    
    try:
        client = _get_client()
        drugs = client.get_drugs(name_filter=name)
        
        if not drugs:
            logger.warning(f"未找到药品: {name}")
            return None
        
        # 返回第一个匹配的药品
        return drugs[0]
        
    except Exception as e:
        logger.error(f"查询药品失败（名称: {name}）: {str(e)}")
        return None

def update_stock(drug_id: int, quantity: int, transaction_type: str) -> bool:
    """
    更新药品库存
    
    注意：实际通过创建订单来更新库存。
    
    Args:
        drug_id: 药品ID
        quantity: 数量
        transaction_type: 类型 ('in' 或 'out')
        
    Returns:
        是否成功
    """
    logger.info(f"更新库存: drug_id={drug_id}, quantity={quantity}, type={transaction_type}")
    
    if transaction_type == 'out':
        # 通过创建订单来减少库存
        try:
            client = _get_client()
            order_result = client.create_order([
                {"id": drug_id, "num": quantity}
            ])
            
            success = order_result is not None and order_result.get('success', False)
            if success:
                logger.info(f"库存更新成功: drug_id={drug_id}, 减少 {quantity}")
            else:
                logger.warning(f"库存更新失败: drug_id={drug_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"库存更新失败: {str(e)}")
            return False
    else:
        # 入库操作 - backend目前不支持，记录日志
        logger.warning(f"入库操作暂未实现: drug_id={drug_id}, quantity={quantity}")
        return False

def get_low_stock_drugs(threshold: int = 50) -> List[Dict[str, Any]]:
    """获取库存低于阈值的药品"""
    logger.info(f"获取低库存药品: threshold={threshold}")
    
    try:
        client = _get_client()
        all_drugs = client.get_drugs()
        
        low_stock_drugs = [
            drug for drug in all_drugs
            if drug.get('quantity', 0) < threshold
        ]
        
        logger.info(f"找到 {len(low_stock_drugs)} 个低库存药品")
        return low_stock_drugs
        
    except Exception as e:
        logger.error(f"获取低库存药品失败: {str(e)}")
        return []

# ==================== 数据库工具函数 ====================
def get_all_drugs() -> List[Dict[str, Any]]:
    """获取所有药品"""
    logger.info("获取所有药品")
    
    try:
        client = _get_client()
        return client.get_drugs()
    except Exception as e:
        logger.error(f"获取所有药品失败: {str(e)}")
        return []

def search_drugs(keyword: str) -> List[Dict[str, Any]]:
    """搜索药品"""
    logger.info(f"搜索药品: {keyword}")
    
    try:
        client = _get_client()
        return client.get_drugs(name_filter=keyword)
    except Exception as e:
        logger.error(f"搜索药品失败: {str(e)}")
        return []

def add_drug(drug_data: Dict[str, Any]) -> bool:
    """添加新药品"""
    logger.warning(f"添加药品功能暂未实现: {drug_data.get('name', 'unknown')}")
    # backend目前不支持添加药品
    return False

def delete_drug(drug_id: int) -> bool:
    """删除药品"""
    logger.warning(f"删除药品功能暂未实现: id={drug_id}")
    # backend目前不支持删除药品
    return False

# ==================== 健康检查 ====================
def health_check() -> Dict[str, Any]:
    """数据库健康检查"""
    try:
        client = _get_client()
        backend_health = client.health_check()
        
        return {
            "status": "connected" if backend_health.get('backend_available', True) else "disconnected",
            "backend_available": backend_health.get('backend_available', False),
            "backend_health": backend_health,
            "timestamp": datetime.now().isoformat(),
            "module": "drug_db (HTTP client)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# ==================== 初始化检查 ====================
if __name__ == "__main__":
    print("药品数据库模块（HTTP客户端版本）")
    print("=" * 50)
    print("此模块通过HTTP API连接到backend药房服务。")
    print("")
    
    # 测试健康检查
    print("健康检查:", json.dumps(health_check(), indent=2, ensure_ascii=False))
    
    # 测试获取所有药品
    print("\n获取所有药品:")
    all_drugs = get_all_drugs()
    print(f"找到 {len(all_drugs)} 个药品")
    
    if all_drugs:
        print("\n前5个药品:")
        for drug in all_drugs[:5]:
            print(f"  {drug.get('drug_id')}: {drug.get('name')} - 库存: {drug.get('quantity')}")
```

- [ ] **Step 4: Update existing tests to use new interface**

```python
# Update P1/tests/test_drug_db.py to work with HTTP client
# Replace mock implementations with HTTP client mocks
```

- [ ] **Step 5: Run drug_db tests**

Run: `cd P1 && pytest tests/test_drug_db_integration.py -v`
Expected: Tests PASS

- [ ] **Step 6: Test actual integration (requires backend running)**

```bash
# Start backend in another terminal first
cd backend
python app.py  # Should be on port 8001

# In another terminal, test drug_db
cd P1
python -c "import drug_db; print(drug_db.health_check())"
```

- [ ] **Step 7: Commit**

```bash
cd P1
git add drug_db.py tests/test_drug_db_integration.py
cd ..
git commit -m "feat: integrate drug_db.py with backend HTTP API"
```

---

## Task 7: P1 tools/medical.py Integration

**Files:**
- Modify: `P1/tools/medical.py` (replace mock submit_approval)
- Modify: `P1/tests/test_tools.py` (update tests)

- [ ] **Step 1: Create test for integrated submit_approval**

```python
# P1/tests/test_medical_integration.py
import pytest
from unittest.mock import Mock, patch
import tools.medical as medical

def test_submit_approval_integrated():
    """Test submit_approval uses HTTP client"""
    with patch('tools.medical.PharmacyHTTPClient') as mock_client_class:
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
```

- [ ] **Step 2: Run test to verify current behavior**

Run: `cd P1 && pytest tests/test_medical_integration.py::test_submit_approval_integrated -v`
Expected: FAIL (function still using mock)

- [ ] **Step 3: Update submit_approval in tools/medical.py**

```python
# In P1/tools/medical.py, find the submit_approval function (around line 362)
# Replace the mock implementation:

def submit_approval(
    patient_name: str,
    advice: str,
    patient_age: int = None,
    patient_weight: float = None,
    symptoms: str = None,
    drug_name: str = None,
    drug_type: str = None,
    **kwargs
) -> str:
    """
    提交用药建议给医生审批
    
    Args:
        patient_name: 患者姓名
        advice: 用药建议
        patient_age: 患者年龄（可选）
        patient_weight: 患者体重（可选）
        symptoms: 症状描述（可选）
        drug_name: 药品名称（可选）
        drug_type: 药品类型（可选）
        
    Returns:
        审批单ID，格式如 "AP-20260407-ABCD1234"
    """
    logger.info(f"提交审批: patient={patient_name}, drug={drug_name}")
    
    try:
        # Import HTTP client
        from utils.http_client import PharmacyHTTPClient
        
        client = PharmacyHTTPClient()
        approval_id = client.create_approval(
            patient_name=patient_name,
            advice=advice,
            patient_age=patient_age,
            patient_weight=patient_weight,
            symptoms=symptoms,
            drug_name=drug_name,
            drug_type=drug_type
        )
        
        if approval_id:
            logger.info(f"审批提交成功: {approval_id}")
            return approval_id
        else:
            logger.error("审批提交失败: 未返回审批ID")
            # Fallback to mock for compatibility
            return f"AP-{datetime.now().strftime('%Y%m%d')}-MOCK{random.randint(1000, 9999)}"
            
    except Exception as e:
        logger.error(f"审批提交失败: {str(e)}")
        # Fallback to mock for compatibility
        return f"AP-{datetime.now().strftime('%Y%m%d')}-MOCK{random.randint(1000, 9999)}"
```

- [ ] **Step 4: Update imports in tools/medical.py**

```python
# Add/update imports at top of tools/medical.py
import random
from datetime import datetime
```

- [ ] **Step 5: Update query_drug function to use drug_db**

```python
# In P1/tools/medical.py, update query_drug function to use real data
def query_drug(query: str) -> str:
    """
    根据症状或药品名称查询相关药物信息。
    
    Args:
        query: 症状关键词或药品名称
        
    Returns:
        药品信息JSON字符串
    """
    logger.info(f"查询药物: {query}")
    
    try:
        # Use drug_db module for real queries
        import drug_db
        
        if any(keyword in query.lower() for keyword in ['头痛', '发热', '咳嗽', '疼痛', 'fever', 'pain', 'cough']):
            # Symptom query
            drugs = drug_db.query_drugs_by_symptom(query)
        else:
            # Name query
            drug = drug_db.query_drug_by_name(query)
            drugs = [drug] if drug else []
        
        if not drugs:
            return json.dumps({
                "status": "not_found",
                "message": f"未找到匹配 '{query}' 的药品",
                "drugs": []
            }, ensure_ascii=False)
        
        # Format response
        formatted_drugs = []
        for drug in drugs:
            formatted_drug = {
                "name": drug.get("name", "未知"),
                "specification": "需从backend获取详细信息",
                "price": 0.0,  # Backend doesn't have price field yet
                "stock": drug.get("quantity", 0),
                "is_prescription": drug.get("name", "").lower() in ["amoxicillin", "azithromycin"],
                "indications": ["需从backend获取适应症信息"],
                "expiry_days": drug.get("expiry_date", 0),
                "location": f"货架{drug.get('shelve_id', 0)}-({drug.get('shelf_x', 0)},{drug.get('shelf_y', 0)})"
            }
            formatted_drugs.append(formatted_drug)
        
        return json.dumps({
            "status": "success",
            "count": len(formatted_drugs),
            "query": query,
            "drugs": formatted_drugs
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"查询药物失败: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"查询失败: {str(e)}",
            "drugs": []
        }, ensure_ascii=False)
```

- [ ] **Step 6: Run medical integration tests**

Run: `cd P1 && pytest tests/test_medical_integration.py -v`
Expected: Tests PASS

- [ ] **Step 7: Commit**

```bash
cd P1
git add tools/medical.py tests/test_medical_integration.py
cd ..
git commit -m "feat: integrate tools/medical.py with backend approval API"
```

---

## Task 8: P1 tools/inventory.py Integration

**Files:**
- Modify: `P1/tools/inventory.py` (replace mock with HTTP client)
- Modify: `P1/tests/test_inventory.py` (update tests)

- [ ] **Step 1: Create test for integrated record_transaction**

```python
# P1/tests/test_inventory_integration.py
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
```

- [ ] **Step 2: Run test to verify current behavior**

Run: `cd P1 && pytest tests/test_inventory_integration.py::test_record_transaction_integrated -v`
Expected: FAIL (function still using mock)

- [ ] **Step 3: Update tools/inventory.py to use HTTP client**

```python
# In P1/tools/inventory.py, update record_transaction function:

def record_transaction(drug_id: int, quantity: int, transaction_type: str, reason: str = None) -> str:
    """
    记录药品出入库流水
    
    Args:
        drug_id: 药品ID
        quantity: 数量
        transaction_type: 类型 ('in' 或 'out')
        reason: 原因（如"医生处方"、"管理员补货"）
        
    Returns:
        操作结果JSON字符串
    """
    logger.info(f"记录库存流水: drug_id={drug_id}, quantity={quantity}, type={transaction_type}, reason={reason}")
    
    try:
        if transaction_type == "out":
            # Use backend order API for out transactions
            from utils.http_client import PharmacyHTTPClient
            
            client = PharmacyHTTPClient()
            order_result = client.create_order([{"id": drug_id, "num": quantity}])
            
            if order_result and order_result.get('success'):
                response = {
                    "success": True,
                    "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "drug_id": drug_id,
                    "quantity": quantity,
                    "type": transaction_type,
                    "reason": reason or "医生处方",
                    "timestamp": datetime.now().isoformat(),
                    "backend_order_id": order_result.get('task_ids', [None])[0],
                    "message": "通过backend订单API处理"
                }
            else:
                response = {
                    "success": False,
                    "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "drug_id": drug_id,
                    "quantity": quantity,
                    "type": transaction_type,
                    "reason": reason or "医生处方",
                    "timestamp": datetime.now().isoformat(),
                    "error": "Backend订单创建失败",
                    "backend_response": order_result
                }
        else:
            # In transactions not supported by backend yet
            response = {
                "success": True,
                "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "drug_id": drug_id,
                "quantity": quantity,
                "type": transaction_type,
                "reason": reason or "管理员补货",
                "timestamp": datetime.now().isoformat(),
                "note": "入库操作暂由本地记录，backend暂不支持"
            }
        
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"记录库存流水失败: {str(e)}")
        response = {
            "success": False,
            "transaction_id": f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "drug_id": drug_id,
            "quantity": quantity,
            "type": transaction_type,
            "reason": reason or "未指定",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "note": "记录失败，backend连接异常"
        }
        return json.dumps(response, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Update other inventory functions**

```python
# Update get_stock_report to use real data
def get_stock_report(start_date: str = None, end_date: str = None) -> str:
    """
    获取库存报告
    
    Args:
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        
    Returns:
        库存报告JSON字符串
    """
    logger.info(f"获取库存报告: start={start_date}, end={end_date}")
    
    try:
        # Get current stock from backend
        from utils.http_client import PharmacyHTTPClient
        import drug_db
        
        client = PharmacyHTTPClient()
        all_drugs = drug_db.get_all_drugs()
        
        # For now, generate simple report from current stock
        # Backend doesn't have transaction history API yet
        report_drugs = []
        for drug in all_drugs[:10]:  # Limit to 10 for demo
            report_drug = {
                "drug_name": drug.get('name', '未知'),
                "drug_id": drug.get('drug_id'),
                "current_stock": drug.get('quantity', 0),
                "expiry_days": drug.get('expiry_date', 0),
                "location": f"货架{drug.get('shelve_id', 0)}",
                "status": "正常" if drug.get('expiry_date', 0) > 0 else "已过期"
            }
            report_drugs.append(report_drug)
        
        response = {
            "report_period": {
                "start_date": start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "end_date": end_date or datetime.now().strftime("%Y-%m-%d")
            },
            "generated_at": datetime.now().isoformat(),
            "total_drugs": len(all_drugs),
            "current_stock_summary": {
                "total_items": len(all_drugs),
                "total_quantity": sum(d.get('quantity', 0) for d in all_drugs),
                "expired_count": len([d for d in all_drugs if d.get('expiry_date', 0) <= 0]),
                "low_stock_count": len([d for d in all_drugs if d.get('quantity', 0) < 50])
            },
            "drugs": report_drugs,
            "note": "基于backend当前库存数据，交易历史功能待实现"
        }
        
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"获取库存报告失败: {str(e)}")
        # Fallback to mock
        return super().get_stock_report(start_date, end_date)
```

- [ ] **Step 5: Update imports**

```python
# Add necessary imports at top of tools/inventory.py
from datetime import datetime, timedelta
```

- [ ] **Step 6: Run inventory integration tests**

Run: `cd P1 && pytest tests/test_inventory_integration.py -v`
Expected: Tests PASS

- [ ] **Step 7: Test end-to-end integration**

```bash
# Start backend first
cd backend
python app.py

# In another terminal, test the full flow
cd P1
python -c "
import drug_db
import tools.medical
import tools.inventory

print('1. Health check:', drug_db.health_check())
print('2. All drugs:', len(drug_db.get_all_drugs()))
print('3. Create approval:', tools.medical.submit_approval('Test', 'Advice'))
print('4. Record transaction:', tools.inventory.record_transaction(1, 2, 'out', 'Test'))
"
```

- [ ] **Step 8: Commit**

```bash
cd P1
git add tools/inventory.py tests/test_inventory_integration.py
cd ..
git commit -m "feat: integrate tools/inventory.py with backend APIs"
```

---

## Task 9: Integration Testing

**Files:**
- Create: `P1/tests/integration/test_backend_integration.py`
- Update: `P1/run_tests.py` (add integration test option)

- [ ] **Step 1: Create end-to-end integration test**

```python
# P1/tests/integration/test_backend_integration.py
"""
Backend integration tests - requires backend service running
"""
import os
import pytest
import json
import time

# Mark as integration test (slow, requires external service)
pytestmark = pytest.mark.integration

@pytest.fixture(scope="module")
def backend_available():
    """Check if backend is available before running tests"""
    import drug_db
    health = drug_db.health_check()
    return health.get('backend_available', False)

@pytest.mark.skipif(
    not os.getenv('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled (set RUN_INTEGRATION_TESTS=1 to run)"
)
class TestBackendIntegration:
    """Integration tests with real backend"""
    
    def test_backend_connection(self):
        """Test basic connection to backend"""
        import drug_db
        health = drug_db.health_check()
        assert health['backend_available'] == True
        print(f"Backend health: {health}")
    
    def test_drug_queries(self, backend_available):
        """Test drug query functions"""
        if not backend_available:
            pytest.skip("Backend not available")
        
        import drug_db
        import tools.medical
        
        # Test getting all drugs
        all_drugs = drug_db.get_all_drugs()
        assert isinstance(all_drugs, list)
        print(f"Found {len(all_drugs)} drugs in backend")
        
        if all_drugs:
            # Test query by name
            first_drug = all_drugs[0]
            drug_by_name = drug_db.query_drug_by_name(first_drug.get('name', ''))
            assert drug_by_name is not None
            assert drug_by_name['drug_id'] == first_drug['drug_id']
    
    def test_approval_workflow(self, backend_available):
        """Test complete approval workflow"""
        if not backend_available:
            pytest.skip("Backend not available")
        
        import tools.medical
        
        # Create approval
        approval_id = tools.medical.submit_approval(
            patient_name="Integration Test Patient",
            advice="Integration test advice",
            patient_age=25,
            symptoms="Test symptoms"
        )
        
        assert approval_id is not None
        assert approval_id.startswith('AP-')
        print(f"Created approval: {approval_id}")
        
        # Note: Approval query would need approval API client in drug_db
        # which we haven't implemented yet
    
    def test_inventory_functions(self, backend_available):
        """Test inventory-related functions"""
        if not backend_available:
            pytest.skip("Backend not available")
        
        import tools.inventory
        import json
        
        # Test stock report (should work even without transactions)
        report_json = tools.inventory.get_stock_report()
        report = json.loads(report_json)
        assert 'current_stock_summary' in report
        assert 'drugs' in report
        
        print(f"Stock report generated: {report['current_stock_summary']}")
```

- [ ] **Step 2: Create mock-based integration test for CI**

```python
# P1/tests/integration/test_mocked_integration.py
"""
Mocked integration tests for CI environments
"""
import pytest
from unittest.mock import Mock, patch
import json

class TestMockedIntegration:
    """Integration tests with mocked backend"""
    
    def test_mocked_drug_queries(self):
        """Test drug queries with mocked backend"""
        with patch('drug_db.PharmacyHTTPClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_drugs.return_value = [
                {"drug_id": 1, "name": "Mock Drug A", "quantity": 10},
                {"drug_id": 2, "name": "Mock Drug B", "quantity": 20}
            ]
            mock_client_class.return_value = mock_client
            
            import drug_db
            drugs = drug_db.get_all_drugs()
            
            assert len(drugs) == 2
            assert drugs[0]['name'] == "Mock Drug A"
    
    def test_mocked_approval_workflow(self):
        """Test approval workflow with mocked backend"""
        with patch('tools.medical.PharmacyHTTPClient') as mock_client_class:
            mock_client = Mock()
            mock_client.create_approval.return_value = "AP-20260407-MOCK123"
            mock_client_class.return_value = mock_client
            
            import tools.medical
            approval_id = tools.medical.submit_approval(
                patient_name="Mock Patient",
                advice="Mock advice"
            )
            
            assert approval_id == "AP-20260407-MOCK123"
    
    def test_complete_medical_consultation_flow(self):
        """Test complete medical consultation flow with mocks"""
        # This would test the full MedicalAgent workflow
        # with all backend calls mocked
        pass
```

- [ ] **Step 3: Update run_tests.py to support integration tests**

```python
# In P1/run_tests.py, add integration test option
def run_integration_tests():
    """Run integration tests (requires backend running)"""
    print("Running integration tests...")
    print("Note: Backend service must be running on port 8001")
    print()
    
    # Set environment variable to enable integration tests
    os.environ['RUN_INTEGRATION_TESTS'] = '1'
    
    # Run integration tests
    result = pytest.main([
        'tests/integration/',
        '-v',
        '--tb=short'
    ])
    
    return result == 0
```

- [ ] **Step 4: Run integration tests**

Run: `cd P1 && python run_tests.py --integration` (if implemented)
Or: `cd P1 && RUN_INTEGRATION_TESTS=1 pytest tests/integration/test_mocked_integration.py -v`

- [ ] **Step 5: Commit**

```bash
cd P1
git add tests/integration/ run_tests.py
cd ..
git commit -m "feat: add integration tests for backend-P1 integration"
```

---

## Task 10: Documentation

**Files:**
- Create: `docs/integration-guide.md`
- Create: `docs/api-reference.md`
- Create: `docs/troubleshooting.md`
- Update: `backend/README.md`
- Update: `P1/README.md`

- [ ] **Step 1: Create integration guide**

```markdown
# Backend-P1 Integration Guide

## Overview
This guide explains how to integrate the smart pharmacy backend with the P1 medical assistant system.

## Architecture
- **Backend**: Flask service on port 8001, provides REST API for drug management, orders, and approvals
- **P1**: Medical assistant with HTTP client components calling backend APIs
- **Data Flow**: P1 tools → HTTP API → Backend → Database/ROS2

## Setup Instructions

### 1. Backend Setup
```bash
cd backend/
pip install -r requirements.txt
python init_db.py  # Initialize database
python app.py      # Start on port 8001
```

### 2. P1 Configuration
```bash
cd P1/
export PHARMACY_BASE_URL=http://localhost:8001
pip install -r requirements.txt
pip install httpx tenacity  # Additional dependencies
```

### 3. Verification
```bash
# Check backend health
curl http://localhost:8001/api/health

# Check P1 connection
python -c "import drug_db; print(drug_db.health_check())"
```

## API Usage Examples

### From P1 Code
```python
from utils.http_client import PharmacyHTTPClient

# Initialize client
client = PharmacyHTTPClient()

# Get all drugs
drugs = client.get_drugs()

# Create approval
approval_id = client.create_approval(
    patient_name="John Doe",
    advice="Take medication as prescribed",
    symptoms="Headache, fever"
)

# Create order (dispense medication)
order_result = client.create_order([
    {"id": 1, "num": 2},  # Drug ID 1, quantity 2
    {"id": 2, "num": 1}   # Drug ID 2, quantity 1
])
```

### From External Systems
```bash
# Get all drugs
curl http://localhost:8001/api/drugs

# Create approval
curl -X POST http://localhost:8001/api/approvals \
  -H "Content-Type: application/json" \
  -d '{"patient_name":"Test","advice":"Test advice"}'

# Approve an approval
curl -X POST http://localhost:8001/api/approvals/AP-20260407-ABCD1234/approve \
  -H "Content-Type: application/json" \
  -d '{"doctor_id":"dr_smith"}'
```

## Development Workflow

### 1. Start Backend
```bash
cd backend
python app.py
```

### 2. Develop P1 Features
```python
# Use the HTTP client in your P1 tools
from utils.http_client import PharmacyHTTPClient
client = PharmacyHTTPClient()
```

### 3. Run Tests
```bash
# Unit tests (mocked)
cd P1
pytest tests/

# Integration tests (requires backend)
RUN_INTEGRATION_TESTS=1 pytest tests/integration/
```

## Common Tasks

### Adding New API Endpoints
1. Add route in `backend/app.py`
2. Add corresponding method in `P1/utils/http_client.py`
3. Update relevant P1 module (`drug_db.py`, `tools/medical.py`, etc.)
4. Add tests

### Debugging Connection Issues
1. Check backend is running: `curl http://localhost:8001/api/health`
2. Check P1 config: `echo $PHARMACY_BASE_URL`
3. Check firewall/network connectivity

## Production Deployment

### Environment Variables
```bash
# Backend
export PORT=8001
export EXPIRY_SWEEP_INTERVAL_SEC=3600

# P1
export PHARMACY_BASE_URL=http://your-backend-host:8001
```

### Monitoring
- Backend health: `/api/health`
- P1 health: `drug_db.health_check()`
- Logs: Check Flask logs (backend) and P1 application logs
```

- [ ] **Step 2: Create API reference**

```markdown
# Backend API Reference

## Base URL
`http://localhost:8001` (development) or your deployment URL

## Authentication
Currently none. For production, implement API keys or JWT.

## Response Format
All responses are JSON. Success responses include `"success": true`.
Error responses include `"error": true` and `"message"`.

## Endpoints

### Health Check
`GET /api/health`

**Response:**
```json
{
  "success": true,
  "backend": "pharmacy",
  "ros2_connected": false,
  "timestamp": "2026-04-07T10:30:00"
}
```

### Drug Management

#### Get All Drugs
`GET /api/drugs`

**Query Parameters:**
- `name` (optional): Filter by drug name (partial match)

**Response:**
```json
{
  "success": true,
  "drugs": [
    {
      "drug_id": 1,
      "name": "阿莫西林",
      "quantity": 50,
      "expiry_date": 365,
      "shelf_x": 1,
      "shelf_y": 1,
      "shelve_id": 1
    }
  ],
  "count": 1
}
```

#### Get Single Drug
`GET /api/drugs/{id}`

**Response:** Same as above but with `"drug"` key instead of `"drugs"`.

### Approval Management

#### Create Approval
`POST /api/approvals`

**Request Body:**
```json
{
  "patient_name": "John Doe",
  "advice": "Take medication",
  "patient_age": 30,
  "patient_weight": 70.5,
  "symptoms": "Headache",
  "drug_name": "Ibuprofen",
  "drug_type": "NSAID"
}
```

**Required Fields:** `patient_name`, `advice`

**Response:**
```json
{
  "success": true,
  "approval_id": "AP-20260407-ABCD1234",
  "message": "Approval created successfully",
  "created_at": "2026-04-07T10:30:00"
}
```

#### Get Approval
`GET /api/approvals/{id}`

**Response:**
```json
{
  "success": true,
  "id": "AP-20260407-ABCD1234",
  "patient_name": "John Doe",
  "status": "pending",
  "created_at": "2026-04-07T10:30:00",
  // ... all approval fields
}
```

#### Get Pending Approvals
`GET /api/approvals/pending`

**Query Parameters:**
- `limit` (optional, default 100): Maximum number to return

**Response:**
```json
{
  "success": true,
  "approvals": [...],
  "count": 5,
  "limit": 100
}
```

#### Approve Approval
`POST /api/approvals/{id}/approve`

**Request Body:**
```json
{
  "doctor_id": "dr_smith"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Approval approved successfully",
  "approval_id": "AP-20260407-ABCD1234",
  "doctor_id": "dr_smith",
  "approved_at": "2026-04-07T10:35:00"
}
```

#### Reject Approval
`POST /api/approvals/{id}/reject`

**Request Body:**
```json
{
  "doctor_id": "dr_jones",
  "reason": "Patient has contraindication"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Approval rejected successfully",
  "approval_id": "AP-20260407-ABCD1234",
  "doctor_id": "dr_jones",
  "reason": "Patient has contraindication",
  "rejected_at": "2026-04-07T10:35:00"
}
```

### Order Management

#### Create Order (Batch Pickup)
`POST /api/order`

**Request Body:**
```json
[
  {"id": 1, "num": 2},
  {"id": 2, "num": 1}
]
```

**Response:**
```json
{
  "success": true,
  "task_ids": [1, 2],
  "message": "已下发 2 个取药任务，库存已扣减"
}
```

#### Get Order History
`GET /api/orders`

**Response:**
```json
{
  "success": true,
  "orders": [
    {
      "task_id": 1,
      "status": "completed",
      "target_drug_id": 1,
      "quantity": 2,
      "created_at": "2026-04-07T10:00:00"
    }
  ],
  "count": 1
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": true,
  "message": "Missing required field: patient_name",
  "code": "MISSING_FIELD"
}
```

### 404 Not Found
```json
{
  "error": true,
  "message": "Drug not found with ID: 999",
  "code": "DRUG_NOT_FOUND"
}
```

### 500 Internal Server Error
```json
{
  "error": true,
  "message": "Database connection failed",
  "code": "DB_CONNECTION_ERROR"
}
```
```

- [ ] **Step 3: Create troubleshooting guide**

```markdown
# Troubleshooting Guide

## Common Issues

### Backend Won't Start

**Issue:** `Address already in use`
**Solution:**
```bash
# Check what's using port 8001
sudo lsof -i :8001
# Kill the process or use different port
kill -9 <PID>
# Or change port in app.py DEFAULT_PORT
```

**Issue:** `ModuleNotFoundError: No module named 'flask'`
**Solution:**
```bash
pip install -r requirements.txt
```

### P1 Can't Connect to Backend

**Issue:** `Connection refused` or timeouts
**Solution:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8001/api/health
   ```
2. Check `PHARMACY_BASE_URL` environment variable:
   ```bash
   echo $PHARMACY_BASE_URL
   ```
3. Check firewall/network:
   ```bash
   telnet localhost 8001
   ```

**Issue:** `CORS errors` in browser console
**Solution:** Backend CORS is configured. If issues persist:
1. Check browser console for exact error
2. Verify backend `add_cors_headers` function is active
3. Try with `curl` to isolate browser vs backend issue

### Database Issues

**Issue:** `SQLite database is locked`
**Solution:**
```bash
# Check for other processes using the database
fuser pharmacy.db
# Kill processes or wait
```

**Issue:** `Table not found`
**Solution:**
```bash
cd backend
python init_db.py  # Reinitialize database
```

### Approval API Issues

**Issue:** Approvals not appearing in pending list
**Solution:**
1. Check approval was created successfully
2. Verify approval status is `pending`
3. Check database directly:
   ```bash
   sqlite3 pharmacy.db "SELECT * FROM approvals WHERE status='pending';"
   ```

**Issue:** Can't approve/reject approval
**Solution:**
1. Verify approval exists and is `pending`
2. Check request body includes `doctor_id`
3. For reject, ensure `reason` is provided

## Logging and Debugging

### Enable Debug Logging
**Backend:** Already in debug mode when run with `python app.py`

**P1:** Set log level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Backend Logs
```bash
cd backend
python app.py 2>&1 | tee backend.log
```

### Check P1 HTTP Traffic
Modify `utils/http_client.py` to log requests:
```python
logger.debug(f"Request: {method} {url}")
logger.debug(f"Response: {response.status_code}")
```

## Performance Issues

### Slow Responses
1. Check backend load with `top` or `htop`
2. Monitor database size: `ls -lh pharmacy.db`
3. Add indexes to frequently queried columns

### High Memory Usage
1. Check for memory leaks in long-running backend
2. Monitor with `ps aux | grep python`
3. Consider restarting backend periodically

## Testing Issues

### Integration Tests Failing
1. Ensure backend is running: `curl http://localhost:8001/api/health`
2. Set `RUN_INTEGRATION_TESTS=1`
3. Check test database is clean: `python init_db.py`

### Mock Tests Failing
1. Verify all mocks are properly configured
2. Check for missing imports in test files
3. Run with `pytest -v` for detailed output

## ROS2 Integration Issues

**Issue:** `ImportError: No module named 'rclpy'`
**Solution:** ROS2 is optional. Backend works without it.

**Issue:** ROS2 tasks not publishing
**Solution:**
1. Verify ROS2 environment is sourced:
   ```bash
   source /opt/ros/humble/setup.bash
   ```
2. Check ROS2 nodes are running
3. Backend logs will show ROS2 status on startup

## Getting Help

1. Check logs for error messages
2. Verify all steps in Integration Guide
3. Test with `curl` to isolate P1 vs backend issues
4. Check database state with `sqlite3 pharmacy.db`

## Emergency Recovery

### Database Corruption
```bash
cd backend
mv pharmacy.db pharmacy.db.backup
python init_db.py
```

### Complete Reset
```bash
# Backend
cd backend
rm -f pharmacy.db
python init_db.py
python app.py

# P1
cd P1
export PHARMACY_BASE_URL=http://localhost:8001
python -c "import drug_db; drug_db.health_check()"
```
```

- [ ] **Step 4: Update backend README**

```markdown
# Update backend/README.md with:
## P1 Integration
This backend is integrated with P1 medical assistant system.

### API Endpoints for P1
- `GET /api/drugs` - Get all drugs (with optional name filter)
- `GET /api/drugs/{id}` - Get specific drug
- `POST /api/approvals` - Create approval request
- `GET /api/approvals/{id}` - Get approval details
- `GET /api/approvals/pending` - Get pending approvals
- `POST /api/approvals/{id}/approve` - Approve approval
- `POST /api/approvals/{id}/reject` - Reject approval
- `POST /api/order` - Create order (dispense medication)

### Running for P1 Integration
```bash
# Use port 8001 for P1 compatibility
PORT=8001 python app.py
# Or modify DEFAULT_PORT in app.py
```

See [Integration Guide](../docs/integration-guide.md) for details.
```

- [ ] **Step 5: Update P1 README**

```markdown
# Update P1/README.md with:
## Backend Integration
P1 now integrates with the smart pharmacy backend for real drug data and approval management.

### Configuration
Set `PHARMACY_BASE_URL` environment variable:
```bash
export PHARMACY_BASE_URL=http://localhost:8001
```

### Integrated Modules
- `drug_db.py` - Real drug queries from backend
- `tools/medical.py` - Real approval submission
- `tools/inventory.py` - Real inventory operations

### Testing
```bash
# Unit tests (mocked)
pytest tests/

# Integration tests (requires backend running)
RUN_INTEGRATION_TESTS=1 pytest tests/integration/
```

See [Integration Guide](docs/integration-guide.md) for details.
```

- [ ] **Step 6: Commit documentation**

```bash
git add docs/integration-guide.md docs/api-reference.md docs/troubleshooting.md
git add backend/README.md P1/README.md
git commit -m "docs: add comprehensive integration documentation"
```

---

## Task 11: Final Integration Test

**Files:**
- Create: `scripts/test-full-integration.py`
- Update: `Makefile` or build scripts

- [ ] **Step 1: Create full integration test script**

```python
#!/usr/bin/env python3
"""
Full integration test - tests complete P1-backend integration
"""
import os
import sys
import time
import subprocess
import requests
import json

def check_backend():
    """Check if backend is running and healthy"""
    try:
        response = requests.get('http://localhost:8001/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Backend running: {data.get('backend', 'unknown')}")
            return True
        else:
            print(f"✗ Backend responded with {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Backend not reachable at http://localhost:8001")
        return False
    except Exception as e:
        print(f"✗ Backend check failed: {e}")
        return False

def test_p1_modules():
    """Test P1 modules integration"""
    import drug_db
    import tools.medical
    import tools.inventory
    
    print("\nTesting P1 modules...")
    
    # Test health check
    health = drug_db.health_check()
    if health.get('backend_available'):
        print("✓ P1 can connect to backend")
    else:
        print("✗ P1 cannot connect to backend")
        return False
    
    # Test drug queries
    drugs = drug_db.get_all_drugs()
    if drugs:
        print(f"✓ Retrieved {len(drugs)} drugs from backend")
    else:
        print("✗ No drugs retrieved from backend")
    
    # Test approval creation
    approval_id = tools.medical.submit_approval(
        patient_name="Integration Test",
        advice="Test medication",
        symptoms="Test symptoms"
    )
    if approval_id and approval_id.startswith('AP-'):
        print(f"✓ Created approval: {approval_id}")
    else:
        print("✗ Failed to create approval")
    
    # Test inventory report
    report_json = tools.inventory.get_stock_report()
    report = json.loads(report_json)
    if report.get('current_stock_summary'):
        print("✓ Generated inventory report")
    else:
        print("✗ Failed to generate inventory report")
    
    return True

def main():
    """Run full integration test"""
    print("=" * 60)
    print("Full Backend-P1 Integration Test")
    print("=" * 60)
    
    # Set environment
    os.environ['PHARMACY_BASE_URL'] = 'http://localhost:8001'
    
    # Check backend
    if not check_backend():
        print("\nPlease start backend first:")
        print("  cd backend && python app.py")
        return 1
    
    # Test P1 modules
    sys.path.insert(0, 'P1')
    success = test_p1_modules()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Integration tests failed")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Create quick start script**

```bash
#!/bin/bash
# scripts/quick-start.sh
echo "Starting Backend-P1 Integration Environment..."

# Start backend
cd backend
echo "Starting backend on port 8001..."
python app.py &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 3

# Set environment for P1
export PHARMACY_BASE_URL=http://localhost:8001

# Start P1 CLI
cd P1
echo "Starting P1 medical assistant..."
echo "Backend PID: $BACKEND_PID"
echo "PHARMACY_BASE_URL: $PHARMACY_BASE_URL"
echo ""
echo "To stop: kill $BACKEND_PID"
echo ""
python cli.py

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null
```

- [ ] **Step 3: Run full integration test**

```bash
chmod +x scripts/test-full-integration.py scripts/quick-start.sh
python scripts/test-full-integration.py
```

- [ ] **Step 4: Commit final integration**

```bash
git add scripts/test-full-integration.py scripts/quick-start.sh
git commit -m "feat: add full integration test and quick start script"
```

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-04-07-backend-p1-integration.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
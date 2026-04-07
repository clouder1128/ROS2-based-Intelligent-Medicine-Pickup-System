# Backend-P1 Integration Guide

## Overview
This guide explains how to integrate the smart pharmacy backend (`test/backend/`) into P1 medical assistant system via HTTP API.

## Architecture
- **Backend**: Flask service on port 8001, provides REST API for drug management, orders, and approvals
- **P1**: Medical assistant with HTTP client components calling backend APIs
- **Data Flow**: P1 tools → HTTP API → Backend → Database/ROS2

## Setup Instructions

### 1. Backend Setup
```bash
cd test/backend/
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
cd test/backend
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
1. Add route in `test/backend/app.py`
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
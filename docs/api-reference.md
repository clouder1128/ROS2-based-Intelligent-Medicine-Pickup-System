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
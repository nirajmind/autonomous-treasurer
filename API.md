# 📚 API Documentation

The Autonomous Treasurer exposes a comprehensive REST API for managing financial operations.

## Quick Access

- **Interactive Docs:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## Authentication

All protected endpoints require a JWT token in the `Authorization` header:

```bash
# 1. Get token
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# 2. Use token in requests
curl -H "Authorization: Bearer <access_token>" \
  http://localhost:8000/api/dashboard
```

---

## Endpoints

### Public Endpoints (No Auth Required)

#### Health Checks

**GET /health**

```bash
curl http://localhost:8000/health
```

Basic health check. Returns 200 if app is running.

**GET /health/live**

```bash
curl http://localhost:8000/health/live
```

Kubernetes liveness probe. Returns 200 if app is alive.

**GET /health/ready**

```bash
curl http://localhost:8000/health/ready
```

Kubernetes readiness probe. Checks database, Redis, blockchain connectivity.

Response:

```json
{
  "status": "healthy",
  "timestamp": "2025-12-21T10:30:45.123456",
  "version": "1.0.0",
  "services": {
    "database": {"status": "healthy", "type": "PostgreSQL"},
    "redis": {"status": "healthy", "type": "Redis"},
    "blockchain": {"status": "healthy", "block_number": 12345}
  }
}
```

#### Authentication

**POST /token**

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Request:

- `username`: Admin username
- `password`: Admin password

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

### Protected Endpoints (Requires JWT Token)

#### Dashboard

**GET /api/dashboard**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/dashboard
```

Returns current treasury status and runway metrics.

Response:

```json
{
  "status": "Online",
  "treasury_balance": 15000.50,
  "currency": "MNEE",
  "monthly_burn": 5000.0,
  "runway_months": 3.0,
  "alerts": []
}
```

**GET /api/dashboard/logs**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/dashboard/logs
```

Returns transaction history and agent decisions (live from Redis or fallback to PostgreSQL).

Response:

```json
[
  {
    "timestamp": "2025-12-21T10:30:45",
    "vendor": "Acme Corp",
    "amount": 1500.0,
    "status": "APPROVED",
    "tx_hash": "0x...",
    "agent_thought": "Amount below limit, auto-approved"
  },
  {
    "timestamp": "2025-12-21T10:25:30",
    "vendor": "Premium Service",
    "amount": 5000.0,
    "status": "PAUSED_FOR_APPROVAL",
    "approval_id": "APR-001",
    "agent_thought": "Exceeds limit, requires human review"
  }
]
```

#### Invoice Processing

**POST /api/process-invoice**

```bash
curl -X POST http://localhost:8000/api/process-invoice \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Invoice #INV-001\nVendor: Acme Corp\nAmount: $1,500.00\nDate: 2025-12-21"
  }'
```

Processes a raw invoice text and automatically handles payment based on policy.

Request:

```json
{
  "raw_text": "Invoice text here (max 100KB)"
}
```

Response (Auto-Approved):

```json
{
  "status": "APPROVED",
  "tx_hash": "0x123abc...",
  "vendor": "Acme Corp",
  "amount": 1500.0,
  "balance": 13500.5,
  "runway_months": 2.7
}
```

Response (Requires Approval):

```json
{
  "status": "PAUSED_FOR_APPROVAL",
  "approval_id": "APR-001",
  "vendor": "Premium Service",
  "amount": 5000.0,
  "reason": "Amount exceeds auto-approval limit of $2,000"
}
```

#### Spending Limits

**GET /api/settings/limits**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/settings/limits
```

Get current spending policy settings.

Response:

```json
{
  "auto_approval_limit": 2000.0,
  "critical_runway_months": 2,
  "currency": "MNEE"
}
```

**POST /api/settings/limits**

```bash
curl -X POST http://localhost:8000/api/settings/limits \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_limit": 5000.0}'
```

Update auto-approval spending limit (admin only).

#### Metrics

**GET /metrics**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/metrics
```

Get application performance metrics.

Response:

```json
{
  "invoices_processed": 42,
  "transactions_approved": 38,
  "transactions_rejected": 4,
  "total_amount_processed": 45000.50,
  "api_requests": 342,
  "errors": 2,
  "start_time": "2025-12-21T09:00:00"
}
```

**POST /metrics/reset**

```bash
curl -X POST http://localhost:8000/metrics/reset \
  -H "Authorization: Bearer $TOKEN"
```

Reset metrics counters (admin only).

---

## Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Invoice approved, dashboard retrieved |
| 201 | Created | New resource created |
| 202 | Accepted | Invoice pending approval |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing JWT token |
| 403 | Forbidden | Invalid credentials |
| 404 | Not Found | Endpoint doesn't exist |
| 422 | Validation Error | Input failed validation |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Unexpected error |
| 503 | Service Unavailable | Database/Redis down |

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": {
    "code": "POLICY_VIOLATION",
    "message": "Amount exceeds auto-approval limit",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-21T10:30:45",
    "details": {
      "limit": 2000.0,
      "requested": 5000.0
    }
  }
}
```

---

## Request Headers

| Header | Required | Example |
|--------|----------|---------|
| `Authorization` | For protected endpoints | `Bearer eyJ0eXAi...` |
| `Content-Type` | For POST requests | `application/json` |
| `X-Request-ID` | Optional (auto-generated) | `550e8400-e29b...` |

---

## Rate Limiting

All endpoints are rate-limited to **100 requests per minute per IP address**.

Response headers include:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
Retry-After: 60
```

When limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## Examples

### Example 1: Complete Invoice Processing Flow

```bash
#!/bin/bash

# 1. Authenticate
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Check dashboard
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/dashboard | jq .

# 3. Process invoice
curl -s -X POST http://localhost:8000/api/process-invoice \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "INVOICE\nVendor: Acme Corporation\nAmount: $1,500.00\nDate: 2025-12-21\nDescription: Software license renewal"
  }' | jq .

# 4. View updated logs
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/dashboard/logs | jq '.[] | {vendor, amount, status}'
```

### Example 2: Health Check Monitoring

```bash
#!/bin/bash

# Check if system is ready
curl -s http://localhost:8000/health/ready | jq '.services'

# Expected output:
# {
#   "database": { "status": "healthy" },
#   "redis": { "status": "healthy" },
#   "blockchain": { "status": "healthy", "block_number": 12345 }
# }
```

### Example 3: Get Metrics and Performance

```bash
#!/bin/bash

TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | jq -r '.access_token')

# Get metrics
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/metrics | jq .

# Expected output:
# {
#   "invoices_processed": 42,
#   "transactions_approved": 38,
#   "transactions_rejected": 4,
#   "total_amount_processed": 45000.50,
#   "api_requests": 342,
#   "errors": 2
# }
```

---

## SDK Support

### Python

```python
import requests

token_response = requests.post(
    "http://localhost:8000/token",
    data={"username": "admin", "password": "admin123"}
)
token = token_response.json()["access_token"]

# Process invoice
invoice_response = requests.post(
    "http://localhost:8000/api/process-invoice",
    headers={"Authorization": f"Bearer {token}"},
    json={"raw_text": "Invoice text..."}
)
print(invoice_response.json())
```

### JavaScript/TypeScript

```javascript
const token = await fetch("http://localhost:8000/token", {
  method: "POST",
  headers: { "Content-Type": "application/x-www-form-urlencoded" },
  body: "username=admin&password=admin123"
}).then(r => r.json()).then(r => r.access_token);

const invoice = await fetch("http://localhost:8000/api/process-invoice", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({ raw_text: "Invoice text..." })
}).then(r => r.json());
```

### cURL

```bash
# See examples above
```

---

## Troubleshooting

### 401 Unauthorized

**Problem:** "Invalid token"
**Solution:** 

1. Get new token: `curl -X POST http://localhost:8000/token ...`
2. Include `Authorization: Bearer <token>` header
3. Check token hasn't expired

### 422 Validation Error

**Problem:** "Invoice text contains potentially malicious patterns"
**Solution:**

1. Check invoice text doesn't contain SQL/script patterns
2. Ensure raw_text is not empty
3. Keep under 100KB

### 429 Too Many Requests

**Problem:** "Rate limit exceeded"
**Solution:**

1. Wait 60 seconds before retrying
2. Implement exponential backoff in client
3. Check `Retry-After` header for wait time

### 503 Service Unavailable

**Problem:** "Database/Redis down"
**Solution:**

1. Check PostgreSQL is running: `docker-compose ps`
2. Check Redis is running: `redis-cli ping`
3. Restart services: `docker-compose restart`

---

## Support

For API issues or feature requests, contact the development team or create an issue on GitHub.

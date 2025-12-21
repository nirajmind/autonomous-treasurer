# ***Observability configuration and setup instructions***

## ✅PRIORITY #2: LOGGING & OBSERVABILITY - COMPLETE

### What was added:

1. ✅ logging_config.py - Structured JSON logging to files + console
2. ✅ observability.py - Health checks + metrics collection
3. ✅ middleware/observability.py - Request tracking middleware
4. ✅ New endpoints in app.py:
   - GET /health/ready - Kubernetes readiness probe
   - GET /health/live - Kubernetes liveness probe
   - GET /metrics - Application performance metrics
   - POST /metrics/reset - Reset metrics

### NEW ENDPOINTS YOU CAN USE IMMEDIATELY:

1. Health Check (for monitoring)

[GET](http://localhost:8000/health/ready)

```json
{
   "status": "healthy",
   "timestamp": "2025-12-21T...",
   "version": "1.0.0",
   "services": {
     "database": {"status": "healthy", "type": "PostgreSQL"},
     "redis": {"status": "healthy", "type": "Redis"},
     "blockchain": {"status": "healthy", "block_number": 12345}
   }
}
```

2. Liveness Probe (for Kubernetes)

[GET](http://localhost:8000/health/live)

```json
{
  "status": "alive",
  "timestamp": "2025-12-21T...",
  "version": "1.0.0"
}
```

3. Application Metrics

[GET](http://localhost:8000/metrics)

#### Requires: JWT Token (from /token endpoint)

```json
{
  "invoices_processed": 42,
  "transactions_approved": 38,
  "transactions_rejected": 4,
  "total_amount_processed": 15000.50,
  "api_requests": 342,
  "errors": 2,
  "start_time": "2025-12-21T..."
}
```

#### LOG FILES LOCATION

- All logs: /logs/treasurer.log (JSON format, rotating)
- Errors only: /logs/treasurer_errors.log (JSON format, rotating)
  
### Each log entry contains

- timestamp (ISO format)
- level (DEBUG, INFO, WARNING, ERROR)
- logger name
- message
- request_id (for tracing requests)
- status_code (for HTTP responses)
- duration_ms (for performance tracking)
- exception info (if error occurred)

### DOCKER SETUP:

Add this to your docker-compose.yml to mount logs:

```yaml
volumes:
  - ./backend/logs:/app/logs
```

#### This ensures logs persist between container restarts

### MONITORING INTEGRATION (Next Steps After Hackathon)

#### These endpoints can be integrated with:

✅ Prometheus - /metrics endpoint (no additional config needed)
✅ Datadog - POST your logs to Datadog's HTTP API
✅ Elastic Stack - Filebeat can tail logs/treasurer.log
✅ New Relic - Use APM agent
✅ CloudWatch - AWS agent can read logs/

print("""
✅ Priority #2 COMPLETE: Logging & Observability
New endpoints:

1. Health Check (for monitoring)

- /health/live - Kubernetes liveness  
  
1. Liveness Probe (for Kubernetes)

- /health/ready - Kubernetes readiness
  
1. Application Metrics - /health/ready - Kubernetes readiness

- Logs: ./logs/treasurer.log (JSON format)

""")

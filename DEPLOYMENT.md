# 🚀 Deployment Guide

Complete guide for deploying the Autonomous Treasurer to production.

---

## Quick Start (5 minutes)

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/yourusername/autonomous-treasurer.git
cd autonomous-treasurer

# 2. Create environment file
cp .env.example backend/.env
# Edit .env with your credentials

# 3. Start with Docker Compose
docker-compose up -d

# 4. Access
# Frontend: http://localhost:5173
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Deploy to Production (30 minutes)

```bash
# See "Production Deployment" section below
```

---

## Architecture

```arch
┌─────────────────┐
│   Frontend      │ (Vue.js + TailwindCSS)
│  (Port 5173)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  FastAPI        │─────→│  PostgreSQL  │
│  Backend        │      │  (Port 5432) │
│  (Port 8000)    │      └──────────────┘
└────────┬────────┘
         │
         ├─────────────→ ┌──────────────┐
         │              │  Redis       │
         │              │  (Port 6379) │
         │              └──────────────┘
         │
         └─────────────→ ┌──────────────┐
                        │  Soneium     │
                        │  Blockchain  │
                        └──────────────┘
```

---

## Prerequisites

- Docker & Docker Compose (v20+)
- Python 3.11+ (for local development)
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- OpenAI API key
- Soneium wallet with testnet funds

---

## Docker Deployment

### Development Environment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Check Service Health

```bash
# Health check
curl http://localhost:8000/health/ready

# Expected response
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "blockchain": {"status": "healthy"}
  }
}
```

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Follow logs
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

---

## Production Deployment

### Environment Setup

1. **Create Production .env**

```bash
# backend/.env.production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod_user:strong_password@prod-db.example.com:5432/treasurer_prod
REDIS_HOST=redis.prod.example.com
WALLET_PRIVATE_KEY=<use AWS Secrets Manager>
OPENAI_API_KEY=<use AWS Secrets Manager>
JWT_SECRET=<use AWS Secrets Manager>
ADMIN_PASSWORD=<use AWS Secrets Manager>
CORS_ORIGINS=["https://yourdomain.com"]
```

2. **Use Docker Secrets (Swarm) or ConfigMaps (Kubernetes)**

```yaml
# docker-compose.prod.yml
version: '3.9'
services:
  backend:
    env_file: .env.production
    environment:
      OPENAI_API_KEY_FILE: /run/secrets/openai_key
      JWT_SECRET_FILE: /run/secrets/jwt_secret
    secrets:
      - openai_key
      - jwt_secret
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

secrets:
  openai_key:
    external: true
  jwt_secret:
    external: true
```

### Database Migration

```bash
# 1. Backup existing database
pg_dump $DATABASE_URL > backup.sql

# 2. Apply migrations (when implemented)
cd backend
alembic upgrade head

# 3. Verify migration
psql $DATABASE_URL -c "SELECT version FROM alembic_version;"
```

### Deploy Using Docker Swarm

```bash
# 1. Initialize swarm
docker swarm init

# 2. Create secrets
echo "sk-proj-..." | docker secret create openai_key -
echo "your-jwt-secret" | docker secret create jwt_secret -

# 3. Deploy stack
docker stack deploy -c docker-compose.prod.yml treasurer

# 4. Monitor deployment
docker stack ps treasurer
docker service logs treasurer_backend

# 5. Scale service
docker service scale treasurer_backend=3

# 6. Update service
docker service update --image backend:v2.0 treasurer_backend

# 7. Rollback
docker service update --image backend:v1.0 treasurer_backend

# 8. Remove stack
docker stack rm treasurer
```

### Deploy Using Kubernetes

```bash
# 1. Create namespace
kubectl create namespace treasurer

# 2. Create secrets
kubectl create secret generic treasurer-secrets \
  --from-literal=openai-key=sk-proj-... \
  --from-literal=jwt-secret=... \
  -n treasurer

# 3. Create configmap
kubectl create configmap treasurer-config \
  --from-env-file=.env.production \
  -n treasurer

# 4. Deploy
kubectl apply -f k8s/deployment.yaml -n treasurer

# 5. Check deployment
kubectl get pods -n treasurer
kubectl logs -f deployment/treasurer-backend -n treasurer

# 6. Expose service
kubectl expose deployment treasurer-backend \
  --type=LoadBalancer \
  --port=8000 \
  -n treasurer

# 7. Monitor
kubectl top pods -n treasurer
kubectl describe pod treasurer-backend-xxx -n treasurer
```

**k8s/deployment.yaml example:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: treasurer-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: treasurer-backend
  template:
    metadata:
      labels:
        app: treasurer-backend
    spec:
      containers:
      - name: backend
        image: treasurer-backend:1.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: treasurer-config
              key: DATABASE_URL
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: treasurer-secrets
              key: openai-key
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

---

## Cloud Providers

### AWS Deployment

```bash
# 1. Push image to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $REGISTRY
docker tag treasurer-backend:1.0 $REGISTRY/treasurer-backend:1.0
docker push $REGISTRY/treasurer-backend:1.0

# 2. Deploy to ECS Fargate
aws ecs create-service \
  --cluster treasurer-prod \
  --service-name treasurer-backend \
  --task-definition treasurer-backend:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"

# 3. Setup RDS for PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier treasurer-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --allocated-storage 20

# 4. Setup ElastiCache for Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id treasurer-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1

# 5. Store secrets in Secrets Manager
aws secretsmanager create-secret \
  --name treasurer/prod \
  --secret-string file://secrets.json
```

### Heroku Deployment

```bash
# 1. Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# 2. Login
heroku login

# 3. Create app
heroku create treasurer-prod

# 4. Add PostgreSQL addon
heroku addons:create heroku-postgresql:standard-0

# 5. Set environment variables
heroku config:set OPENAI_API_KEY=sk-proj-...
heroku config:set JWT_SECRET=...
heroku config:set CORS_ORIGINS=https://yourdomain.com

# 6. Deploy
git push heroku main

# 7. View logs
heroku logs --tail

# 8. Monitor
heroku ps
heroku releases
```

### Google Cloud Run

```bash
# 1. Build image
docker build -t gcr.io/PROJECT_ID/treasurer-backend:1.0 .

# 2. Push to GCR
docker push gcr.io/PROJECT_ID/treasurer-backend:1.0

# 3. Deploy to Cloud Run
gcloud run deploy treasurer-backend \
  --image gcr.io/PROJECT_ID/treasurer-backend:1.0 \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DB_URL \
  --set-env-vars OPENAI_API_KEY=$OPENAI_KEY \
  --memory 512Mi \
  --cpu 1

# 4. Monitor
gcloud run services describe treasurer-backend
```

---

## Production Checklist

### Pre-Deployment

- [ ] All tests passing (`pytest`)
- [ ] No hardcoded secrets in code
- [ ] Environment variables configured
- [ ] Database backup created
- [ ] API keys rotated
- [ ] SSL/TLS certificate ready
- [ ] Domain DNS configured

### Deployment

- [ ] Use separate production database
- [ ] Use separate production Redis instance
- [ ] Run database migrations
- [ ] Enable database backups (daily)
- [ ] Enable database replication
- [ ] Set up monitoring (logs, metrics, errors)
- [ ] Set up alerting on failures
- [ ] Test health endpoints
- [ ] Verify JWT tokens work

### Post-Deployment

- [ ] Monitor error rate (target: <0.1%)
- [ ] Monitor response time (target: <500ms)
- [ ] Monitor database connections (max: 20)
- [ ] Monitor Redis memory usage (max: 256MB)
- [ ] Verify backups are working
- [ ] Test invoice processing end-to-end
- [ ] Test blockchain transactions
- [ ] Setup log aggregation (ELK, Datadog)
- [ ] Setup APM monitoring
- [ ] Setup alerting

---

## Scaling

### Horizontal Scaling

```bash
# Scale to 5 instances (Docker Swarm)
docker service scale treasurer_backend=5

# Scale to 5 pods (Kubernetes)
kubectl scale deployment treasurer-backend --replicas=5
```

### Load Balancing

```arch
                  ┌─ Backend Pod 1 (8000)
Load Balancer ────┼─ Backend Pod 2 (8000)
                  └─ Backend Pod 3 (8000)
                  
                  ┌─ PostgreSQL Primary (5432)
                  └─ PostgreSQL Replica (5432) [read-only]
                  
                  ┌─ Redis Primary (6379)
                  └─ Redis Replica (6379) [read-only]
```

### Database Replication

```bash
# PostgreSQL Primary-Replica setup
# Primary: prod-db.example.com:5432
# Replica: prod-db-replica.example.com:5432

# Configure replica
psql -h replica-host -c "STANDBY_MODE=on"
psql -h primary-host -c "SELECT pg_start_backup();"
pg_basebackup -h primary-host -D /pgdata -Fp -Pv
psql -h replica-host -c "SELECT pg_stop_backup();"
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

```bash
# Response time
curl -w "Response time: %{time_total}s\n" http://localhost:8000/health/live

# Error rate
curl http://localhost:8000/metrics | jq '.errors'

# Database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory
redis-cli info memory | grep used_memory_human

# Disk space
df -h
```

### Setup Monitoring with Prometheus + Grafana

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'treasurer-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Setup Alerting

```yaml
# alerts.yml
groups:
  - name: treasurer
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.001
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: HighResponseTime
        expr: response_time_p95 > 500
        for: 5m
        annotations:
          summary: "Slow response times"
```

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Verify ports are free
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Rebuild images
docker-compose down -v
docker-compose up --build
```

### Database connection error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql $DATABASE_URL -c "SELECT 1"

# Verify credentials in .env
cat backend/.env | grep DATABASE_URL
```

### Out of memory

```bash
# Check usage
docker stats

# Increase limits in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Slow queries

```bash
# Enable slow query log
ALTER SYSTEM SET log_min_duration_statement = 100;
SELECT pg_reload_conf();

# Analyze query
EXPLAIN ANALYZE SELECT ... FROM ...;

# Create index
CREATE INDEX idx_name ON table(column);
```

---

## Rollback Procedure

```bash
# Docker Swarm
docker service update --image treasurer-backend:v1.0 treasurer_backend

# Kubernetes
kubectl rollout history deployment treasurer-backend
kubectl rollout undo deployment treasurer-backend --to-revision=2

# Database
psql $DATABASE_URL < backup.sql
```

---

## Support

For deployment issues:

1. Check health endpoint: `http://localhost:8000/health/ready`
2. Review logs: `docker-compose logs -f`
3. Check documentation: `API.md`, `ENV_CONFIG.md`
4. File issue on GitHub with logs attached

---

**Next:** Review monitoring setup and configure alerts for your environment.

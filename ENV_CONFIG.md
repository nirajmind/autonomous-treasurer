# Environment Configuration Guide

## Overview

The Autonomous Treasurer uses environment variables for configuration. This ensures:

- ✅ Security (no hardcoded API keys)
- ✅ Flexibility (different configs per environment)
- ✅ Production-ready (secrets in vault, not git)

## Setup

### 1. Create `.env` File

Copy the template:

```bash
cp .env.example .env
```

### 2. Fill in Your Credentials

```bash
# OpenAI API
OPENAI_API_KEY=sk-proj-your-key-here

# JWT Authentication
JWT_SECRET=your-very-long-random-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/treasurer_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Soneium Blockchain
WALLET_PRIVATE_KEY=0x...your-private-key...
MNEE_TOKEN_ADDRESS=0x...MNEE-contract-address...
RPC_URL=https://rpc.minato.soneium.org/

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Admin
ADMIN_PASSWORD=strong-password-here
```

### 3. Secure Your .env File

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Restrict file permissions
chmod 600 .env
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for invoice parsing | `sk-proj-...` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `WALLET_PRIVATE_KEY` | Soneium wallet private key | `0x...` |
| `JWT_SECRET` | Secret for signing JWT tokens | Random 32+ char string |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `ADMIN_PASSWORD` | `admin123` | Default admin password (change in production!) |
| `CORS_ORIGINS` | `["*"]` | CORS allowed origins |
| `RPC_URL` | Mainnet URL | Blockchain RPC endpoint |
| `MNEE_TOKEN_ADDRESS` | Mainnet address | MNEE token contract address |

## Environment-Specific Configs

### Development

```bash
# .env (development)
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://user:password@localhost:5432/treasurer_dev
REDIS_HOST=localhost
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

### Testing

```bash
# .env.test (automatically loaded during pytest)
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./test.db
REDIS_HOST=localhost
```

### Production

```bash
# .env.production (in secured vault)
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod_user:secure_password@prod-host:5432/treasurer_prod
REDIS_HOST=redis.internal
ADMIN_PASSWORD=<use AWS Secrets Manager>
WALLET_PRIVATE_KEY=<use AWS Secrets Manager>
OPENAI_API_KEY=<use AWS Secrets Manager>
CORS_ORIGINS=["https://yourdomain.com"]
```

## Loading Environment Variables

### Python Application

```python
from dotenv import load_dotenv
import os

# Load from .env
load_dotenv()

# Access variables
api_key = os.getenv("OPENAI_API_KEY")
database_url = os.getenv("DATABASE_URL")
```

### Docker

```dockerfile
# In Dockerfile
COPY .env /app/.env
ENV $(cat .env | xargs)
```

### Docker Compose

```yaml
# In docker-compose.yml
services:
  backend:
    env_file: .env
    environment:
      DEBUG: "false"
```

## Secrets Management (Production)

For production, use a secrets manager instead of .env files:

### AWS Secrets Manager

```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='autonomous-treasurer')
credentials = json.loads(secret['SecretString'])
api_key = credentials['OPENAI_API_KEY']
```

### HashiCorp Vault

```python
import hvac

client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.read_secret_version(path='autonomous-treasurer')
api_key = secret['data']['data']['OPENAI_API_KEY']
```

### GitHub Secrets (for CI/CD)

```yaml
# In .github/workflows/ci.yml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Validation

The application validates required environment variables on startup:

```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env='OPENAI_API_KEY')
    database_url: str = Field(..., env='DATABASE_URL')
    jwt_secret: str = Field(..., env='JWT_SECRET')
    
    class Config:
        env_file = ".env"

# This will raise an error if required vars are missing
settings = Settings()
```

## Troubleshooting

### Environment variable not found

```bash
# Verify .env exists and is in the right location
ls -la .env

# Check if variable is set
echo $OPENAI_API_KEY

# Manually set it
export OPENAI_API_KEY="your-key-here"
```

### Wrong values being used

```bash
# Check which .env file is being loaded
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('DATABASE_URL'))"
```

### Database connection failing

```bash
# Verify connection string format
# postgres://user:password@host:port/database
# or
# postgresql://user:password@host:port/database
```

## Best Practices

✅ **DO:**

- Store sensitive values in secrets manager
- Use different credentials per environment
- Rotate API keys regularly
- Never commit `.env` to git
- Document all required variables
- Validate variables on startup
- Use strong, random secrets

❌ **DON'T:**

- Hardcode secrets in code
- Share API keys via email
- Use same credentials for all environments
- Commit `.env` to git
- Use weak default passwords
- Log secrets in debug output
- Reuse old API keys

## Next Steps

After setting up environment variables:

1. ✅ Run local development with `.env`
2. ✅ Run tests with `.env.test`
3. ✅ Deploy to staging with `.env.staging`
4. ✅ Deploy to production with secrets manager

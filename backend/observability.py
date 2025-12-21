"""Health checks and service status monitoring"""

import logging
from typing import Dict, Optional
from datetime import datetime
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("TreasurerAPI")

class HealthChecker:
    """Check health of all dependencies"""
    
    def __init__(self, db_session: Session, redis_client: redis.Redis):
        self.db_session = db_session
        self.redis_client = redis_client
    
    async def check_database(self) -> Dict[str, any]:
        """Check PostgreSQL connectivity"""
        try:
            result = self.db_session.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "PostgreSQL"
            }
        except Exception as e:
            logger.error(f"❌ Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "PostgreSQL",
                "error": str(e)
            }
    
    async def check_redis(self) -> Dict[str, any]:
        """Check Redis connectivity"""
        try:
            self.redis_client.ping()
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "Redis"
            }
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "Redis",
                "error": str(e)
            }
    
    async def check_blockchain(self, web3_provider) -> Dict[str, any]:
        """Check Web3/Blockchain RPC connectivity"""
        try:
            is_connected = web3_provider.is_connected()
            if is_connected:
                block_number = web3_provider.eth.block_number
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "Soneium Blockchain",
                    "block_number": block_number
                }
            else:
                return {
                    "status": "unhealthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "Soneium Blockchain",
                    "error": "Not connected"
                }
        except Exception as e:
            logger.error(f"❌ Blockchain health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "type": "Soneium Blockchain",
                "error": str(e)
            }
    
    async def check_all(self, web3_provider=None) -> Dict[str, any]:
        """Check all services"""
        logger.info("🔍 Running health checks...")
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {}
        }
        
        # Check database
        db_health = await self.check_database()
        health_status["services"]["database"] = db_health
        if db_health["status"] != "healthy":
            health_status["status"] = "degraded"
        
        # Check Redis
        redis_health = await self.check_redis()
        health_status["services"]["redis"] = redis_health
        if redis_health["status"] != "healthy":
            health_status["status"] = "degraded"
        
        # Check blockchain if provider available
        if web3_provider:
            blockchain_health = await self.check_blockchain(web3_provider)
            health_status["services"]["blockchain"] = blockchain_health
            if blockchain_health["status"] != "healthy":
                health_status["status"] = "degraded"
        
        logger.info(f"✅ Health check complete: {health_status['status']}")
        return health_status


class MetricsCollector:
    """Collect application metrics"""
    
    def __init__(self):
        self.metrics = {
            "invoices_processed": 0,
            "transactions_approved": 0,
            "transactions_rejected": 0,
            "total_amount_processed": 0.0,
            "api_requests": 0,
            "errors": 0,
            "start_time": datetime.utcnow().isoformat()
        }
    
    def record_invoice(self, amount: float, status: str):
        """Record invoice processing"""
        self.metrics["invoices_processed"] += 1
        if status == "approved":
            self.metrics["transactions_approved"] += 1
            self.metrics["total_amount_processed"] += amount
        elif status == "rejected":
            self.metrics["transactions_rejected"] += 1
    
    def record_request(self):
        """Record API request"""
        self.metrics["api_requests"] += 1
    
    def record_error(self):
        """Record error"""
        self.metrics["errors"] += 1
    
    def get_metrics(self) -> Dict:
        """Get current metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset metrics"""
        self.metrics = {
            "invoices_processed": 0,
            "transactions_approved": 0,
            "transactions_rejected": 0,
            "total_amount_processed": 0.0,
            "api_requests": 0,
            "errors": 0,
            "start_time": datetime.utcnow().isoformat()
        }

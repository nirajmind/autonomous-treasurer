"""Request tracking middleware for observability"""

import time
import logging
import uuid
from fastapi import Request

logger = logging.getLogger("TreasurerAPI")

async def request_tracking_middleware(request: Request, call_next):
    """
    Track request timing, add request ID, and log all requests.
    No code changes needed - just added to middleware stack.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    # Skip logging for health checks to avoid spam
    skip_logging = request.url.path in ["/health", "/health/live", "/health/ready"]
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        if not skip_logging:
            logger.info(
                f"{request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                    "method": request.method,
                    "path": request.url.path
                }
            )
        
        response.headers["X-Request-ID"] = request_id
        return response
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "duration_ms": round(duration * 1000, 2),
                "method": request.method,
                "path": request.url.path,
                "error": str(e)
            },
            exc_info=True
        )
        raise

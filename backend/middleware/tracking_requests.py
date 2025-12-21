"""Request tracking and logging middleware"""

import time
import logging
import uuid
from fastapi import Request

logger = logging.getLogger(__name__)

async def request_tracking_middleware(request: Request, call_next):
    """Track request timing and add request ID"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
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
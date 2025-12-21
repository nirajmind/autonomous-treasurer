"""Global error handling middleware"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import logging
import uuid
from datetime import datetime

from .treasuere_exception import TreasurerException

logger = logging.getLogger(__name__)

class ErrorResponse:
    def __init__(self, error_code: str, message: str, request_id: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.request_id = request_id
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "request_id": self.request_id,
                "timestamp": self.timestamp,
                "details": self.details
            }
        }


async def treasurer_exception_handler(request: Request, exc: TreasurerException):
    """Handle custom treasurer exceptions"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    logger.error(
        f"Treasurer error: {exc.error_code}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        request_id=request_id,
        details=exc.details
    )
    
    # Map error codes to HTTP status codes
    status_codes = {
        "INVOICE_PARSE_ERROR": 400,
        "POLICY_VIOLATION": 403,
        "APPROVAL_REQUIRED": 202,  # Accepted but pending
        "INSUFFICIENT_RUNWAY": 403,
        "BLOCKCHAIN_ERROR": 502,
        "DATABASE_ERROR": 503,
        "EXTERNAL_SERVICE_ERROR": 502,
    }
    
    status_code = status_codes.get(exc.error_code, 500)
    return JSONResponse(status_code=status_code, content=error_response.to_dict())


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    logger.error(
        f"Unhandled exception: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please contact support.",
        request_id=request_id
    )
    
    return JSONResponse(status_code=500, content=error_response.to_dict())


def setup_error_handlers(app: FastAPI):
    """Register error handlers with FastAPI"""
    app.add_exception_handler(TreasurerException, treasurer_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
"""Security headers to prevent common attacks"""

import logging
from fastapi import Request

logger = logging.getLogger("TreasurerAPI")

# Security headers that should be added to all responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",  # Prevent MIME type sniffing
    "X-Frame-Options": "DENY",  # Prevent clickjacking
    "X-XSS-Protection": "1; mode=block",  # XSS protection
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",  # HSTS
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",  # CSP
    "Referrer-Policy": "strict-origin-when-cross-origin",  # Referrer control
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",  # Disable unnecessary APIs
}


async def security_headers_middleware(request: Request, call_next):
    """
    Add security headers to all responses.
    Mitigates: MIME type sniffing, clickjacking, XSS, etc.
    """
    response = await call_next(request)
    
    # Add security headers
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    
    # Remove server header to avoid information disclosure
    if "Server" in response.headers:
        del response.headers["Server"]
    
    logger.debug(f"Security headers added to response for {request.url.path}")
    
    return response

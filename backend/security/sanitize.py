"""SQL injection prevention utilities"""

import logging
import re
from typing import Any

logger = logging.getLogger("TreasurerAPI")

class SQLInjectionPrevention:
    """Utilities to prevent SQL injection attacks"""
    
    # SQL keywords that shouldn't appear in safe user input
    DANGEROUS_SQL_PATTERNS = [
        r"(\bDROP\b|\bDELETE\b|\bTRUNCATE\b)",  # Destructive operations
        r"(\bUPDATE\b|\bINSERT\b|\bREPLACE\b)",  # Modification operations
        r"(--|;|/\*|\*/)",  # SQL comments and statement separators
        r"(\bunion\b|\bselect\b|\bfrom\b|\bwhere\b)",  # SELECT queries
        r"(\bexec\b|\bexecute\b|\bscript\b)",  # Execution commands
    ]
    
    @staticmethod
    def is_dangerous(user_input: str) -> bool:
        """
        Check if input contains SQL injection patterns.
        Returns True if input is suspicious.
        """
        if not isinstance(user_input, str):
            return False
        
        for pattern in SQLInjectionPrevention.DANGEROUS_SQL_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def sanitize_input(user_input: str, max_length: int = 255) -> str:
        """
        Sanitize user input.
        Note: Use parameterized queries instead of this function.
        """
        if not isinstance(user_input, str):
            return ""
        
        # Remove null bytes
        user_input = user_input.replace("\x00", "")
        
        # Limit length
        user_input = user_input[:max_length]
        
        # Remove control characters
        user_input = "".join(char for char in user_input if ord(char) >= 32 or char == "\n")
        
        return user_input.strip()


class XSSPrevention:
    """Utilities to prevent Cross-Site Scripting (XSS) attacks"""
    
    # Dangerous characters/patterns in user input
    XSS_PATTERNS = [
        r"<\s*script[^>]*>.*?</\s*script\s*>",  # Script tags
        r"on\w+\s*=",  # Event handlers (onclick, onload, etc.)
        r"<\s*iframe[^>]*>",  # Iframe tags
        r"javascript:",  # Javascript URLs
        r"<\s*embed[^>]*>",  # Embed tags
        r"<\s*object[^>]*>",  # Object tags
    ]
    
    @staticmethod
    def is_dangerous(user_input: str) -> bool:
        """Check if input contains XSS patterns"""
        if not isinstance(user_input, str):
            return False
        
        for pattern in XSSPrevention.XSS_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML special characters"""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        
        return text


class CSRFProtection:
    """CSRF token validation (tokens should be generated at login)"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate a random CSRF token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_csrf_token(provided_token: str, session_token: str) -> bool:
        """
        Validate CSRF token using constant-time comparison
        to prevent timing attacks
        """
        import hmac
        return hmac.compare_digest(provided_token, session_token)


class InputSanitizer:
    """Unified input sanitization"""
    
    @staticmethod
    def sanitize_string(
        user_input: str,
        max_length: int = 255,
        allow_html: bool = False
    ) -> str:
        """
        Sanitize string input.
        
        Args:
            user_input: The string to sanitize
            max_length: Maximum allowed length
            allow_html: If False, escape HTML characters
        """
        if not isinstance(user_input, str):
            return ""
        
        # Check for SQL injection
        if SQLInjectionPrevention.is_dangerous(user_input):
            raise ValueError("Input contains potentially dangerous SQL patterns")
        
        # Check for XSS
        if XSSPrevention.is_dangerous(user_input):
            raise ValueError("Input contains potentially dangerous script patterns")
        
        # Sanitize
        user_input = user_input[:max_length]
        user_input = user_input.strip()
        
        if not allow_html:
            user_input = XSSPrevention.escape_html(user_input)
        
        return user_input
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and validate email address"""
        import re
        
        email = email.strip().lower()
        
        # Basic email validation regex
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:  # RFC 5321
            raise ValueError("Email too long")
        
        return email

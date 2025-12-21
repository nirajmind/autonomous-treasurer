"""Input validation schemas using Pydantic"""

from pydantic import BaseModel, Field, field_validator, ConfigDict, constr
from typing import Optional
import re

# =============================================================================
# INVOICE VALIDATION
# =============================================================================

class InvoiceValidation:
    """Validators for invoice inputs"""
    
    @staticmethod
    def validate_invoice_text(text: str) -> bool:
        """Prevent malicious invoice text"""
        if not text or len(text.strip()) == 0:
            raise ValueError("Invoice text cannot be empty")
        
        if len(text) > 100000:  # 100KB max
            raise ValueError("Invoice text exceeds maximum size (100KB)")
        
        # Check for SQL injection patterns (specific enough to avoid false positives)
        # Focus on actual SQL syntax combinations, not just keywords
        dangerous_patterns = [
            r"DROP\s+(TABLE|DATABASE|VIEW|INDEX)",
            r"DELETE\s+FROM",
            r"UPDATE\s+\w+\s+SET",
            r"INSERT\s+INTO",
            r"EXEC(UTE)?\s*\(",
            r"(--|#|/\*)",  # SQL comments (exclude */ to avoid false positives on URLs)
            r"UNION\s+(ALL\s+)?SELECT",
            r";\s*(DROP|DELETE|UPDATE|INSERT)",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise ValueError("Invoice text contains potentially malicious patterns")
        
        return True
    
    @staticmethod
    def validate_vendor_name(name: str) -> bool:
        """Validate vendor name"""
        if not name or len(name.strip()) == 0:
            raise ValueError("Vendor name cannot be empty")
        
        if len(name) > 255:
            raise ValueError("Vendor name too long (max 255 chars)")
        
        # Allow alphanumeric, spaces, hyphens, dots, & symbols
        if not re.match(r"^[a-zA-Z0-9\s\-\.&'(),]+$", name):
            raise ValueError("Vendor name contains invalid characters")
        
        return True
    
    @staticmethod
    def validate_amount(amount: float) -> bool:
        """Validate invoice amount"""
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        
        if amount > 999999999.99:  # Prevent overflow
            raise ValueError("Amount exceeds maximum (999,999,999.99)")
        
        # Check precision (max 2 decimal places for currency)
        if len(str(amount).split('.')[-1]) > 2:
            raise ValueError("Amount must have max 2 decimal places")
        
        return True
    
    @staticmethod
    def validate_currency(currency: str) -> bool:
        """Validate currency code"""
        if not currency or len(currency.strip()) == 0:
            raise ValueError("Currency cannot be empty")
        
        # ISO 4217 currency codes are 3 uppercase letters
        if not re.match(r"^[A-Z]{3}$", currency):
            raise ValueError("Invalid currency code (must be 3 uppercase letters)")
        
        return True


# =============================================================================
# REQUEST VALIDATION MODELS
# =============================================================================

class InvoiceRequestModel(BaseModel):
    """Validated invoice request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "raw_text": "Invoice #INV-001\nVendor: Acme Corp\nAmount: $1,500.00\nDate: 2025-12-21"
            }
        }
    )
    
    raw_text: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Raw invoice text (max 100KB)"
    )
    
    @field_validator('raw_text')
    @classmethod
    def validate_text(cls, v):
        InvoiceValidation.validate_invoice_text(v)
        return v


class TransactionRequestModel(BaseModel):
    """Validated transaction request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vendor_name": "Acme Corp",
                "amount": 1500.00,
                "currency": "USD",
                "category": "Software"
            }
        }
    )
    
    vendor_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Vendor name"
    )
    amount: float = Field(..., gt=0, le=999999999.99, description="Transaction amount")
    currency: str = Field(
        ..., 
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
        description="ISO 4217 currency code"
    )
    category: Optional[str] = Field(None, max_length=100, description="Expense category")
    
    @field_validator('vendor_name')
    @classmethod
    def validate_vendor(cls, v):
        InvoiceValidation.validate_vendor_name(v)
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amt(cls, v):
        InvoiceValidation.validate_amount(v)
        return v
    
    @field_validator('currency')
    @classmethod
    def validate_curr(cls, v):
        InvoiceValidation.validate_currency(v)
        return v


class LoginRequestModel(BaseModel):
    """Validated login request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "password": "secure_password_123"
            }
        }
    )
    
    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        description="Username (alphanumeric, dash, underscore, dot)"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Password (min 8 chars)"
    )


class LimitUpdateRequestModel(BaseModel):
    """Validated spending limit update"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_limit": 5000.00
            }
        }
    )
    
    new_limit: float = Field(..., gt=0, le=999999999.99, description="New spending limit")
    
    @field_validator('new_limit')
    @classmethod
    def validate_limit(cls, v):
        InvoiceValidation.validate_amount(v)
        return v


# =============================================================================
# RESPONSE VALIDATION MODELS
# =============================================================================

class ErrorResponseModel(BaseModel):
    """Standard error response"""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    request_id: str = Field(..., description="Request tracking ID")
    details: Optional[dict] = Field(None, description="Additional error details")


class SuccessResponseModel(BaseModel):
    """Standard success response"""
    status: str = Field(..., description="Operation status")
    data: Optional[dict] = Field(None, description="Response data")
    timestamp: str = Field(..., description="Response timestamp")

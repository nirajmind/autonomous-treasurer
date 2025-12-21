"""Custom exceptions for Autonomous Treasurer"""

class TreasurerException(Exception):
    """Base exception for all treasurer errors"""
    def __init__(self, message: str, error_code: str, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

# Invoice Processing Errors
class InvoiceParsingError(TreasurerException):
    """Raised when invoice parsing fails"""
    pass

class InvalidInvoiceFormat(TreasurerException):
    """Raised when invoice format is invalid"""
    pass

# Policy & Approval Errors
class PolicyViolationError(TreasurerException):
    """Raised when transaction violates policy"""
    pass

class ApprovalRequiredError(TreasurerException):
    """Raised when transaction requires manual approval"""
    pass

class InsufficientRunwayError(TreasurerException):
    """Raised when payment would drop runway below critical threshold"""
    pass

# Blockchain Errors
class BlockchainError(TreasurerException):
    """Base blockchain error"""
    pass

class TransactionFailedError(BlockchainError):
    """Raised when blockchain transaction fails"""
    pass

class GasEstimationError(BlockchainError):
    """Raised when gas estimation fails"""
    pass

class NonceCollisionError(BlockchainError):
    """Raised when nonce conflict occurs"""
    pass

class ReorgDetectedError(BlockchainError):
    """Raised when blockchain reorg is detected"""
    pass

# Database Errors
class DatabaseError(TreasurerException):
    """Base database error"""
    pass

class TransactionAbortedError(DatabaseError):
    """Raised when database transaction is aborted"""
    pass

# External Service Errors
class ExternalServiceError(TreasurerException):
    """Raised when external service (OpenAI, RPC) fails"""
    pass

class RPCTimeoutError(ExternalServiceError):
    """Raised when RPC call times out"""
    pass
"""Unit tests for security and validation"""

import pytest
from security.validation import (
    InvoiceValidation,
    InvoiceRequestModel,
    TransactionRequestModel,
)
from security.sanitize import SQLInjectionPrevention, XSSPrevention, InputSanitizer


class TestInvoiceValidation:
    """Test invoice input validation"""
    
    def test_valid_invoice_text(self):
        """Valid invoice should pass validation"""
        valid_text = "Invoice #INV-001\nVendor: Acme Corp\nAmount: $1,500.00"
        assert InvoiceValidation.validate_invoice_text(valid_text)
    
    def test_empty_invoice_text(self):
        """Empty invoice should fail"""
        with pytest.raises(ValueError, match="empty"):
            InvoiceValidation.validate_invoice_text("")
    
    def test_sql_injection_detection(self):
        """SQL injection patterns should be blocked"""
        malicious = "'; DROP TABLE users; --"
        with pytest.raises(ValueError, match="malicious"):
            InvoiceValidation.validate_invoice_text(malicious)
    
    def test_invoice_size_limit(self):
        """Invoice exceeding size limit should fail"""
        huge_text = "x" * 101000  # 101KB
        with pytest.raises(ValueError, match="exceeds maximum"):
            InvoiceValidation.validate_invoice_text(huge_text)
    
    def test_valid_vendor_name(self):
        """Valid vendor name should pass"""
        assert InvoiceValidation.validate_vendor_name("Acme Corp")
        assert InvoiceValidation.validate_vendor_name("Apple Inc.")
        assert InvoiceValidation.validate_vendor_name("ABC-123 & Co.")
    
    def test_invalid_vendor_name(self):
        """Invalid vendor name should fail"""
        with pytest.raises(ValueError):
            InvoiceValidation.validate_vendor_name("")
        
        with pytest.raises(ValueError):
            InvoiceValidation.validate_vendor_name("x" * 256)  # Too long
        
        with pytest.raises(ValueError):
            InvoiceValidation.validate_vendor_name("Acme@#$%")  # Invalid chars
    
    def test_valid_amount(self):
        """Valid amounts should pass"""
        assert InvoiceValidation.validate_amount(100.00)
        assert InvoiceValidation.validate_amount(0.01)
        assert InvoiceValidation.validate_amount(999999999.99)
    
    def test_invalid_amount(self):
        """Invalid amounts should fail"""
        with pytest.raises(ValueError):
            InvoiceValidation.validate_amount(0)  # Zero
        
        with pytest.raises(ValueError):
            InvoiceValidation.validate_amount(-100)  # Negative
        
        with pytest.raises(ValueError):
            InvoiceValidation.validate_amount(1000000000)  # Too large
    
    def test_valid_currency(self):
        """Valid currency codes should pass"""
        assert InvoiceValidation.validate_currency("USD")
        assert InvoiceValidation.validate_currency("EUR")
        assert InvoiceValidation.validate_currency("GBP")
    
    def test_invalid_currency(self):
        """Invalid currency codes should fail"""
        with pytest.raises(ValueError):
            InvoiceValidation.validate_currency("US")  # Too short
        
        with pytest.raises(ValueError):
            InvoiceValidation.validate_currency("USDA")  # Too long
        
        with pytest.raises(ValueError):
            InvoiceValidation.validate_currency("usd")  # Lowercase


class TestSQLInjectionPrevention:
    """Test SQL injection detection"""
    
    def test_drop_detection(self):
        """DROP statements should be detected"""
        assert SQLInjectionPrevention.is_dangerous("DROP TABLE users")
        assert SQLInjectionPrevention.is_dangerous("drop table transactions")
    
    def test_delete_detection(self):
        """DELETE statements should be detected"""
        assert SQLInjectionPrevention.is_dangerous("DELETE FROM users WHERE id=1")
    
    def test_union_detection(self):
        """UNION queries should be detected"""
        assert SQLInjectionPrevention.is_dangerous("SELECT * FROM users UNION SELECT")
    
    def test_comment_detection(self):
        """SQL comments should be detected"""
        assert SQLInjectionPrevention.is_dangerous("SELECT * FROM users -- comment")
        assert SQLInjectionPrevention.is_dangerous("SELECT /* comment */ * FROM users")
    
    def test_safe_input(self):
        """Safe input should not be flagged"""
        assert not SQLInjectionPrevention.is_dangerous("Acme Corp invoice #12345")
        assert not SQLInjectionPrevention.is_dangerous("Amount: $1,500.00")


class TestXSSPrevention:
    """Test XSS detection"""
    
    def test_script_tag_detection(self):
        """Script tags should be detected"""
        assert XSSPrevention.is_dangerous("<script>alert('xss')</script>")
        assert XSSPrevention.is_dangerous("<SCRIPT>bad()</SCRIPT>")
    
    def test_event_handler_detection(self):
        """Event handlers should be detected"""
        assert XSSPrevention.is_dangerous('onclick="alert(\'xss\')"')
        assert XSSPrevention.is_dangerous("onload=malicious()")
    
    def test_iframe_detection(self):
        """IFrame tags should be detected"""
        assert XSSPrevention.is_dangerous('<iframe src="evil.com"></iframe>')
    
    def test_javascript_url_detection(self):
        """JavaScript URLs should be detected"""
        assert XSSPrevention.is_dangerous('href="javascript:alert(\'xss\')"')
    
    def test_safe_input(self):
        """Safe input should not be flagged"""
        assert not XSSPrevention.is_dangerous("Click here for more info")
        assert not XSSPrevention.is_dangerous("Invoice from Acme Corp")
    
    def test_html_escaping(self):
        """HTML should be properly escaped"""
        escaped = XSSPrevention.escape_html('<script>alert("test")</script>')
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "&quot;" in escaped


class TestInputSanitizer:
    """Test input sanitization"""
    
    def test_sanitize_string(self):
        """Strings should be sanitized"""
        result = InputSanitizer.sanitize_string("  hello world  ")
        assert result == "hello world"
        assert result == result.strip()
    
    def test_sanitize_string_max_length(self):
        """String should be truncated to max length"""
        long_string = "x" * 300
        result = InputSanitizer.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_rejects_sql_injection(self):
        """SQL injection should be rejected"""
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_string("'; DROP TABLE users; --")
    
    def test_sanitize_string_rejects_xss(self):
        """XSS should be rejected"""
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_string("<script>alert('xss')</script>")
    
    def test_sanitize_email_valid(self):
        """Valid emails should pass"""
        assert InputSanitizer.sanitize_email("user@example.com")
        assert InputSanitizer.sanitize_email("test.user+tag@sub.domain.co.uk")
    
    def test_sanitize_email_invalid(self):
        """Invalid emails should fail"""
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_email("invalid.email")
        
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_email("@example.com")


class TestPydanticValidation:
    """Test Pydantic model validation"""
    
    def test_valid_invoice_request(self):
        """Valid invoice request should pass"""
        invoice = InvoiceRequestModel(
            raw_text="Invoice #INV-001\nVendor: Acme\nAmount: $100"
        )
        assert invoice.raw_text
    
    def test_invalid_invoice_request_empty(self):
        """Empty invoice request should fail"""
        with pytest.raises(ValueError):
            InvoiceRequestModel(raw_text="")
    
    def test_invalid_invoice_request_sql_injection(self):
        """SQL injection in invoice request should fail"""
        with pytest.raises(ValueError):
            InvoiceRequestModel(raw_text="'; DROP TABLE users; --")
    
    def test_valid_transaction_request(self):
        """Valid transaction request should pass"""
        transaction = TransactionRequestModel(
            vendor_name="Acme Corp",
            amount=1500.00,
            currency="USD",
            category="Software"
        )
        assert transaction.vendor_name == "Acme Corp"
        assert transaction.amount == 1500.00
    
    def test_invalid_transaction_request_amount(self):
        """Invalid amount should fail"""
        with pytest.raises(ValueError):
            TransactionRequestModel(
                vendor_name="Acme Corp",
                amount=-100,  # Negative amount
                currency="USD"
            )
    
    def test_invalid_transaction_request_currency(self):
        """Invalid currency should fail"""
        with pytest.raises(ValueError):
            TransactionRequestModel(
                vendor_name="Acme Corp",
                amount=100.00,
                currency="USDA"  # Invalid code
            )

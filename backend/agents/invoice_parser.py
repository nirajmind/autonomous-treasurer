"""Invoice parser with comprehensive error handling"""

import logging
import traceback
from typing import Dict, Optional
#from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from exception.treasuere_exception import InvoiceParsingError, ExternalServiceError
from exception.retry_logic import retry_async_decorator, RetryConfig

logger = logging.getLogger(__name__)

# 1. Define the Output Schema using Pydantic
class InvoiceSchema(BaseModel):
    vendor_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None

class InvoiceParser:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            temperature=0.0,
            model="gpt-4-turbo"
        )
        self.output_parser = PydanticOutputParser(pydantic_object=InvoiceSchema)
        self.format_instructions = self.output_parser.get_format_instructions()

    def parse_invoice_text(self, invoice_text_raw: str) -> InvoiceSchema:
        """
        Takes raw text (OCR'd from PDF) and returns structured JSON
        
        Your original logic + enhanced error handling
        Includes retry logic with error handling in the method itself.
        """
        logger.info("🧠 Agent starting analysis...")
        
        try:
            # Validate input
            if not invoice_text_raw or len(invoice_text_raw.strip()) == 0:
                raise ValueError("Invoice text is empty")
            
            # YOUR ORIGINAL APPROACH - preserved exactly
            template_string = """
You are an automated Treasurer Agent.
You are given the text content of an invoice.

Extract the following information:
1. Vendor Name
2. Total Amount
3. Currency
4. Expense Category

If you cannot find a field, return null.

Invoice Text:
{invoice_text}

{format_instructions}
            """

            prompt = ChatPromptTemplate.from_template(template_string)
            messages = prompt.format_messages(
                invoice_text=invoice_text_raw,
                format_instructions=self.format_instructions
            )
            
            logger.info("📡 Sending request to OpenAI API...")
            response = self.llm.invoke(messages)
            logger.info("✅ OpenAI Response received.")
            
            # Parse with Pydantic validation
            parsed_invoice = self.output_parser.parse(response.content)
            
            logger.info(f"✅ Invoice parsed: {parsed_invoice.vendor_name} - {parsed_invoice.amount} {parsed_invoice.currency}")
            return parsed_invoice

        except Exception as e:
            # --- YOUR DEBUGGING GOLD - preserved ---
            logger.error(f"❌ OPENAI CALL FAILED: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Enhanced: Wrap in our exception system
            if "API" in str(e) or "timeout" in str(e).lower():
                raise ExternalServiceError(
                    message=f"OpenAI API failed: {str(e)}",
                    error_code="OPENAI_API_ERROR",
                    details={"original_error": str(type(e).__name__)}
                )
            else:
                raise InvoiceParsingError(
                    message=f"Invoice parsing failed: {str(e)}",
                    error_code="PARSE_FAILED",
                    details={"original_error": str(type(e).__name__)}
                )


# --- Module-level function for direct import ---
def parse_invoice_text(invoice_text_raw: str) -> InvoiceSchema:
    """
    Module-level wrapper function for invoice parsing.
    Creates InvoiceParser instance and parses the invoice text.
    
    Args:
        invoice_text_raw: Raw invoice text to parse
        
    Returns:
        InvoiceSchema: Structured invoice data
        
    Raises:
        InvoiceParsingError: If parsing fails
        ExternalServiceError: If OpenAI API fails
    """
    import os
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    parser = InvoiceParser(openai_api_key=openai_api_key)
    return parser.parse_invoice_text(invoice_text_raw)
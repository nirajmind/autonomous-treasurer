from typing import Optional
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import logging
import traceback

# Set up a specific logger for this file
logger = logging.getLogger("InvoiceParser")

# 1. Define the Output Schema using Pydantic
class InvoiceSchema(BaseModel):
    vendor_name: Optional[str]
    amount: Optional[float]
    currency: Optional[str]
    category: Optional[str]

# Create parser
output_parser = PydanticOutputParser(pydantic_object=InvoiceSchema)
format_instructions = output_parser.get_format_instructions()
# 2. The Logic
def parse_invoice_text(invoice_text_raw: str):
    """
    Takes raw text (OCR'd from PDF) and returns structured JSON
    """
    logger.info("🧠 Agent starting analysis...")
    try:
        llm = ChatOpenAI(temperature=0.0, model="gpt-4-turbo")
        
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
            format_instructions=format_instructions
        )
        
        logger.info("📡 Sending request to OpenAI API...")
        response = llm.invoke(messages)
        logger.info("✅ OpenAI Response received.")
        
        return output_parser.parse(response.content)

    except Exception as e:
        # --- THIS IS THE DEBUGGING GOLD ---
        logger.error(f"❌ OPENAI CALL FAILED: {str(e)}")
        logger.error(traceback.format_exc()) # Prints the full stack trace
        raise e

# --- QUICK TEST ---
if __name__ == "__main__":
    mock_invoice = """
    INVOICE #001
    From: Amazon Web Services (AWS)
    Date: Dec 17, 2025

    Description:
    Elastic Compute Cloud ..... $42.50
    Data Transfer ............. $2.50

    TOTAL DUE: $45.00 USD
    """

    print("Agent is reading invoice...")
    try:
        result = parse_invoice_text(mock_invoice)
        print("--- EXTRACTED DATA ---")
        print(result.dict())  # Pydantic object → dict

        if result.amount and result.amount < 50.0:
            print("DECISION: Amount is under $50. Auto-Pay Approved.")
        else:
            print("DECISION: Requires Human Approval.")
    except Exception as e:
        print(f"Error during test: {e}")
        print("Note: If this failed with an API Key error, it's expected until you set your .env key.")
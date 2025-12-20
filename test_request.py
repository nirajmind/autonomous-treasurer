import requests
import json

# 1. The Endpoint (Your FastAPI running locally)
url = "http://127.0.0.1:8000/api/process-invoice"

# 2. The Invoice Payload (The "Digital Invoice")
payload = {
    "raw_text": "Invoice INV-TEST-001 from CloudServices for 50 MNEE due on 2025-12-30",
    "invoice_id": "INV-TEST-001",
    "vendor_name": "CloudServices Inc",
    "vendor_wallet": "0x1234567890abcdef1234567890abcdef12345678", 
    "amount": 50.00,
    "currency": "MNEE",
    "due_date": "2025-12-30"
}

# 3. Send the Request
print(f"🚀 Sending Invoice for {payload['amount']} MNEE...")

try:
    response = requests.post(url, json=payload)
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"📄 Response: {response.json()}")

except Exception as e:
    print(f"❌ Error: {e}")
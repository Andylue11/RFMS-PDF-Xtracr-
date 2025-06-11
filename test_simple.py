print("Simple test working")
import requests
print("Requests imported")

from dotenv import load_dotenv
import os

load_dotenv('.env-test')
BASE_URL = os.getenv('RFMS_BASE_URL')
print(f"BASE_URL: {BASE_URL}")

# Test the flat structure with minimal payload
payload = {
    "category": "Order",
    "poNumber": "TEST-SIMPLE-123",
    "UserOrderType": 18,
    "ServiceType": 8,
    "ContractType": 1
}

print("Payload created:", payload)
print("Test complete") 
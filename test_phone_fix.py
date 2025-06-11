import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env-test')

# RFMS API Configuration
BASE_URL = os.getenv('RFMS_BASE_URL')
STORE_CODE = os.getenv('RFMS_STORE_CODE')
API_KEY = os.getenv('RFMS_API_KEY')

def test_phone_fix():
    """Test phone field variations to fix missing phone issue."""
    print("📞 TESTING PHONE FIELD FIX")
    print("=" * 50)
    print("Based on AZ002871 success + phone field variations")
    
    # Get session token
    response = requests.post(
        f"{BASE_URL}/v2/session/begin",
        auth=(STORE_CODE, API_KEY),
        headers={'Content-Type': 'application/json'}
    )
    
    session_token = response.json().get('sessionToken')
    
    supervisor_name = "Jackson Peters"
    supervisor_phone = "0447012125"
    
    po_number = f"PHONE-FIX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Testing multiple phone field formats")
    
    # AZ002871 payload + phone field variations
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        "soldTo": {
            "customerId": 5,
            "firstName": "Jackson",
            "lastName": "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone": supervisor_phone,     # Original format
            "phone1": supervisor_phone,    # Alternative format 1
            "phone2": supervisor_phone,    # Alternative format 2
            "email": "jackson.peters@example.com"
        },
        "shipTo": {
            "firstName": "Site",
            "lastName": "Customer",
            "address1": "1505 ROSEBANK WAY WEST",
            "city": "HOPE ISLAND",
            "state": "QLD",
            "postalCode": "4212",
            "phone": supervisor_phone,     # Add phone to shipTo too
            "phone1": supervisor_phone     # Alternative in shipTo
        },
        "privateNotes": f"PHONE FIX TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"Testing phone1, phone2 fields: {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,
        "serviceTypeId": 8,
        "contractTypeId": 1,
        "adSource": 1
    }
    
    response = requests.post(
        f"{BASE_URL}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers={'Content-Type': 'application/json'},
        json=payload
    )
    
    print(f"📥 Status: {response.status_code}")
    print(f"📥 Response: {response.text}")
    
    result = response.json()
    if result.get('status') == 'success':
        order_id = result.get('result')
        print(f"✅ PHONE FIX Order: {order_id}")
        print(f"📞 Testing phone, phone1, phone2 fields")
        print(f"🔍 Check if phone now appears in RFMS!")
        return True
    else:
        print(f"❌ Failed: {result.get('result')}")
        return False

if __name__ == "__main__":
    test_phone_fix() 
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

def test_phone_soldto_only():
    """Test Phone1 and Phone2 fields only under soldTo customer section."""
    print("📞 TESTING PHONE1 & PHONE2 - SOLDTO ONLY")
    print("=" * 60)
    print("Phone1/Phone2 only under soldTo customer section")
    
    # Get session token
    response = requests.post(
        f"{BASE_URL}/v2/session/begin",
        auth=(STORE_CODE, API_KEY),
        headers={'Content-Type': 'application/json'}
    )
    
    session_token = response.json().get('sessionToken')
    
    supervisor_name = "Jackson Peters"
    supervisor_phone1 = "0447012125"    # Primary phone (mobile)
    supervisor_phone2 = "0732341234"    # Secondary phone (office)
    
    po_number = f"SOLDTO-PHONE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"📞 SoldTo Phone1 (Mobile): {supervisor_phone1}")
    print(f"📞 SoldTo Phone2 (Office): {supervisor_phone2}")
    print(f"🎯 Phone fields ONLY in soldTo customer section")
    
    # AZ002871 payload + Phone1/Phone2 ONLY in soldTo
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone1}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        "soldTo": {
            "customerId": 5,  # PROFILE BUILD GROUP
            "firstName": "Jackson",
            "lastName": "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone1": supervisor_phone1,    # Mobile phone - ONLY HERE
            "phone2": supervisor_phone2,    # Office phone - ONLY HERE
            "email": "jackson.peters@example.com"
        },
        "shipTo": {
            "firstName": "Site",
            "lastName": "Customer",
            "address1": "1505 ROSEBANK WAY WEST",
            "city": "HOPE ISLAND",
            "state": "QLD",
            "postalCode": "4212"
            # NO phone fields in shipTo
        },
        # All the successful fields from AZ002871
        "privateNotes": f"SOLDTO PHONE TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"Customer Phones: Mobile {supervisor_phone1}, Office {supervisor_phone2}",
        "workOrderNotes": f"Customer Contact - Mobile: {supervisor_phone1} | Office: {supervisor_phone2}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "adSource": 1
    }
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Phone1/Phone2 ONLY in soldTo customer")
    
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
        print(f"✅ SUCCESS! SoldTo Phone Order: {order_id}")
        print(f"📞 Customer Phone1: {supervisor_phone1} (Mobile)")
        print(f"📞 Customer Phone2: {supervisor_phone2} (Office)")
        print(f"🔍 Check RFMS for customer phone fields!")
        
        # Show the exact payload structure
        print(f"\n📋 EXACT PAYLOAD STRUCTURE:")
        print(f"✅ soldTo.phone1: {supervisor_phone1}")
        print(f"✅ soldTo.phone2: {supervisor_phone2}")
        print(f"❌ shipTo: NO phone fields")
        
        return True
    else:
        print(f"❌ Failed: {result.get('result')}")
        return False

if __name__ == "__main__":
    print("📞 SOLDTO PHONE ONLY TEST")
    print("Phone1 and Phone2 only under soldTo customer")
    print("=" * 70)
    
    success = test_phone_soldto_only()
    
    print(f"\n" + "=" * 70)
    print("🎯 SOLDTO PHONE RESULT:")
    if success:
        print("✅ SUCCESS! Phone1/Phone2 under soldTo only!")
        print("📞 Customer Mobile: 0447012125")
        print("📞 Customer Office: 0732341234")
        print("🔍 Check RFMS interface - customer section should show both phones")
    else:
        print("❌ SoldTo phone test failed") 
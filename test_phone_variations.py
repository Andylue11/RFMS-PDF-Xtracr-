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

def test_phone_variations():
    """Test Phone1 and Phone2 fields with different phone numbers."""
    print("📞 TESTING PHONE1 & PHONE2 WITH DIFFERENT NUMBERS")
    print("=" * 60)
    print("Based on AZ002871 success + Phone1/Phone2 variations")
    
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
    
    po_number = f"PHONE-VAR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"📞 Phone1 (Mobile): {supervisor_phone1}")
    print(f"📞 Phone2 (Office): {supervisor_phone2}")
    print(f"🎯 Testing Phone1/Phone2 with different numbers")
    
    # AZ002871 payload + Phone1/Phone2 with different numbers
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
            "phone1": supervisor_phone1,    # Mobile phone
            "phone2": supervisor_phone2,    # Office phone  
            "email": "jackson.peters@example.com"
        },
        "shipTo": {
            "firstName": "Site",
            "lastName": "Customer",
            "address1": "1505 ROSEBANK WAY WEST",
            "city": "HOPE ISLAND",
            "state": "QLD",
            "postalCode": "4212",
            "phone1": supervisor_phone1,    # Site contact mobile
            "phone2": supervisor_phone2     # Site contact office
        },
        # All the successful fields from AZ002871
        "privateNotes": f"PHONE VAR TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"Phone Variations: Mobile {supervisor_phone1}, Office {supervisor_phone2}",
        "workOrderNotes": f"Primary: {supervisor_phone1} | Secondary: {supervisor_phone2}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "adSource": 1
    }
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: AZ002871 + Phone1/Phone2 with different numbers")
    
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
        print(f"✅ SUCCESS! Phone Variations Order: {order_id}")
        print(f"📞 Phone1: {supervisor_phone1} (Mobile)")
        print(f"📞 Phone2: {supervisor_phone2} (Office)")
        print(f"🔍 Check RFMS for both phone numbers!")
        
        # Show the exact payload used
        print(f"\n📋 EXACT PAYLOAD USED:")
        print(f"📞 soldTo.phone1: {supervisor_phone1}")
        print(f"📞 soldTo.phone2: {supervisor_phone2}")
        print(f"📞 shipTo.phone1: {supervisor_phone1}")
        print(f"📞 shipTo.phone2: {supervisor_phone2}")
        
        return True
    else:
        print(f"❌ Failed: {result.get('result')}")
        return False

if __name__ == "__main__":
    print("📞 PHONE VARIATIONS TEST")
    print("Testing Phone1 and Phone2 with different numbers")
    print("=" * 70)
    
    success = test_phone_variations()
    
    print(f"\n" + "=" * 70)
    print("🎯 PHONE VARIATIONS RESULT:")
    if success:
        print("✅ SUCCESS! Phone1/Phone2 order created!")
        print("📞 Mobile: 0447012125")
        print("📞 Office: 0732341234")
        print("🔍 Check RFMS interface to verify both phone numbers appear")
    else:
        print("❌ Phone variations test failed") 
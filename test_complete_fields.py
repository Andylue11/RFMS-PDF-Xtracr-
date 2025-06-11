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

def test_complete_field_mapping():
    """Test complete field mapping building on the successful AZ002854 customer structure."""
    print("🎯 TESTING COMPLETE FIELD MAPPING")
    print("=" * 60)
    print("Building on successful AZ002854 customer structure + missing fields")
    
    # Get session token
    response = requests.post(
        f"{BASE_URL}/v2/session/begin",
        auth=(STORE_CODE, API_KEY),
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code != 200:
        print("❌ Failed to get session token")
        return False
        
    session_token = response.json().get('sessionToken')
    
    # PDF extraction data
    supervisor_name = "Jackson Peters"
    supervisor_phone = "0447012125"
    
    po_number = f"COMPLETE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    install_date = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: AZ002854 success + phone/date/note/type fields")
    print(f"🔑 Theory: Add missing pieces to complete field population")
    
    # Complete structure with all missing fields added to successful base
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        # Keep successful customer structure from AZ002854
        "soldTo": {
            "customerId": 5,  # PROFILE BUILD GROUP
            "firstName": "Jackson",
            "lastName": "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "address2": "",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone": supervisor_phone,  # 🔑 Add phone field
            "email": "jackson.peters@example.com"
        },
        "shipTo": {
            "firstName": "Site",
            "lastName": "Customer", 
            "address1": "1505 ROSEBANK WAY WEST",
            "address2": "",
            "city": "HOPE ISLAND",
            "state": "QLD",
            "postalCode": "4212"
        },
        # 🔑 Add missing date fields
        "estimatedDeliveryDate": estimated_delivery,
        "quoteDate": datetime.now().strftime("%Y-%m-%d"),
        # 🔑 Add missing note fields  
        "privateNotes": f"COMPLETE TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"Complete Field Test: {supervisor_name} - {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        # 🔑 Add missing type fields
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "adSource": 1,
        # 🔑 Add lines with install date
        "lines": [
            {
                "productId": 213322,
                "colorId": 2133,
                "quantity": 1000.0,
                "priceLevel": "Price10",
                "installDate": install_date,  # 🔑 Install date
                "notes": f"PDF Supervisor: {supervisor_name}",
                "lineGroupId": 4
            }
        ]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Successful AZ002854 + all missing fields")
    print(f"🔑 Adding: phone, dates, notes, type IDs")
    
    response = requests.post(
        f"{BASE_URL}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        json=payload
    )
    
    print(f"📥 Response status: {response.status_code}")
    print(f"📥 Response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get("status") == "success":
                order_id = result.get('result')
                print(f"✅ SUCCESS! Complete order created: {order_id}")
                return True
            else:
                print(f"❌ Order creation failed: {result.get('result', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("🎯 COMPLETE FIELD MAPPING TEST")
    print("Building on successful AZ002854 structure + missing fields")
    print("=" * 70)
    
    success = test_complete_field_mapping()
    
    print(f"\n" + "=" * 70)
    print("🎯 FINAL RESULT:")
    if success:
        print("✅ SUCCESS! Complete field mapping test passed!")
    else:
        print("❌ Complete field mapping test failed") 
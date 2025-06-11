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

def get_session_token():
    """Get RFMS API session token."""
    try:
        response = requests.post(
            f"{BASE_URL}/v2/session/begin",
            auth=(STORE_CODE, API_KEY),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('sessionToken')
        else:
            print(f"Failed to get session token. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

def test_comprehensive_lines():
    """Test the comprehensive lines structure provided by user."""
    print("📦 TESTING COMPREHENSIVE LINES STRUCTURE")
    print("=" * 60)
    print("Using detailed lines format with all required fields")
    
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return False
    
    supervisor_name = "Jackson Peters"
    supervisor_phone1 = "0447012125"
    supervisor_phone2 = "0732341234"
    dollar_value = 1000.00
    
    po_number = f"COMPREHENSIVE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"💰 Dollar Value: ${dollar_value}")
    print(f"🎯 Testing comprehensive lines structure with detailed fields")
    
    # Successful AZ002876 payload + comprehensive lines structure
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone1}",
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
            "phone1": supervisor_phone1,
            "phone2": supervisor_phone2,
            "email": "jackson.peters@example.com"
        },
        "shipTo": {
            "firstName": "Site",
            "lastName": "Customer",
            "address1": "1505 ROSEBANK WAY WEST",
            "city": "HOPE ISLAND",
            "state": "QLD",
            "postalCode": "4212"
        },
        "privateNotes": f"COMPREHENSIVE LINES TEST - Supervisor: {supervisor_name}",
        "publicNotes": f"Testing detailed lines structure with ALL fields",
        "workOrderNotes": f"Contact: {supervisor_name} - {supervisor_phone1}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,
        "serviceTypeId": 8,
        "contractTypeId": 1,
        "adSource": 1,
        # 🔥 COMPREHENSIVE LINES STRUCTURE - User's format
        "lines": [
            {
                "id": "",
                "isUseTaxLine": False,
                "notes": "",
                "internalNotes": "",
                "productId": 213322,
                "colorId": 2133,
                "quantity": dollar_value,
                "serialNumber": "",
                "ecProductId": None,
                "ecColorId": None,
                "delete": False,
                "priceLevel": 10,
                "lineStatus": "none",
                "lineGroupId": 4
            }
        ]
    }
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"📦 Lines structure: Comprehensive with all detailed fields")
    print(f"🔑 Key fields: id, isUseTaxLine, notes, internalNotes, serialNumber, etc.")
    
    response = requests.post(
        f"{BASE_URL}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers={'Content-Type': 'application/json'},
        json=payload
    )
    
    print(f"📥 Status: {response.status_code}")
    print(f"📥 Response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get('status') == 'success':
                order_id = result.get('result')
                print(f"✅ SUCCESS! Comprehensive lines order: {order_id}")
                print(f"🎉 BREAKTHROUGH! Lines structure working!")
                
                # Show the successful lines structure
                print(f"\n📋 SUCCESSFUL LINES STRUCTURE:")
                lines_item = payload['lines'][0]
                for field, value in lines_item.items():
                    print(f"   {field}: {value}")
                
                return order_id
            else:
                print(f"❌ Failed: {result.get('result', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    print("📦 COMPREHENSIVE LINES TEST")
    print("Testing detailed lines structure with all required fields")
    print("=" * 70)
    
    order_id = test_comprehensive_lines()
    
    print(f"\n" + "=" * 70)
    print("🎯 COMPREHENSIVE LINES RESULT:")
    if order_id:
        print(f"✅ SUCCESS! Comprehensive lines structure works! Order: {order_id}")
        print("🎉 MAJOR BREAKTHROUGH - Lines field solved!")
        print("📋 Key: Use detailed structure with all fields:")
        print("   ✅ id, isUseTaxLine, notes, internalNotes")
        print("   ✅ productId, colorId, quantity")
        print("   ✅ serialNumber, ecProductId, ecColorId")
        print("   ✅ delete, priceLevel, lineStatus, lineGroupId")
        print("🔧 Now we have COMPLETE order creation capability!")
        print("📋 Final structure: Customer fields + phone fields + comprehensive lines = COMPLETE")
    else:
        print("❌ Comprehensive lines test failed")
        print("🔍 Need to investigate further") 
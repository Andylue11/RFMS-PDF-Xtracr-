import os
import sys
import json
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env-test')

# RFMS API Configuration
BASE_URL = os.getenv('RFMS_BASE_URL')
STORE_CODE = os.getenv('RFMS_STORE_CODE')
API_KEY = os.getenv('RFMS_API_KEY')

def get_session_token():
    """Get RFMS API session token."""
    response = requests.post(
        f"{BASE_URL}/v2/session/begin",
        auth=(STORE_CODE, API_KEY),
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        return response.json().get('sessionToken')
    return None

def test_devb_flat_payload():
    """Test the exact DevB flat payload structure."""
    print("🧪 Testing DevB Flat Payload Structure")
    print("=" * 50)
    
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return
    
    print("✅ Session token obtained")
    
    # Generate unique identifiers
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    po_number = f"DEVB-FLAT-{timestamp}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # DevB flat payload - EXACT structure from your example
    payload = json.dumps({
        "username": "zoran.vekic",
        "createOrder": True,
        "category": "Order",
        "poNumber": po_number,
        "adSource": 1,
        "quoteDate": None,
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": f"ZV-{po_number}",
        "customerSource": "Customer",
        "customerSeqNum": 1747,
        "customerUpSeqNum": 0,
        "customerFirstName": "DEVB",
        "customerLastName": "FLATTEST",
        "customerAddress1": "999 DEVB FLAT STREET",
        "customerAddress2": "LEVEL FLAT",
        "customerCity": "FLATVILLE",
        "customerState": "QLD",
        "customerPostalCode": "9999",
        "customerCounty": None,
        "customerPhone1": "0799999999",
        "customerPhone2": "0488888888",
        "customerEmail": "devb.flat.test@example.com",
        "shipTo": {
            "lastName": "FLATTEST",
            "firstName": "DEVB",
            "address1": "999 DEVB FLAT STREET",
            "address2": "LEVEL FLAT",
            "city": "FLATVILLE",
            "state": "QLD",
            "postalCode": "9999",
            "county": None
        },
        "storeNumber": 49,
        "privateNotes": f"PRIVATE - DEVB FLAT TEST {timestamp}",
        "publicNotes": f"PUBLIC - DEVB FLAT PAYLOAD TEST {timestamp}",
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": None,
        "UserOrderType": 18,
        "ServiceType": 8,
        "ContractType": 1,
        "PriceLevel": 3,
        "TaxStatus": "Tax",
        "Occupied": False,
        "Voided": False,
        "TaxStatusLocked": False,
        "TaxInclusive": False,
        "lines": [
            {
                "productId": "213322",
                "colorId": "2133",
                "quantity": 1500.0,
                "priceLevel": 10,
                "lineGroupId": 4
            }
        ]
    })
    
    print(f"📤 Endpoint: {BASE_URL}/v2/order/create")
    print(f"📦 PO Number: {po_number}")
    print(f"🔍 Look for: DEVB FLATTEST, 999 DEVB FLAT STREET, FLATVILLE")
    
    # Send request - using /v2/order/create with v2 prefix
    response = requests.post(
        f"{BASE_URL}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers={'Content-Type': 'application/json'},
        data=payload
    )
    
    print(f"📊 Status: {response.status_code}")
    print(f"📄 Response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get("status") == "success":
                order_number = result.get("result")
                print(f"✅ DEVB Flat Order Created: {order_number}")
                print("\n🔍 VERIFICATION NEEDED:")
                print(f"   1. Check order {order_number} in RFMS system")
                print("   2. Look for customer name: 'DEVB FLATTEST'")
                print("   3. Look for address: '999 DEVB FLAT STREET, FLATVILLE'")
                print(f"   4. Look for PO number: '{po_number}'")
                print(f"   5. Look for notes containing: '{timestamp}'")
                return order_number
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
    
    print("❌ DevB flat payload test failed")
    return None

if __name__ == "__main__":
    test_devb_flat_payload() 
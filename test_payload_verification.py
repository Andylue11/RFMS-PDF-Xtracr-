import os
import sys
import json
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('.env-test')

# RFMS API Configuration  
BASE_URL = os.getenv('RFMS_BASE_URL')
STORE_CODE = os.getenv('RFMS_STORE_CODE')
STORE_NUMBER = os.getenv('RFMS_STORE_NUMBER', '49')
USERNAME = os.getenv('RFMS_USERNAME')
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
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

def test_devb_payload(session_token, customer_id, dollar_value):
    """Test the DevB flat payload structure."""
    print("\n" + "="*60)
    print("🧪 TESTING: DevB Flat Payload Structure")
    print("="*60)
    
    po_number = f"DEVB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # DevB payload structure (flat) - exactly as provided
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
        "customerSeqNum": customer_id,
        "customerUpSeqNum": 0,
        "customerFirstName": "DevB",
        "customerLastName": "TestUser",
        "customerAddress1": "123 DevB Street",
        "customerAddress2": "Suite B",
        "customerCity": "Brisbane",
        "customerState": "QLD",
        "customerPostalCode": "4000",
        "customerCounty": None,
        "customerPhone1": "0712345678",
        "customerPhone2": "0423456789",
        "customerEmail": "devb.test@example.com",
        "shipTo": {
            "lastName": "TestUser",
            "firstName": "DevB",
            "address1": "123 DevB Street",
            "address2": "Suite B",
            "city": "Brisbane",
            "state": "QLD",
            "postalCode": "4000",
            "county": None
        },
        "storeNumber": 49,
        "privateNotes": "PRIVATE - DevB payload test order",
        "publicNotes": "PUBLIC - DevB payload structure test",
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
                "quantity": float(dollar_value),
                "priceLevel": 10,
                "lineGroupId": 4
            }
        ]
    })

    print(f"📤 Sending to: {BASE_URL}/order/create")
    print(f"📦 PO Number: {po_number}")
    
    response = requests.post(
        f"{BASE_URL}/order/create",  # Non-v2 endpoint as in DevB
        auth=(STORE_CODE, session_token),
        headers={'Content-Type': 'application/json'},
        data=payload
    )
    
    print(f"📊 Response Status: {response.status_code}")
    print(f"📄 Response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get("status") == "success":
                order_number = result.get("result")
                print(f"✅ DevB Order Created: {order_number}")
                return order_number, "devb_flat"
        except:
            pass
    
    return None, "devb_flat"

def main():
    """Main testing function."""
    print("🧪 RFMS PAYLOAD VERIFICATION TESTING")
    print("="*60)
    print("Testing DevB flat payload structure")
    print("API Docs: https://api2docs.rfms.online/?version=latest#37a93689-1503-4605-8e5c-f490d615cac0")
    
    # Get session token
    print("\n🔐 Getting session token...")
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token. Exiting.")
        sys.exit(1)
    print("✅ Session token obtained")

    # Test DevB flat payload structure
    devb_order, devb_type = test_devb_payload(session_token, 1747, 1500.00)
    
    print("\n" + "="*60)
    print("📊 RESULTS")
    print("="*60)
    if devb_order:
        print(f"✅ Order Created: {devb_order}")
        print("🔍 Next step: Manual verification needed")
        print("   - Check RFMS system to see if order contains DevB test data")
        print("   - Look for: 'DevB TestUser', '123 DevB Street', 'Brisbane'")
    else:
        print("❌ Order creation failed")

if __name__ == "__main__":
    main()
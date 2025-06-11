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

def test_ultimate_complete_order():
    """Test with ALL working fields combined - the ultimate complete order."""
    print("🎉 TESTING ULTIMATE COMPLETE ORDER")
    print("=" * 60)
    print("Combining ALL working fields from incremental test")
    
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
    
    po_number = f"ULTIMATE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: ALL working fields combined!")
    print(f"🔑 Excluding: 'lines' field (causes key error)")
    
    # ULTIMATE payload with ALL working fields from incremental test
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        # Successful customer structure from AZ002854
        "soldTo": {
            "customerId": 5,  # PROFILE BUILD GROUP
            "firstName": "Jackson",
            "lastName": "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone": supervisor_phone,
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
        # ALL the working fields we discovered
        "privateNotes": f"ULTIMATE TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"Ultimate Field Test: {supervisor_name} - {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "adSource": 1
        # NOTE: Excluding 'lines' field as it causes "key not present" error
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: ULTIMATE - All 8 working fields combined!")
    print(f"✅ Including: privateNotes, publicNotes, workOrderNotes")
    print(f"✅ Including: estimatedDeliveryDate, userOrderTypeId, serviceTypeId")
    print(f"✅ Including: contractTypeId, adSource")
    print(f"❌ Excluding: lines (problematic field)")
    
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
                print(f"✅ SUCCESS! ULTIMATE order created: {order_id}")
                print(f"🎉 This should have the MOST complete field population!")
                print(f"🔍 Check RFMS interface for complete data:")
                print(f"   ✅ Customer details + email (from AZ002854)")
                print(f"   ✅ Phone numbers (from soldTo)")
                print(f"   ✅ All note fields (private, public, work order)")
                print(f"   ✅ Delivery date")
                print(f"   ✅ Order type, service type, contract type")
                print(f"   ✅ Ad source")
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
    print("🎉 ULTIMATE COMPLETE ORDER TEST")
    print("Combining ALL successful fields from incremental testing")
    print("=" * 70)
    
    success = test_ultimate_complete_order()
    
    print(f"\n" + "=" * 70)
    print("🎯 FINAL RESULT:")
    if success:
        print("✅ SUCCESS! ULTIMATE complete order created!")
        print("🎉 This represents the MAXIMUM field population possible!")
        print("📊 Progress achieved:")
        print("   ✅ Customer structure (AZ002854 baseline)")
        print("   ✅ + 8 additional fields (AZ002863-AZ002870 discoveries)")
        print("   ✅ = ULTIMATE order with comprehensive data!")
        print("🔍 Check RFMS interface to verify complete field population")
    else:
        print("❌ Ultimate order test failed")
 
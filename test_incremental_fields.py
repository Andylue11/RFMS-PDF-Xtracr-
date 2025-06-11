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
    response = requests.post(
        f"{BASE_URL}/v2/session/begin",
        auth=(STORE_CODE, API_KEY),
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        return response.json().get('sessionToken')
    else:
        print(f"❌ Failed to get session token: {response.status_code}")
        return None

def test_incremental_field_addition():
    """Test adding fields one by one to the successful AZ002854 structure."""
    print("🔍 TESTING INCREMENTAL FIELD ADDITION")
    print("=" * 60)
    print("Adding ONE field at a time to successful AZ002854 structure")
    
    session_token = get_session_token()
    if not session_token:
        return False
    
    supervisor_name = "Jackson Peters"
    supervisor_phone = "0447012125"
    
    # Base successful structure from AZ002854
    base_payload = {
        "category": "Order",
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
        }
    }
    
    # Fields to test adding one by one
    test_fields = [
        ("privateNotes", f"TEST - PDF Supervisor: {supervisor_name}"),
        ("publicNotes", f"Field Test: {supervisor_name} - {supervisor_phone}"),
        ("workOrderNotes", f"Contact: {supervisor_name} - Phone: {supervisor_phone}"),
        ("estimatedDeliveryDate", (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")),
        ("userOrderTypeId", 18),
        ("serviceTypeId", 8),
        ("contractTypeId", 1),
        ("adSource", 1),
        ("lines", [{"productId": 213322, "colorId": 2133, "quantity": 1000.0, "priceLevel": "Price10"}])
    ]
    
    results = []
    
    for field_name, field_value in test_fields:
        print(f"\n🧪 Testing addition of: {field_name}")
        
        # Create payload with current field added
        test_payload = base_payload.copy()
        test_payload["poNumber"] = f"INCR-{field_name.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_payload[field_name] = field_value
        
        response = requests.post(
            f"{BASE_URL}/v2/order/create",
            auth=(STORE_CODE, session_token),
            headers={'Content-Type': 'application/json'},
            json=test_payload
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    order_id = result.get('result')
                    print(f"✅ SUCCESS! Field '{field_name}' added successfully: {order_id}")
                    results.append((field_name, "SUCCESS", order_id))
                else:
                    error = result.get('result', 'Unknown error')
                    print(f"❌ FAILED! Field '{field_name}' caused error: {error}")
                    results.append((field_name, "FAILED", error))
            except Exception as e:
                print(f"❌ ERROR parsing response: {str(e)}")
                results.append((field_name, "ERROR", str(e)))
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            results.append((field_name, "HTTP_ERROR", response.status_code))
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 INCREMENTAL FIELD TEST RESULTS:")
    print("=" * 60)
    
    for field_name, status, details in results:
        if status == "SUCCESS":
            print(f"✅ {field_name:20} | SUCCESS | Order: {details}")
        else:
            print(f"❌ {field_name:20} | {status:8} | {details}")
    
    successful_fields = [r[0] for r in results if r[1] == "SUCCESS"]
    failed_fields = [r[0] for r in results if r[1] != "SUCCESS"]
    
    print(f"\n📈 SUMMARY:")
    print(f"✅ Successful fields: {', '.join(successful_fields) if successful_fields else 'None'}")
    print(f"❌ Failed fields: {', '.join(failed_fields) if failed_fields else 'None'}")
    
    return len(successful_fields) > 0

if __name__ == "__main__":
    print("🔍 INCREMENTAL FIELD ADDITION TEST")
    print("Testing which fields can be added to successful AZ002854 structure")
    print("=" * 70)
    
    success = test_incremental_field_addition()
    
    print(f"\n" + "=" * 70)
    print("🎯 FINAL RESULT:")
    if success:
        print("✅ Some fields can be successfully added!")
        print("🔍 Check results above to see which ones work")
    else:
        print("❌ All additional fields failed")
        print("💡 Stick with the successful AZ002854 structure") 
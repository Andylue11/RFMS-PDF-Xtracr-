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
STORE_NUMBER = os.getenv('RFMS_STORE_NUMBER', '49')  # Default to 49 if not set
USERNAME = os.getenv('RFMS_USERNAME')
API_KEY = os.getenv('RFMS_API_KEY')

def load_pdf_extraction_data(json_file_path="test_extractor_output.json"):
    """Load PDF extraction data from JSON file."""
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as f:
                return json.load(f)
        else:
            print(f"PDF extraction data file not found: {json_file_path}")
            return None
    except Exception as e:
        print(f"Error loading PDF extraction data: {str(e)}")
        return None

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

def create_successful_order(base_url, session_token, customer_id):
    """Create an order using the successful AZ002876 payload structure."""
    print(f"\n🎯 Creating order with SUCCESSFUL AZ002876 structure")
    print(f"Customer ID: {customer_id}")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"  # Default fallback
    supervisor_phone1 = "0447012125"    # Primary phone (mobile)
    supervisor_phone2 = "0732341234"    # Secondary phone (office)
    
    if pdf_data:
        # Extract supervisor info from PDF data
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        extracted_phone = job_details.get("supervisor_phone") or job_details.get("supervisor_mobile")
        if extracted_phone:
            supervisor_phone1 = extracted_phone
        print(f"📄 Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone1}")
    
    # Generate a unique PO number for this test
    po_number = f"SUCCESS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"📞 Mobile: {supervisor_phone1} | Office: {supervisor_phone2}")
    
    # SUCCESSFUL AZ002876 payload structure - MAXIMUM FIELD POPULATION
    payload = {
        "category": "Order",  # Prevents weborders
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone1}",
        "storeNumber": int(STORE_NUMBER),
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        # Successful customer structure with phone1/phone2 ONLY in soldTo
        "soldTo": {
            "customerId": customer_id,
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "lastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "address2": "",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone1": supervisor_phone1,    # Mobile phone - ONLY HERE
            "phone2": supervisor_phone2,    # Office phone - ONLY HERE
            "email": f"{supervisor_name.lower().replace(' ', '.')}@example.com"
        },
        "shipTo": {
            "firstName": "Site",
            "lastName": "Customer",
            "address1": "1505 ROSEBANK WAY WEST",
            "address2": "",
            "city": "HOPE ISLAND",
            "state": "QLD",
            "postalCode": "4212"
            # NO phone fields in shipTo
        },
        # All successful fields from AZ002876
        "privateNotes": f"PDF Extracted - Supervisor: {supervisor_name}",
        "publicNotes": f"Customer Phones: Mobile {supervisor_phone1}, Office {supervisor_phone2}",
        "workOrderNotes": f"Contact: {supervisor_name} - Mobile: {supervisor_phone1} | Office: {supervisor_phone2}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "adSource": 1
        # NOTE: lines field excluded - causes "key not present" error
    }

    headers = {'Content-Type': 'application/json'}

    print(f"📤 Sending to: {base_url}/v2/order/create")
    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        json=payload
    )
    
    print(f"📥 Response status: {response.status_code}")
    print(f"📥 Response: {response.text}")
    
    result = response.json()
    if result.get("status") == "success":
        order_id = result.get('result')
        print(f"✅ SUCCESS! Order created: {order_id}")
        return order_id, po_number
    else:
        print(f"❌ Failed: {result.get('result', 'Unknown error')}")
        return None, None

def test_lines_variations(base_url, session_token, customer_id):
    """Test different lines field structures to solve the lines issue."""
    print(f"\n🔧 TESTING LINES VARIATIONS")
    print("=" * 50)
    print("Testing different lines structures to solve 'key not present' error")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"
    supervisor_phone1 = "0447012125"
    supervisor_phone2 = "0732341234"
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        extracted_phone = job_details.get("supervisor_phone") or job_details.get("supervisor_mobile")
        if extracted_phone:
            supervisor_phone1 = extracted_phone
    
    # Base successful payload from AZ002876
    base_payload = {
        "category": "Order",
        "jobNumber": f"{supervisor_name} {supervisor_phone1}",
        "storeNumber": int(STORE_NUMBER),
        "salesperson1": "ZORAN VEKIC",
        "soldTo": {
            "customerId": customer_id,
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
        "privateNotes": f"LINES TEST - Supervisor: {supervisor_name}",
        "publicNotes": f"Testing lines structures",
        "workOrderNotes": f"Contact: {supervisor_name} - {supervisor_phone1}",
        "estimatedDeliveryDate": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "userOrderTypeId": 18,
        "serviceTypeId": 8,
        "contractTypeId": 1,
        "adSource": 1
    }
    
    # Different lines structures to test
    lines_variations = [
        ("Minimal Lines", [{"productId": 213322}]),
        ("Lines with Color", [{"productId": 213322, "colorId": 2133}]),
        ("Lines with Quantity", [{"productId": 213322, "colorId": 2133, "quantity": 1000}]),
        ("String ProductId", [{"productId": "213322", "colorId": "2133", "quantity": 1000}]),
        ("Lines with Price", [{"productId": 213322, "colorId": 2133, "quantity": 1000, "price": 195.50}]),
        ("Lines with PriceLevel", [{"productId": 213322, "colorId": 2133, "quantity": 1000, "priceLevel": 10}]),
        ("orderLines Format", [{"productId": 213322, "colorId": 2133, "quantity": 1000, "unitPrice": 195.50}])
    ]
    
    results = []
    
    for test_name, lines_structure in lines_variations:
        print(f"\n🧪 Testing: {test_name}")
        
        # Create test payload with current lines structure
        test_payload = base_payload.copy()
        test_payload["poNumber"] = f"LINES-{test_name.upper().replace(' ', '-')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_payload["lines"] = lines_structure
        
        response = requests.post(
            f"{base_url}/v2/order/create",
            auth=(STORE_CODE, session_token),
            headers={'Content-Type': 'application/json'},
            json=test_payload
        )
        
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get("status") == "success":
                    order_id = result.get('result')
                    print(f"✅ SUCCESS! {test_name}: {order_id}")
                    results.append((test_name, "SUCCESS", order_id))
                else:
                    error = result.get('result', 'Unknown error')
                    print(f"❌ FAILED! {test_name}: {error}")
                    results.append((test_name, "FAILED", error))
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                results.append((test_name, "ERROR", str(e)))
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            results.append((test_name, "HTTP_ERROR", response.status_code))
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 LINES VARIATIONS TEST RESULTS:")
    print("=" * 60)
    
    for test_name, status, details in results:
        if status == "SUCCESS":
            print(f"✅ {test_name:20} | SUCCESS | Order: {details}")
        else:
            print(f"❌ {test_name:20} | {status:8} | {details}")
    
    successful_structures = [r for r in results if r[1] == "SUCCESS"]
    failed_structures = [r for r in results if r[1] != "SUCCESS"]
    
    print(f"\n📈 LINES SUMMARY:")
    if successful_structures:
        print(f"✅ Working lines structures: {len(successful_structures)}")
        for test_name, _, order_id in successful_structures:
            print(f"   🎯 {test_name}: {order_id}")
    else:
        print(f"❌ No working lines structures found")
    
    if failed_structures:
        print(f"❌ Failed lines structures: {len(failed_structures)}")
    
    return len(successful_structures) > 0

def main():
    """Main function to test the successful structure and work on lines issue."""
    print("🎯 RFMS ORDER CREATION - SUCCESSFUL STRUCTURE + LINES")
    print("=" * 70)
    print("Using ONLY the successful AZ002876 payload structure")
    print("Focus: Solving the lines field issue")
    
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return False
    
    customer_id = 5  # PROFILE BUILD GROUP
    
    print("\n1️⃣ Testing successful structure (without lines)...")
    order_id, po_number = create_successful_order(BASE_URL, session_token, customer_id)
    
    if order_id:
        print(f"✅ Baseline successful order: {order_id}")
        print("\n2️⃣ Now testing lines variations...")
        lines_success = test_lines_variations(BASE_URL, session_token, customer_id)
        
        print(f"\n" + "=" * 70)
        print("🎯 FINAL RESULTS:")
        print(f"✅ Successful payload structure: WORKING (AZ002876 format)")
        print(f"📞 Phone fields: WORKING (phone1/phone2 in soldTo)")
        print(f"🔧 Lines field: {'WORKING' if lines_success else 'NEEDS MORE WORK'}")
        
        if lines_success:
            print("🎉 SUCCESS! Complete order structure with lines!")
        else:
            print("🔍 Lines field still needs investigation")
            print("💡 May need different field names or structure")
    else:
        print("❌ Baseline structure failed - check configuration")

if __name__ == "__main__":
    main() 
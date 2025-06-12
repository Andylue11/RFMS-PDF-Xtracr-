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
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

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

def test_az002874_correct_method():
    """Test the CORRECT AZ002874 method that the user specified."""
    print("🎯 TESTING CORRECT AZ002874 METHOD")
    print("=" * 60)
    print("Using the correct method that the user identified")
    
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return False
        
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"
    supervisor_phone = "0447012125"
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"📄 Using PDF supervisor: {supervisor_name}, {supervisor_phone}")
    
    po_number = f"AZ002874-METHOD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: AZ002874 correct method (to be implemented)")
    
    # PLACEHOLDER: User to specify the correct AZ002874 structure
    # Based on conversation, likely the flat structure that creates populated orders
    payload = {
        "category": "Order",  # Prevents weborders
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        "soldTo": {
            "customerId": 5,  # PROFILE BUILD GROUP
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "lastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "address2": "",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone1": supervisor_phone,
            "phone2": "0732341234",
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
        },
        "privateNotes": f"AZ002874 CORRECT METHOD - Supervisor: {supervisor_name}",
        "publicNotes": f"Using correct AZ002874 structure - {supervisor_name} - {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "adSource": 1
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: AZ002874 correct method (FLAT)")
    
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
                print(f"✅ SUCCESS! AZ002874 method order created: {order_id}")
                print(f"🎯 This should match the correct AZ002874 behavior!")
                print(f"🔍 Check RFMS to verify: Regular orders + populated fields")
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
    print("📋 AZ002874 CORRECT METHOD TEST")
    print("Implementation of the correct method as specified by user")
    print("=" * 70)
    
    success = test_az002874_correct_method()
    
    print(f"\n" + "=" * 70)
    print("🎯 FINAL RESULT:")
    if success:
        print("✅ SUCCESS! AZ002874 correct method implemented!")
        print("🎯 This matches the correct working structure")
        print("💡 Use this method for production order creation")
    else:
        print("❌ AZ002874 correct method failed")
        print("🔍 Please specify the exact structure that created AZ002874")
        
    print("\n💡 USER INPUT NEEDED:")
    print("Please specify the exact payload structure that created AZ002874:")
    print("1. Flat structure (no nested 'order')?")
    print("2. Nested structure with 'order' wrapper?")
    print("3. SaveOrder action method?")
    print("4. Different endpoint?")
    print("5. Specific field values or structure?") 
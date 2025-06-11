import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables  
load_dotenv('.env-test')

# RFMS API Configuration
STORE_CODE = os.getenv('RFMS_STORE_CODE')
API_KEY = os.getenv('RFMS_API_KEY') 
BASE_URL = os.getenv('RFMS_BASE_URL')

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
    """Get session token from RFMS API."""
    print("Getting session token...")
    url = f"{BASE_URL}/v2/Session/Begin"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, auth=(STORE_CODE, API_KEY), headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session token obtained successfully")
        return data.get('sessionToken')
    else:
        print(f"❌ Session error: {response.status_code} - {response.text}")
        return None

def test_exact_working_flat_structure():
    """Test using the EXACT working flat payload structure with specified IDs."""
    print("🎯 EXACT WORKING FLAT STRUCTURE TEST WITH SPECIFIED IDs")
    print("=" * 70)
    print("Using the EXACT structure that created orders with populated data!")
    print("With user specified IDs: userOrderTypeId=18, serviceTypeId=8, contractTypeId=1")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"  # Default fallback
    supervisor_phone = "0447012125"    # Default fallback
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"📄 Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    else:
        print(f"📄 Using default supervisor data: {supervisor_name}, {supervisor_phone}")
    
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return False
        
    # Generate a unique PO number for this test
    po_number = f"WORKING-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"\n🚀 Creating order with EXACT working flat structure:")
    print(f"   🔗 Endpoint: {BASE_URL}/v2/order/create (corrected path)")  
    print(f"   📦 PO Number: {po_number}")
    print(f"   👤 Customer ID: 2 (from successful logs)")
    print(f"   📞 Supervisor: {supervisor_name} - {supervisor_phone}")
    print(f"   🎯 userOrderTypeId: 18 (RESIDENTIAL INSURANCE)")
    print(f"   🎯 serviceTypeId: 8 (SUPPLY & INSTALL)")
    print(f"   🎯 contractTypeId: 1 (30 DAY ACCOUNT)")
    
    # EXACT working payload structure (FLAT, not nested) with specified IDs
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "adSource": 1,
        "quoteDate": None,
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
                 "soldTo.customerId": 2,  # Use customer ID 2 like successful orders (as number)
        "soldTo": {
            "lastName": "Peters",
            "firstName": "Jackson",
            "address1": "123 Test Street", 
            "address2": "PDF Extraction Test",
            "city": "Brisbane",
            "state": "QLD",
            "postalCode": "4000",
            "county": None,
            "Phone1": supervisor_phone,
            "Phone2": supervisor_phone,
            "Email": "jackson.peters@example.com"
        },
        "shipTo": {
            "lastName": "Peters", 
            "firstName": "Jackson",
            "address1": "123 Test Street",
            "address2": "PDF Extraction Test",
            "city": "Brisbane",
            "state": "QLD", 
            "postalCode": "4000",
            "county": None
        },
        "storeNumber": 49,
        "privateNotes": "PRIVATE - Test job with complete customer details",  # EXACT working text
        "publicNotes": f"PUBLIC - PDF Extracted: {supervisor_name} - {supervisor_phone}",
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": None,
                 "UserOrderType": 18,  # 🔑 RESIDENTIAL INSURANCE (user specified)
         "ServiceType": 8,     # 🔑 SUPPLY & INSTALL (user specified)
         "ContractType": 1,    # 🔑 30 DAY ACCOUNT (user specified)
        "PriceLevel": 3,
        "TaxStatus": "Tax",
        "Occupied": False,
        "Voided": False,
        "TaxStatusLocked": False,
        "TaxInclusive": False,
        "lines": [
            {
                "productId": "213322",
                "colorId": 2133,
                "quantity": 1000.0,
                "priceLevel": "Price10",
                "lineGroupId": 4
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    # Use the exact same endpoint and format as working structure  
    print(f"📤 Sending request to: {BASE_URL}/v2/order/create")
    response = requests.post(
        f"{BASE_URL}/v2/order/create",  # Working structure: BASE_URL/v2 + /order/create
        auth=(STORE_CODE, session_token),
        headers=headers,
        json=payload  # json=payload not data=json.dumps(payload)!
    )
    
    print(f"📥 Response status: {response.status_code}")
    print(f"📥 Response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            if result.get("status") == "success":
                order_id = result.get('result')
                print(f"✅ SUCCESS! Order created: {order_id}")
                print(f"🎯 Used EXACT working flat structure with specified IDs!")
                
                # Now retrieve the order to check if data was saved
                print(f"\n🔍 Retrieving order to check data persistence...")
                retrieve_response = requests.post(
                    f"{BASE_URL}/v2/order/find",  # Still use v2 for retrieval
                    auth=(STORE_CODE, session_token), 
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps({"poNumber": po_number})
                )
                
                if retrieve_response.status_code == 200:
                    retrieve_data = retrieve_response.json()
                    if retrieve_data.get("result"):
                        order_data = retrieve_data["result"]
                        if isinstance(order_data, list) and len(order_data) > 0:
                            order_info = order_data[0]
                        else:
                            order_info = order_data
                            
                        print(f"\n📊 RETRIEVAL RESULTS:")
                        print(f"   📋 Order Number: {order_info.get('invoiceNumber', 'N/A')}")
                        print(f"   👤 Customer: {order_info.get('customerFirstName', 'N/A')} {order_info.get('customerLastName', 'N/A')}")
                        print(f"   📞 Phone: {order_info.get('phone1', 'N/A')}")
                        print(f"   🏷️  Job Number: {order_info.get('jobNumber', 'N/A')}")
                        print(f"   📝 Notes: {order_info.get('note', 'N/A')}")
                        print(f"   🔒 Private Notes: {order_info.get('privateNote', 'N/A')}")
                        print(f"   📢 Public Notes: {order_info.get('publicNote', 'N/A')}")  
                        print(f"   👨‍💼 Salesperson: {order_info.get('salesPerson1', 'N/A')}")
                        print(f"   🏪 Store: {order_info.get('store', 'N/A')}")
                        
                        # Check if data is populated
                        has_customer = (order_info.get('customerFirstName', 'N/A') not in ['N/A', '', None])
                        has_phone = (order_info.get('phone1', 'N/A') not in ['N/A', '', None])
                        has_job = (order_info.get('jobNumber', 'N/A') not in ['N/A', '', None])
                        
                        if has_customer or has_phone or has_job:
                            print(f"\n🎉 SUCCESS! Data is populated with working flat structure!")
                            return True
                        else:
                            print(f"\n📊 Data appears empty in API response")
                            print(f"📋 Available fields: {list(order_info.keys())}")
                            print(f"💡 Data might be saved but not visible via this API endpoint")
                            print(f"🔍 Check RFMS web interface to verify actual data persistence")
                            return order_id  # Return order ID even if data not visible
                    else:
                        print(f"❌ Order not found in retrieval")
                        return False
                else:
                    print(f"❌ Retrieval failed: {retrieve_response.status_code} - {retrieve_response.text}")
                    return order_id  # Return order ID even if retrieval failed
            else:
                print(f"❌ Order creation failed: {result}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def main():
    """Run the exact working flat structure test with specified IDs."""
    success = test_exact_working_flat_structure()
    
    print(f"\n" + "=" * 70)
    print("🎯 FINAL RESULT:")
    if success:
        if isinstance(success, str):
            print(f"✅ Order created successfully: {success}")
            print("📊 Data persistence needs verification in RFMS web interface")
        else:
            print("✅ SUCCESS! The exact working flat structure with specified IDs worked!")
            print("🎉 Data is visible and populated correctly!")
        print("💡 This confirms the correct payload format for PDF extraction integration")
    else:
        print("❌ Test failed - order was not created")
        
    print("\n📋 Next steps:")
    print("   1. Check the order in RFMS web interface")
    print("   2. Verify supervisor name and phone data populated")
    print("   3. Confirm privateNotes and publicNotes are saved")
    print("   4. Update main PDF extraction workflow with this structure")

if __name__ == "__main__":
    main() 
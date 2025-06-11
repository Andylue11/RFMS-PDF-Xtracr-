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

def create_test_order(base_url, session_token, customer_id, dollar_value, commencement_date=None):
    """Create a test order using the successful AZ002876 payload structure."""
    print(f"\nCreating test order for customer ID: {customer_id}")
    
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
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone1}")
    
    # Generate a unique PO number for this test
    po_number = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Calculate estimated delivery date
    if commencement_date:
        estimated_delivery = commencement_date
    else:
        # Default to today + 5 days if no commencement date provided
        estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Use the successful AZ002876 payload structure - MAXIMUM FIELD POPULATION
    payload = {
        "category": "Order",  # Prevents weborders
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone1}",
        "storeNumber": int(STORE_NUMBER),
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        # Successful customer structure with phone1/phone2
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

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        json=payload
    )
    print(f"Order creation response status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.json()

def retrieve_order(base_url, session_token, po_number):
    """Retrieve an order by PO number to check what data was saved."""
    print(f"\nRetrieving order with PO: {po_number}")
    
    payload = json.dumps({"poNumber": po_number})
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{base_url}/v2/order/find",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    
    print(f"Order retrieval response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        result = data.get("result")
        if result:
            # Handle both list and dict responses
            if isinstance(result, list):
                if len(result) > 0:
                    order = result[0]  # Get first order from list
                else:
                    print("No orders found in response")
                    return None
            else:
                order = result
            
            print(f"Order found: {order.get('invoiceNumber', 'N/A')}")
            print(f"PO Number: {order.get('poNumber', 'N/A')}")
            print(f"Job Number: {order.get('jobNumber', 'N/A')}")
            print(f"Customer: {order.get('customerFirstName', 'N/A')} {order.get('customerLastName', 'N/A')}")
            print(f"Notes: {order.get('note', 'N/A')}")
            print(f"Work Order Notes: {order.get('workOrderNote', 'N/A')}")
            print(f"Salesperson: {order.get('salesPerson1', 'N/A')}")
            print(f"Store: {order.get('store', 'N/A')}")
            print(f"Phone1: {order.get('phone1', 'N/A')}")
            print(f"Email: {order.get('email', 'N/A')}")
            return order
        else:
            print("No order found")
            return None
    else:
        print(f"Error retrieving order: {response.text}")
        return None

def save_order(base_url, session_token, order_id):
    """Try to save/finalize an order using SaveOrder method."""
    print(f"\nAttempting to save order: {order_id}")
    
    # Try different HTTP methods and endpoints
    endpoints = [
        f"{base_url}/v2/order/save",
        f"{base_url}/v2/order/{order_id}/save",
        f"{base_url}/v2/order/update",
        f"{base_url}/v2/order/{order_id}",
        f"{base_url}/v2/order/commit",
        f"{base_url}/v2/order/finalize"
    ]
    
    methods = ["POST", "PUT", "PATCH"]
    
    payload = {"orderId": order_id}
    
    for endpoint in endpoints:
        for method in methods:
            print(f"Trying {method} {endpoint}")
            
            try:
                if method == "POST":
                    response = requests.post(endpoint, auth=(STORE_CODE, session_token), 
                                           headers={'Content-Type': 'application/json'}, 
                                           data=json.dumps(payload))
                elif method == "PUT":
                    response = requests.put(endpoint, auth=(STORE_CODE, session_token), 
                                          headers={'Content-Type': 'application/json'}, 
                                          data=json.dumps(payload))
                elif method == "PATCH":
                    response = requests.patch(endpoint, auth=(STORE_CODE, session_token), 
                                            headers={'Content-Type': 'application/json'}, 
                                            data=json.dumps(payload))
                
                print(f"Response: {response.status_code} - {response.text[:100]}")
                
                if response.status_code in [200, 201, 204]:
                    print(f"✓ SUCCESS with {method} {endpoint}")
                    return response.json() if response.text else {"success": True}
                    
            except Exception as e:
                print(f"Error: {str(e)}")
    
    return None

def test_nested_structure(base_url, session_token, customer_id):
    """Test the working nested structure with minimal required fields."""
    print(f"\n=== TESTING WORKING NESTED STRUCTURE ===")
    
    po_number = f"NESTED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    payload = json.dumps({
        "category": "Order",  # Add this to match working examples
        "username": "zoran.vekic",
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": customer_id,
            "CustomerUpSeqNum": customer_id,
            "CustomerFirstName": "Jackson",
            "CustomerLastName": "Peters",
            "CustomerAddress1": "123 Test St",
            "CustomerAddress2": "",
            "CustomerCity": "Brisbane",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4000",
            "CustomerCounty": "",
            "Phone1": "0447012125",
            "ShipToFirstName": "Jackson",
            "ShipToLastName": "Peters",
            "ShipToAddress1": "123 Test St",
            "ShipToAddress2": "",
            "ShipToCity": "Brisbane",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4000",
            "Phone2": "0447012125",
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": "jackson@example.com",
            "CustomNote": "Supervisor: Jackson Peters",
            "Note": "PDF Extracted - Jackson Peters supervisor",
            "WorkOrderNote": "",
            "PickingTicketNote": None,
            "OrderDate": "",
            "MeasureDate": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "PromiseDate": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "PONumber": po_number,  # Changed from PONum to PONumber
            "adSource": 1,  # Add adSource field as suggested
            "CustomerType": "INSURANCE",
            "JobNumber": "Jackson Peters 0447012125",
            "DateEntered": datetime.now().strftime("%Y-%m-%d"),
            "DatePaid": None,
            "DueDate": "",
            "Model": None,
            "PriceLevel": 3,
            "TaxStatus": "Tax",
            "Occupied": False,
            "Voided": False,
            "TaxCode": None,
            "OverheadMarginBase": None,
            "TaxStatusLocked": False,
            "Map": None,
            "Zone": None,
            "Phase": None,
            "Tract": None,
            "Block": None,
            "Lot": None,
            "Unit": None,
            "Property": None,
            "PSMemberNumber": 0,
            "PSMemberName": None,
            "PSBusinessName": None,
            "TaxMethod": "",
            "TaxInclusive": False,
            "UserOrderType": 12,     # Changed from userOrderTypeId
            "ServiceType": 9,        # Changed from serviceTypeId
            "ContractType": 2,       # Changed from contractTypeId
            "Timeslot": 0,
            "InstallStore": 49,
            "AgeFrom": None,
            "Completed": None,
            "ReferralAmount": 0.0,
            "ReferralLocked": False,
            "PreAuthorization": None,
            "SalesTax": 0.0,
            "GrandInvoiceTotal": 0.0,
            "MaterialOnly": 0.0,
            "Labor": 0.0,
            "MiscCharges": 750.0,
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []
        },
        "products": None
    })

    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    print(f"Nested structure response status: {response.status_code}")
    print(f"Nested structure response: {response.text}")
    
    result = response.json()
    if result.get("status") == "success":
        print(f"✓ Order created successfully!")
        if isinstance(result.get("result"), dict):
            invoice_number = result["result"].get("invoiceNumber")
            print(f"Invoice Number: {invoice_number}")
        elif isinstance(result.get("result"), str):
            order_id = result.get('result')
            print(f"Order ID: {order_id}")
            
            # Try SaveOrder method as suggested
            save_result = save_order(base_url, session_token, order_id)
            if save_result:
                print(f"✓ SaveOrder method succeeded!")
            else:
                print(f"✗ SaveOrder method failed or not found")
        
        # Now retrieve the order to check if data was saved
        retrieve_order(base_url, session_token, po_number)
    else:
        print(f"✗ Order creation failed: {result.get('result', 'Unknown error')}")
        
    return result

def test_exact_working_structure(base_url, session_token, customer_id):
    """Test the EXACT working structure that created populated orders."""
    print(f"\n=== TESTING EXACT WORKING STRUCTURE ===")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"  # Default fallback
    supervisor_phone = "0447012125"    # Default fallback
    
    if pdf_data:
        # Extract supervisor info from PDF data
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    po_number = f"EXACT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # EXACT working payload structure that created populated orders
    payload = json.dumps({
        "category": "Order",  # CRITICAL - This was missing in failing tests
        "username": "zoran.vekic",
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": customer_id,
            "CustomerUpSeqNum": customer_id,
            "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "CustomerLastName": " ".join(supervisor_name.split()[1:]) if len(supervisor_name.split()) > 1 else "Peters",
            "CustomerAddress1": "123 Test Street",
            "CustomerAddress2": "",
            "CustomerCity": "Brisbane",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4000",
            "CustomerCounty": "",
            "Phone1": supervisor_phone,
            "ShipToFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "ShipToLastName": " ".join(supervisor_name.split()[1:]) if len(supervisor_name.split()) > 1 else "Peters",
            "ShipToAddress1": "123 Test Street",
            "ShipToAddress2": "",
            "ShipToCity": "Brisbane",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4000",
            "Phone2": supervisor_phone,
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "CustomNote": f"PDF Extracted - Supervisor: {supervisor_name}",
            "Note": f"TEST ORDER - Supervisor: {supervisor_name} - Phone: {supervisor_phone}",
            "WorkOrderNote": "",
            "PONum": po_number,  # Note: PONum not PONumber
            "JobNumber": f"{supervisor_name} {supervisor_phone}",
            "Date": datetime.now().strftime("%Y-%m-%d"),  # Note: Date not DateEntered
            "RequiredDate": estimated_delivery,
            "ShippedDate": None,
            "Terms": "",
            "DueDate": estimated_delivery,
            "FOB": "",
            "Reference": "",
            "Memo": "",
            "IsTaxable": True,
            "SalesTaxRate": 0.1,
            "SalesTax": 0.0,
            "Freight": 0.0,
            "Other": 0.0,
            "MiscCharges": 1000.0,
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []
        },
        "products": None
    })

    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    print(f"Exact working structure response status: {response.status_code}")
    print(f"Exact working structure response: {response.text}")
    
    result = response.json()
    if result.get("status") == "success":
        print(f"✓ Order created successfully with EXACT working structure!")
        order_id = result.get('result')
        if order_id:
            print(f"Order ID: {order_id}")
            
        # Now retrieve the order to check if data was saved
        retrieve_order(base_url, session_token, po_number)
    else:
        print(f"✗ Exact working structure failed: {result.get('result', 'Unknown error')}")
        
    return result

def test_customer_id_2_structure(base_url, session_token):
    """Test with customer ID 2 that appeared in successful log entries."""
    print(f"\n=== TESTING WITH CUSTOMER ID 2 (from successful logs) ===")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "JOHN"  # From successful log entry
    supervisor_phone = "0447012125"
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    po_number = f"CUST2-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Use customer ID 2 like successful orders, and mark as **VOID** like successful entries
    payload = json.dumps({
        "category": "Order",
        "username": "zoran.vekic",
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": 2,  # Use customer ID 2 like successful orders
            "CustomerUpSeqNum": 2,
            "CustomerFirstName": f"{supervisor_name}      **VOID**",  # Add **VOID** like successful entries
            "CustomerLastName": "TESTORDER",
            "CustomerAddress1": "123 Test Street",
            "CustomerAddress2": "",
            "CustomerCity": "Brisbane", 
            "CustomerState": "QLD",
            "CustomerPostalCode": "4000",
            "CustomerCounty": "",
            "Phone1": supervisor_phone,
            "ShipToFirstName": f"{supervisor_name}      **VOID**",
            "ShipToLastName": "TESTORDER",
            "ShipToAddress1": "123 Test Street",
            "ShipToAddress2": "",
            "ShipToCity": "Brisbane",
            "ShipToState": "QLD", 
            "ShipToPostalCode": "4000",
            "Phone2": supervisor_phone,
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": f"{supervisor_name.lower()}@example.com",
            "CustomNote": f"PDF Test - Supervisor: {supervisor_name}",
            "Note": f"CUST2 TEST - {supervisor_name} - {supervisor_phone}",
            "WorkOrderNote": "",
            "PONum": po_number,
            "JobNumber": f"{supervisor_name} {supervisor_phone}",
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "RequiredDate": estimated_delivery,
            "ShippedDate": None,
            "Terms": "",
            "DueDate": estimated_delivery,
            "FOB": "",
            "Reference": "",
            "Memo": "",
            "IsTaxable": True,
            "SalesTaxRate": 0.1,
            "SalesTax": 0.0,
            "Freight": 0.0,
            "Other": 0.0,
            "MiscCharges": 1000.0,
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []
        },
        "products": None
    })

    print(f"📤 Sending payload with CustomerSeqNum: 2")
    print(f"📤 CustomerFirstName: '{supervisor_name}      **VOID**'")
    print(f"📤 PO Number: {po_number}")

    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    print(f"Customer ID 2 response status: {response.status_code}")
    print(f"Customer ID 2 response: {response.text}")
    
    result = response.json()
    if result.get("status") == "success":
        print(f"✓ Order created successfully with Customer ID 2!")
        order_id = result.get('result')
        if order_id:
            print(f"Order ID: {order_id}")
            
        # Now retrieve the order to check if data was saved
        retrieve_order(base_url, session_token, po_number)
    else:
        print(f"✗ Customer ID 2 test failed: {result.get('result', 'Unknown error')}")
        
    return result

def test_store_1_structure(base_url, session_token, customer_id):
    """Test with Store: 1 instead of Store: 49 to see if store affects data persistence."""
    print(f"\n=== TESTING WITH STORE: 1 (instead of 49) ===")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"  # Default fallback
    supervisor_phone = "0447012125"    # Default fallback
    
    if pdf_data:
        # Extract supervisor info from PDF data
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    po_number = f"STORE1-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # EXACT working payload structure but with Store: 1
    payload = json.dumps({
        "category": "Order",
        "username": "zoran.vekic",
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": customer_id,
            "CustomerUpSeqNum": customer_id,
            "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "CustomerLastName": " ".join(supervisor_name.split()[1:]) if len(supervisor_name.split()) > 1 else "Peters",
            "CustomerAddress1": "123 Test Street",
            "CustomerAddress2": "",
            "CustomerCity": "Brisbane",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4000",
            "CustomerCounty": "",
            "Phone1": supervisor_phone,
            "ShipToFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "ShipToLastName": " ".join(supervisor_name.split()[1:]) if len(supervisor_name.split()) > 1 else "Peters",
            "ShipToAddress1": "123 Test Street",
            "ShipToAddress2": "",
            "ShipToCity": "Brisbane",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4000",
            "Phone2": supervisor_phone,
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 1,  # 🔑 KEY CHANGE: Store 1 instead of 49
            "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "CustomNote": f"PDF Extracted - Supervisor: {supervisor_name}",
            "Note": f"STORE1 TEST - Supervisor: {supervisor_name} - Phone: {supervisor_phone}",
            "WorkOrderNote": "",
            "PONum": po_number,
            "JobNumber": f"{supervisor_name} {supervisor_phone}",
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "RequiredDate": estimated_delivery,
            "ShippedDate": None,
            "Terms": "",
            "DueDate": estimated_delivery,
            "FOB": "",
            "Reference": "",
            "Memo": "",
            "IsTaxable": True,
            "SalesTaxRate": 0.1,
            "SalesTax": 0.0,
            "Freight": 0.0,
            "Other": 0.0,
            "MiscCharges": 1000.0,
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []
        },
        "products": None
    })

    print(f"🏪 KEY CHANGE: Using Store: 1 (instead of 49)")
    print(f"📦 PO Number: {po_number}")

    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    print(f"Store 1 response status: {response.status_code}")
    print(f"Store 1 response: {response.text}")
    
    result = response.json()
    if result.get("status") == "success":
        print(f"✓ Order created successfully with Store: 1!")
        order_id = result.get('result')
        if order_id:
            print(f"Order ID: {order_id}")
            
        # Now retrieve the order to check if data was saved
        retrieve_order(base_url, session_token, po_number)
    else:
        print(f"✗ Store 1 test failed: {result.get('result', 'Unknown error')}")
        
    return result

def test_working_flat_structure(base_url, session_token):
    """Test the EXACT working flat payload structure found in test_rfms_customer_job.py."""
    print(f"\n=== TESTING EXACT WORKING FLAT STRUCTURE ===")
    print("This is the structure that actually created orders with populated data!")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"  # Default fallback
    supervisor_phone = "0447012125"    # Default fallback
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    # Generate a unique PO number for this test
    po_number = f"FLAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"🎯 KEY DIFFERENCES in working structure:")
    print(f"   ✅ FLAT payload (not nested under 'order')")
    print(f"   ✅ Endpoint: /order/create (NOT /v2/order/create)")
    print(f"   ✅ Field names: privateNotes, publicNotes")
    print(f"   ✅ Request format: json=payload")
    print(f"   ✅ Updated IDs: userOrderTypeId=18, serviceTypeId=8, contractTypeId=1")
    
    # EXACT working payload structure from test_rfms_customer_job.py with updated IDs
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "adSource": 1,
        "quoteDate": None,
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "soldTo.customerId": "2",  # Use customer ID 2 like successful orders
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
        "userOrderTypeId": 18,  # 🔑 RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # 🔑 SUPPLY & INSTALL  
        "contractTypeId": 1,    # 🔑 30 DAY ACCOUNT
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

    print(f"📤 Sending to: {base_url}/order/create (FLAT STRUCTURE)")
    # Use exact same endpoint and format as working structure
    response = requests.post(
        f"{base_url}/order/create",  # NOT /v2/order/create!
        auth=(STORE_CODE, session_token),
        headers=headers,
        json=payload  # json=payload not data=json.dumps(payload)!
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    result = response.json() if response.status_code == 200 else {"status": "error", "result": response.text}
    if result.get("status") == "success":
        order_id = result.get('result')
        print(f"✅ SUCCESS! Flat structure order created: {order_id}")
        
        # Retrieve the order to check if data was saved
        retrieve_order(base_url, session_token, po_number)
    else:
        print(f"❌ Flat structure test failed: {result.get('result', 'Unknown error')}")
        
    return result

def test_exact_working_flat_with_pdf():
    """Test the EXACT working flat structure with PDF data and specified IDs."""
    print("🎯 TESTING EXACT WORKING FLAT STRUCTURE WITH PDF DATA")
    print("=" * 70)
    
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
    print(f"   🔗 Endpoint: {BASE_URL}/v2/order/create")  
    print(f"   📦 PO Number: {po_number}")
    print(f"   👤 Customer ID: 2 (from successful logs)")
    print(f"   📞 Supervisor: {supervisor_name} - {supervisor_phone}")
    print(f"   🎯 Using specified IDs: userOrderTypeId=18, serviceTypeId=8, contractTypeId=1")
    
    # EXACT working payload structure (FLAT, not nested) with specified IDs
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "adSource": 1,
        "quoteDate": None,
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "soldTo.customerId": "2",  # Use customer ID 2 like successful orders
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
        "userOrderTypeId": 18,  # 🔑 RESIDENTIAL INSURANCE 
        "serviceTypeId": 8,     # 🔑 SUPPLY & INSTALL
        "contractTypeId": 1,    # 🔑 30 DAY ACCOUNT
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

    # Use the v2 endpoint  
    print(f"📤 Sending request to: {BASE_URL}/v2/order/create")
    response = requests.post(
        f"{BASE_URL}/v2/order/create",  # Use v2 endpoint!
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
                            print(f"\n❌ Data still appears empty in API response")
                            print(f"📋 All available fields: {list(order_info.keys())}")
                            print(f"💡 Data might be saved but not visible via this API endpoint")
                            print(f"🔍 Check RFMS web interface to verify actual data persistence")
                            return False
                    else:
                        print(f"❌ Order not found in retrieval")
                        return False
                else:
                    print(f"❌ Retrieval failed: {retrieve_response.status_code} - {retrieve_response.text}")
                    return False
            else:
                print(f"❌ Order creation failed: {result}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def test_anti_weborder_flat_structure():
    """Test the exact structure to prevent weborders based on documentation."""
    print("🚫 TESTING ANTI-WEBORDER FLAT STRUCTURE")
    print("=" * 60)
    print("Based on RFMS docs: category: Order at top level prevents weborders")
    
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
    
    po_number = f"ANTI-WEB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Key: category: Order at TOP LEVEL (not nested)")
    print(f"🎯 Key: NO SaveOrder wrapper")
    print(f"🎯 Key: FLAT structure like working examples")
    
    # FLAT structure based on documentation requirements
    payload = {
        "category": "Order",  # 🔑 TOP LEVEL - prevents weborders per docs
        "username": "zoran.vekic",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "soldTo": {
            "customerId": 5,  # PROFILE BUILD GROUP
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "lastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "address2": "",
            "city": "MILTON", 
            "state": "QLD",
            "postalCode": "4064",
            "phone1": supervisor_phone,
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
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        "privateNotes": f"ANTI-WEBORDER TEST - Supervisor: {supervisor_name}",
        "publicNotes": f"PDF Extracted: {supervisor_name} - {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 12,    # SUPPLY & INSTALL
        "contractTypeId": 2,    # 30 DAY ACCOUNT
        "adSource": 1,
        "lines": [
            {
                "productId": "213322",
                "colorId": "2133",
                "quantity": 1000.0,
                "priceLevel": 10
            }
        ]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: FLAT with category at TOP LEVEL")
    
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
                print(f"✅ SUCCESS! Anti-weborder order created: {order_id}")
                print(f"🎯 This should NOT be a weborder!")
                print(f"🔍 Check RFMS interface to verify it's in regular orders")
                
                # Retrieve to check basic data
                retrieve_order(BASE_URL, session_token, po_number)
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

def test_profile_build_group_payload(base_url, session_token):
    """Test with PROFILE BUILD GROUP customer data using provided keyId's."""
    print(f"\n=== TESTING PROFILE BUILD GROUP PAYLOAD ===")
    print("Using customer data and keyId's provided by user")
    
    # Load PDF extraction data for supervisor info
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"  # Default fallback
    supervisor_phone = "0447012125"    # Default fallback
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    # Generate a unique PO number for this test
    po_number = f"PROFILE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = "2025-06-04"  # From provided data
    measure_date = "2025-05-25"  # 5 days from entered date
    
    print(f"📦 PO Number: {po_number}")
    print(f"🏢 Customer: PROFILE BUILD GROUP")
    print(f"📞 Customer Phone: 0418674500")
    print(f"🚚 Delivery Date: {estimated_delivery}")
    
    # Fixed payload using flat structure to avoid weborders  
    payload = {
        "category": "Order",
        "username": "zoran.vekic",
        "poNumber": f"FLAT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "soldTo": {
            "customerId": 5,
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "lastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "address2": "",
            "city": "MILTON", 
            "state": "QLD",
            "postalCode": "4064",
            "phone1": supervisor_phone,
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
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        "privateNotes": f"PDF Extracted - Supervisor: {supervisor_name}",
        "publicNotes": f"Order Template Test - {supervisor_name} - {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        "estimatedDeliveryDate": estimated_delivery,
        "enteredDate": datetime.now().strftime("%Y-%m-%d"),
        "measureDate": measure_date,
        "taxStatus": "Tax", 
        "taxMethod": "SalesTax",
        "adSourceId": 1,
        "isOccupied": False,
        "timeSlot": 0,
        "phase": "",
        "model": "",
        "unit": "", 
        "recycleFee": 0.0,
        "calculateFee": False,
        "block": "",
        "tract": "",
        "lot": "",
        "userOrderTypeId": 18,
        "serviceTypeId": 12,
        "contractTypeId": 2,
        "discount": 0.0,
        "lines": [
            {
                "id": "",
                "isUseTaxLine": False,
                "notes": f"PDF Supervisor: {supervisor_name}",
                "internalNotes": f"Contact: {supervisor_phone}",
                "productId": 213322,
                "colorId": 2133,
                "quantity": 1000.00,
                "serialNumber": "",
                "ecProductId": None,
                "ecColorId": None,
                "delete": False,
                "priceLevel": 10,
                "lineStatus": "none", 
                "lineGroupId": 4,
                "inTransit": False,
                "promiseDate": "",
                "installDate": (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d"),
                "shipTo": None,
                "attachments": [],
                "workOrderLines": [
                    {
                        "id": "",
                        "lineNumber": "1",
                        "areaName": "Test Area",
                        "quantity": "1000.00",
                        "rate": "195.50",
                        "notes": f"Supervisor: {supervisor_name}",
                        "delete": False
                    }
                ]
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    print(f"📤 Sending to: {base_url}/v2/order/create")
    print(f"🎯 Using keyId's: userOrderTypeId={payload['userOrderTypeId']}, serviceTypeId={payload['serviceTypeId']}, contractTypeId={payload['contractTypeId']}")
    
    # Use the v2 endpoint
    response = requests.post(
        f"{base_url}/v2/order/create",
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
                print(f"✅ SUCCESS! Profile Build Group order created: {order_id}")
                
                # Retrieve the order to check if data was saved
                retrieve_order(base_url, session_token, po_number)
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

def test_profile_build_group_main():
    """Main function to test Profile Build Group payload."""
    print("🏢 PROFILE BUILD GROUP ORDER TEST")
    print("=" * 50)
    print("Testing with provided customer data and keyId's")
    print("Customer: PROFILE BUILD GROUP")
    print("Using keyId's: userOrderTypeId=18, serviceTypeId=12, contractTypeId=2")
    
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return False
        
    success = test_profile_build_group_payload(BASE_URL, session_token)
    
    print(f"\n" + "=" * 50)
    print("🎯 FINAL RESULT:")
    if success:
        print("✅ SUCCESS! Profile Build Group order created successfully!")
        print("🏢 Customer data from provided keyId's was used")
        print("💡 Check RFMS web interface to verify complete data population")
    else:
        print("❌ Profile Build Group order creation failed")
        print("🔍 Check error messages above for troubleshooting")
        
    return success

def test_save_order_template(base_url, session_token):
    """Test with the original SaveOrder payload template + action SaveOrder method."""
    print(f"\n=== TESTING ORIGINAL SAVEORDER TEMPLATE + ACTION METHOD ===")
    print("Using original SaveOrder structure + action: SaveOrder")
    
    # Load PDF extraction data for supervisor info
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"  # Default fallback
    supervisor_phone = "0447012125"    # Default fallback
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    # Generate dates
    current_date = datetime.now().strftime("%Y-%m-%d")
    estimated_delivery = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    measure_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    install_date = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
    print(f"📦 Using original SaveOrder template + action method")
    print(f"🏢 Customer ID: 5 (PROFILE BUILD GROUP)")
    print(f"📞 Supervisor: {supervisor_name} - {supervisor_phone}")
    print(f"🚚 Delivery Date: {estimated_delivery}")
    
    # Original SaveOrder payload structure + action: SaveOrder method
    payload = {
        "username": "zoran.vekic",
        "action": "SaveOrder",  # ← KEY: This prevents weborders
        "SaveOrder": {
            "category": "Order",
            "soldTo": {
                "customerId": 5,
                "phone1": supervisor_phone,
                "phone2": "",
                "email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
                "customerType": "BUILDERS",
                "businessName": None,
                "LastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
                "FirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
                "Address1": "23 MAYNEVIEW STREET",
                "Address2": "",
                "city": "MILTON",
                "state": "QLD",
                "PostalCode": "4064",
                "county": "",
                "country": None
            },
            "shipTo": {
                "businessName": None,
                "lastName": "Customer",
                "firstName": "Site",
                "Address1": "1505 ROSEBANK WAY WEST",
                "Address2": "",
                "city": "HOPE ISLAND",
                "state": "QLD",
                "PostalCode": "4212",
                "county": "",
                "country": None
            },
            "salesperson1": "ZORAN VEKIC",
            "salesperson2": "",
            "salespersonSplitPercent": 1.0,
            "storeCode": "49",
            "storeNumber": 49,
            "CustomNote": f"PDF Extracted - Supervisor: {supervisor_name}",
            "Note": f"SaveOrder Template Test - {supervisor_name} - {supervisor_phone}",
            "WorkOrderNote": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
            "estimatedDeliveryDate": estimated_delivery,
            "enteredDate": current_date,
            "measureDate": measure_date,
            "taxStatus": "Tax",
            "taxMethod": "SalesTax",
            "adSourceId": 1,
            "isOccupied": False,
            "timeSlot": 0,
            "phase": "",
            "model": "",
            "unit": "",
            "recycleFee": 0.0,
            "calculateFee": False,
            "block": "",
            "tract": "",
            "lot": "",
            "userOrderTypeId": 18,
            "serviceTypeId": 12,
            "contractTypeId": 2,
            "discount": 0.0,
            "lines": [
                {
                    "id": "",
                    "isUseTaxLine": False,
                    "notes": f"PDF Supervisor: {supervisor_name}",
                    "internalNotes": f"Contact: {supervisor_phone}",
                    "productId": 213322,
                    "colorId": 2133,
                    "quantity": 1000.00,
                    "serialNumber": "",
                    "ecProductId": None,
                    "ecColorId": None,
                    "delete": False,
                    "priceLevel": 10,
                    "lineStatus": "none",
                    "lineGroupId": 4,
                    "inTransit": False,
                    "promiseDate": "",
                    "installDate": install_date,
                    "shipTo": None,
                    "attachments": [],
                    "workOrderLines": [
                        {
                            "id": "",
                            "lineNumber": "1",
                            "areaName": "Test Area",
                            "quantity": "1000.00",
                            "rate": "195.50",
                            "notes": f"Supervisor: {supervisor_name}",
                            "delete": False
                        }
                    ]
                }
            ]
        }
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    print(f"📤 Sending to: {base_url}/v2/order/create")
    print(f"🎯 Using action: SaveOrder + original SaveOrder structure")
    
    # Use the v2 endpoint
    response = requests.post(
        f"{base_url}/v2/order/create",
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
                print(f"✅ SUCCESS! SaveOrder + action method created order: {order_id}")
                print(f"🔍 Check RFMS for complete customer data population...")
                return True
            else:
                print(f"❌ SaveOrder + action failed: {result.get('result', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def test_save_order_main():
    """Main function to test the SaveOrder template."""
    print("📝 SAVEORDER TEMPLATE TEST")
    print("=" * 50)
    print("Testing with new order payload template")
    print("Structure: username + order wrapper")
    print("Category: Order")
    
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return False
        
    success = test_save_order_template(BASE_URL, session_token)
    
    print(f"\n" + "=" * 50)
    print("🎯 SAVEORDER TEMPLATE RESULT:")
    if success:
        print("✅ SUCCESS! Order template order created successfully!")
        print("📝 Used order wrapper structure with Order category")
        print("🎯 Template syntax errors were fixed and PDF data was mapped")
        print("💡 Check RFMS web interface to verify complete data population")
    else:
        print("❌ Order template order creation failed")
        print("🔍 Check error messages above for troubleshooting")
        
    return success

def test_saveorder_method(base_url, session_token):
    """Test using SaveOrder method as mentioned by someone."""
    print(f"\n=== TESTING SAVEORDER METHOD ===")
    print("Testing different SaveOrder method approaches")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"
    supervisor_phone = "0447012125"
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    po_number = f"SAVEORDER-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Approach 1: SaveOrder as action parameter
    print(f"\n🔹 Approach 1: SaveOrder as action parameter")
    payload1 = {
        "username": "zoran.vekic",
        "action": "SaveOrder",
        "category": "Order",
        "poNumber": po_number + "-A1",
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "CustomerSeqNum": 5,
        "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
        "CustomerLastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
        "CustomerAddress1": "23 MAYNEVIEW STREET",
        "CustomerCity": "MILTON",
        "CustomerState": "QLD",
        "CustomerPostalCode": "4064",
        "Phone1": supervisor_phone,
        "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
        "SalesPerson1": "ZORAN VEKIC",
        "Store": 49,
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,
        "serviceTypeId": 12,
        "contractTypeId": 2
    }
    
    # Approach 2: SaveOrder as wrapper object  
    print(f"\n🔹 Approach 2: SaveOrder as wrapper object")
    payload2 = {
        "username": "zoran.vekic",
        "SaveOrder": {
            "category": "Order",
            "poNumber": po_number + "-A2", 
            "jobNumber": f"{supervisor_name} {supervisor_phone}",
            "CustomerSeqNum": 5,
            "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "CustomerLastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
            "CustomerAddress1": "23 MAYNEVIEW STREET",
            "CustomerCity": "MILTON",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4064", 
            "Phone1": supervisor_phone,
            "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "SalesPerson1": "ZORAN VEKIC",
            "Store": 49,
            "estimatedDeliveryDate": estimated_delivery,
            "userOrderTypeId": 18,
            "serviceTypeId": 12,
            "contractTypeId": 2
        }
    }
    
    # Approach 3: SaveOrder as method parameter
    print(f"\n🔹 Approach 3: SaveOrder as method parameter")
    payload3 = {
        "username": "zoran.vekic",
        "method": "SaveOrder",
        "category": "Order",
        "poNumber": po_number + "-A3",
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "CustomerSeqNum": 5,
        "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
        "CustomerLastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
        "CustomerAddress1": "23 MAYNEVIEW STREET",
        "CustomerCity": "MILTON",
        "CustomerState": "QLD",
        "CustomerPostalCode": "4064",
        "Phone1": supervisor_phone,
        "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
        "SalesPerson1": "ZORAN VEKIC", 
        "Store": 49,
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,
        "serviceTypeId": 12,
        "contractTypeId": 2
    }
    
    # Test all approaches
    payloads = [
        ("Action Parameter", payload1),
        ("Wrapper Object", payload2), 
        ("Method Parameter", payload3)
    ]
    
    headers = {'Content-Type': 'application/json'}
    
    for approach_name, payload in payloads:
        print(f"\n🧪 Testing {approach_name} approach...")
        print(f"📤 Sending to: {base_url}/v2/order/create")
        
        response = requests.post(
            f"{base_url}/v2/order/create",
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
                    print(f"✅ SUCCESS! {approach_name} created order: {order_id}")
                    return True, approach_name
                else:
                    print(f"❌ {approach_name} failed: {result.get('result', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Error parsing response: {str(e)}")
        else:
            print(f"❌ API Error: {response.status_code}")
    
    return False, None

def test_saveorder_endpoint(base_url, session_token):
    """Test using SaveOrder as a specific endpoint."""
    print(f"\n=== TESTING SAVEORDER ENDPOINT ===")
    print("Testing SaveOrder as specific API endpoint")
    
    # Load PDF extraction data
    pdf_data = load_pdf_extraction_data()
    supervisor_name = "Jackson Peters"
    supervisor_phone = "0447012125"
    
    if pdf_data:
        job_details = pdf_data.get("job_details", {})
        supervisor_name = job_details.get("supervisor_name", supervisor_name)
        supervisor_phone = job_details.get("supervisor_phone", supervisor_phone) or job_details.get("supervisor_mobile", supervisor_phone)
        print(f"Using PDF extracted supervisor: {supervisor_name}, {supervisor_phone}")
    
    po_number = f"ENDPOINT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Test different SaveOrder endpoints
    endpoints = [
        f"{base_url}/SaveOrder",
        f"{base_url}/v2/SaveOrder", 
        f"{base_url}/v2/order/SaveOrder",
        f"{base_url}/api/SaveOrder"
    ]
    
    payload = {
        "username": "zoran.vekic",
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "CustomerSeqNum": 5,
        "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
        "CustomerLastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
        "CustomerAddress1": "23 MAYNEVIEW STREET", 
        "CustomerCity": "MILTON",
        "CustomerState": "QLD",
        "CustomerPostalCode": "4064",
        "Phone1": supervisor_phone,
        "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
        "SalesPerson1": "ZORAN VEKIC",
        "Store": 49,
        "estimatedDeliveryDate": estimated_delivery,
        "userOrderTypeId": 18,
        "serviceTypeId": 12,
        "contractTypeId": 2
    }
    
    headers = {'Content-Type': 'application/json'}
    
    for endpoint in endpoints:
        print(f"\n🧪 Testing endpoint: {endpoint}")
        
        try:
            response = requests.post(
                endpoint,
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
                        print(f"✅ SUCCESS! SaveOrder endpoint {endpoint} created order: {order_id}")
                        return True, endpoint
                    else:
                        print(f"❌ Endpoint failed: {result.get('result', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ Error parsing response: {str(e)}")
            elif response.status_code == 404:
                print(f"❌ Endpoint not found: {endpoint}")
            elif response.status_code == 405:
                print(f"❌ Method not allowed: {endpoint}")
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Connection error to {endpoint}: {str(e)}")
    
    return False, None

def test_hybrid_structure():
    """Test combining nested order structure (prevents weborders) with working field mapping."""
    print("🔀 TESTING HYBRID STRUCTURE")
    print("=" * 50)
    print("Combining: nested order structure + working field mapping")
    
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
    
    po_number = f"HYBRID-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: Nested order (prevents weborders) + proper field mapping")
    
    # Hybrid structure: nested order + working field mapping from successful examples
    payload = {
        "category": "Order",  # Prevents weborders per docs
        "username": "zoran.vekic", 
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,  # Explicit prevention
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": 5,  # PROFILE BUILD GROUP
            "CustomerUpSeqNum": 5,
            "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "CustomerLastName": supervisor_name.split()[-1] if supervisor_name else "Peters", 
            "CustomerAddress1": "23 MAYNEVIEW STREET",
            "CustomerAddress2": "",
            "CustomerCity": "MILTON",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4064",
            "CustomerCounty": "",
            "Phone1": supervisor_phone,
            "ShipToFirstName": "Site",
            "ShipToLastName": "Customer",
            "ShipToAddress1": "1505 ROSEBANK WAY WEST", 
            "ShipToAddress2": "",
            "ShipToCity": "HOPE ISLAND",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4212",
            "Phone2": supervisor_phone,
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "CustomNote": f"HYBRID TEST - PDF Supervisor: {supervisor_name}",
            "Note": f"Hybrid Structure Test - {supervisor_name} - {supervisor_phone}",
            "WorkOrderNote": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
            "PONum": po_number,  # Use PONum not poNumber
            "JobNumber": f"{supervisor_name} {supervisor_phone}",
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "RequiredDate": estimated_delivery, 
            "ShippedDate": None,
            "DueDate": estimated_delivery,
            "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
            "serviceTypeId": 12,    # SUPPLY & INSTALL  
            "contractTypeId": 2,    # 30 DAY ACCOUNT
            "adSource": 1,
            "PriceLevel": 3,
            "TaxStatus": "Tax",
            "Occupied": False,
            "Voided": False,
            "TaxStatusLocked": False,
            "TaxInclusive": False,
            "MiscCharges": 1000.0,
            "InvoiceTotal": 0.0,
            "Lines": [
                {
                    "productId": "213322",
                    "colorId": "2133",
                    "quantity": 1000.0,
                    "priceLevel": 10
                }
            ]
        },
        "products": None
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Nested order + comprehensive field mapping")
    
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
                print(f"✅ SUCCESS! Hybrid order created: {order_id}")
                print(f"🎯 Should be: Regular orders + populated fields!")
                print(f"🔍 Check RFMS to verify both weborder prevention AND data population")
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

def test_template_with_action_method():
    """Test the user's working template with our action SaveOrder method."""
    print("🎯 TESTING USER'S TEMPLATE + ACTION SAVEORDER METHOD")
    print("=" * 60)
    print("Combining working template structure + action method")
    
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
    
    po_number = f"TEMPLATE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: Working template + action SaveOrder method")
    
    # User's template structure with action SaveOrder method
    payload = {
        "username": "zoran.vekic",
        "action": "SaveOrder",  # Our working method
        "category": "Order",    # Required for non-weborders
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "userOrderTypeId": 18,
            "serviceTypeId": 8,
            "contractTypeId": 1,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": 5,  # PROFILE BUILD GROUP
            "CustomerUpSeqNum": 5,
            "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "CustomerLastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
            "CustomerAddress1": "23 MAYNEVIEW STREET",
            "CustomerAddress2": "",
            "CustomerCity": "MILTON",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4064",
            "CustomerCounty": "",
            "Phone1": supervisor_phone,
            "ShipToFirstName": "Site",
            "ShipToLastName": "Customer",
            "ShipToAddress1": "1505 ROSEBANK WAY WEST",
            "ShipToAddress2": "",
            "ShipToCity": "HOPE ISLAND",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4212",
            "Phone2": supervisor_phone,
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "CustomNote": f"TEMPLATE+ACTION - PDF Supervisor: {supervisor_name}",
            "Note": f"Template + Action Method Test - {supervisor_name} - {supervisor_phone}",
            "WorkOrderNote": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
            "PONum": po_number,
            "JobNumber": f"{supervisor_name} {supervisor_phone}",
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "RequiredDate": estimated_delivery,
            "ShippedDate": None,
            "Terms": "",
            "DueDate": estimated_delivery,
            "FOB": "",
            "Reference": "",
            "Memo": "",
            "IsTaxable": True,
            "SalesTaxRate": 0.1,
            "SalesTax": 0.0,
            "Freight": 0.0,
            "Other": 0.0,
            "MiscCharges": 1000.0,
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": [{
                "productId": "213322",
                "colorId": "2133",
                "quantity": 1000.0,
                "priceLevel": 10,
                "lineGroupId": 4
            }]
        },
        "products": None
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Working template + action SaveOrder")
    
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
                print(f"✅ SUCCESS! Template + Action order created: {order_id}")
                print(f"🎯 Should be: Regular orders + populated fields!")
                print(f"🔍 Check RFMS to verify BOTH weborder prevention AND data population")
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

def test_auto_populate_with_customer_id():
    """Test using soldTo.customerId to trigger automatic data population from RFMS."""
    print("🔄 TESTING AUTO-POPULATE WITH CUSTOMER ID")
    print("=" * 60)
    print("Using soldTo.customerId to trigger RFMS auto-population")
    
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
    
    po_number = f"AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: soldTo.customerId triggers RFMS auto-population")
    print(f"🔑 Key insight: Let RFMS fetch customer data automatically")
    
    # Flat structure with soldTo.customerId for auto-population
    payload = {
        "category": "Order",  # Prevents weborders
        "poNumber": po_number,
        "adSource": 1,
        "quoteDate": None,
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "soldTo.customerId": 5,  # PROFILE BUILD GROUP - let RFMS auto-populate
        "soldTo": {
            # Override specific fields with PDF data
            "phone1": supervisor_phone,
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
        "storeNumber": 49,
        "privateNotes": f"AUTO-POPULATE TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"RFMS Auto-populated customer + PDF data: {supervisor_name} - {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": None,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "lines": [
            {
                "productId": 213322,
                "colorId": 2133,
                "quantity": 1000.0,
                "priceLevel": "Price10"
            }
        ]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Flat with soldTo.customerId auto-population")
    
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
                print(f"✅ SUCCESS! Auto-populate order created: {order_id}")
                print(f"🎯 Should be: Regular orders + auto-populated customer data!")
                print(f"🔍 Check RFMS to verify BOTH weborder prevention AND data population")
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

def test_working_endpoint_structure():
    """Test using the exact working endpoint /order/create that was used in successful examples."""
    print("🎯 TESTING EXACT WORKING ENDPOINT")
    print("=" * 60)
    print("Using /order/create endpoint (not /v2/order/create)")
    
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
    
    po_number = f"WORKING-EP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: Use /order/create endpoint (that created populated orders)")
    print(f"🔑 Key difference: Different endpoint might handle data differently")
    
    # Use the EXACT structure from test_rfms_customer_job.py that worked
    test_data = {
        "sold_to": {
            "phone": supervisor_phone,
            "email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "address": {
                "address1": "23 MAYNEVIEW STREET",
                "address2": "",
                "city": "MILTON",
                "state": "QLD",
                "postalCode": "4064"
            }
        },
        "ship_to": {
            "phone": supervisor_phone,
            "email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "address": {
                "address1": "1505 ROSEBANK WAY WEST",
                "address2": "",
                "city": "HOPE ISLAND",
                "state": "QLD",
                "postalCode": "4212"
            }
        }
    }
    
    # EXACT payload structure from working examples
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "adSource": 1,
        "quoteDate": None,
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "soldTo.customerId": "5",  # PROFILE BUILD GROUP as string
        "soldTo": {
            "lastName": supervisor_name.split()[-1] if supervisor_name else "Peters",
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "address1": test_data["sold_to"]["address"]["address1"],
            "address2": test_data["sold_to"]["address"]["address2"],
            "city": test_data["sold_to"]["address"]["city"],
            "state": test_data["sold_to"]["address"]["state"],
            "postalCode": test_data["sold_to"]["address"]["postalCode"],
            "county": None,
            "Phone1": test_data["sold_to"]["phone"],
            "Phone2": test_data["ship_to"]["phone"],
            "Email": test_data["sold_to"]["email"]
        },
        "shipTo": {
            "lastName": "Customer",
            "firstName": "Site",
            "address1": test_data["ship_to"]["address"]["address1"],
            "address2": test_data["ship_to"]["address"]["address2"],
            "city": test_data["ship_to"]["address"]["city"],
            "state": test_data["ship_to"]["address"]["state"],
            "postalCode": test_data["ship_to"]["address"]["postalCode"],
            "county": None
        },
        "storeNumber": 49,
        "privateNotes": f"WORKING ENDPOINT TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"Endpoint Test: {supervisor_name} - {supervisor_phone}",
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": None,
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
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
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/order/create (NOT /v2/order/create)")
    print(f"🎯 Structure: Exact working structure from successful examples")
    
    response = requests.post(
        f"{BASE_URL}/order/create",  # 🔑 KEY: /order/create not /v2/order/create
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
                print(f"✅ SUCCESS! Working endpoint order created: {order_id}")
                print(f"🎯 Should be: Regular orders + populated customer data!")
                print(f"🔍 Check RFMS to verify BOTH weborder prevention AND data population")
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

def test_exact_az002766_with_current_data():
    """Test using the EXACT AZ002766 structure (100% successful) with current PDF data."""
    print("🎯 TESTING EXACT AZ002766 STRUCTURE WITH CURRENT DATA")
    print("=" * 70)
    print("Using the 100% successful AZ002766 structure with our PDF data")
    
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
    
    po_number = f"AZ002766-REPLICA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: EXACT AZ002766 structure with PDF data mapped")
    print(f"🔑 Key: Customer ID 2 + **VOID** pattern + NO type IDs")
    
    # EXACT AZ002766 payload structure with our PDF data
    payload = {
        "category": "Order",
        "username": "zoran.vekic",
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": 2,  # 🔑 KEY: Customer ID 2 like AZ002766
            "CustomerUpSeqNum": 2,
            "CustomerFirstName": f"{supervisor_name.split()[0] if supervisor_name else 'JACKSON'}           **VOID**",  # 🔑 KEY: **VOID** pattern
            "CustomerLastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "PETERS",
            "CustomerAddress1": "23 MAYNEVIEW STREET",
            "CustomerAddress2": "",
            "CustomerCity": "MILTON",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4064",
            "CustomerCounty": "",
            "Phone1": supervisor_phone,
            "ShipToFirstName": f"{supervisor_name.split()[0] if supervisor_name else 'JACKSON'}           **VOID**",  # Same pattern
            "ShipToLastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "PETERS",
            "ShipToAddress1": "1505 ROSEBANK WAY WEST",
            "ShipToAddress2": "",
            "ShipToCity": "HOPE ISLAND",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4212",
            "Phone2": supervisor_phone,
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "CustomNote": f"PDF Extracted - AZ002766 Replica with {supervisor_name}",
            "Note": f"EXACT AZ002766 STRUCTURE - PDF: {supervisor_name} - {supervisor_phone}",
            "WorkOrderNote": "",
            "PONum": po_number,  # Use PONum like AZ002766
            "JobNumber": f"{supervisor_name} {supervisor_phone}",
            "Date": current_date,  # Use Date not DateEntered like AZ002766
            "RequiredDate": estimated_delivery,
            "ShippedDate": None,
            "Terms": "",
            "DueDate": estimated_delivery,
            "FOB": "",
            "Reference": "",
            "Memo": "",
            "IsTaxable": True,
            "SalesTaxRate": 0.1,
            "SalesTax": 0.0,
            "Freight": 0.0,
            "Other": 0.0,
            "MiscCharges": 1000.0,
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []  # Empty lines like AZ002766
        },
        "products": None
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: EXACT AZ002766 replica with PDF data")
    print(f"🔑 CustomerFirstName: '{payload['order']['CustomerFirstName']}'")
    print(f"🔑 CustomerSeqNum: {payload['order']['CustomerSeqNum']}")
    
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
                print(f"✅ SUCCESS! AZ002766 replica order created: {order_id}")
                print(f"🎯 Should be: Regular orders + 100% populated fields like AZ002766!")
                print(f"🔍 Check RFMS to verify complete data population")
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

def test_saveorder_wrapper_without_action():
    """Test SaveOrder wrapper structure without action parameter to avoid weborders."""
    print("🔄 TESTING SAVEORDER WRAPPER WITHOUT ACTION")
    print("=" * 60)
    print("SaveOrder wrapper (populates fields) + nested structure (prevents weborders)")
    
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
    
    po_number = f"SAVEORDER-NO-ACTION-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: SaveOrder wrapper WITHOUT action parameter")
    print(f"🔑 Key: Use SaveOrder structure but avoid action that causes weborders")
    
    # SaveOrder wrapper structure WITHOUT action parameter
    payload = {
        "category": "Order",  # Prevents weborders
        "username": "zoran.vekic",
        "SaveOrder": {  # SaveOrder wrapper for field population
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": 5,  # PROFILE BUILD GROUP
            "CustomerUpSeqNum": 5,
            "CustomerFirstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "CustomerLastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "Peters",
            "CustomerAddress1": "23 MAYNEVIEW STREET",
            "CustomerAddress2": "",
            "CustomerCity": "MILTON",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4064",
            "CustomerCounty": "",
            "Phone1": supervisor_phone,
            "ShipToFirstName": "Site",
            "ShipToLastName": "Customer",
            "ShipToAddress1": "1505 ROSEBANK WAY WEST",
            "ShipToAddress2": "",
            "ShipToCity": "HOPE ISLAND",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4212",
            "Phone2": supervisor_phone,
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": f"{supervisor_name.lower().replace(' ', '.')}@example.com",
            "CustomNote": f"SAVEORDER WITHOUT ACTION - PDF: {supervisor_name}",
            "Note": f"SaveOrder Wrapper Test - {supervisor_name} - {supervisor_phone}",
            "WorkOrderNote": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
            "PONum": po_number,
            "JobNumber": f"{supervisor_name} {supervisor_phone}",
            "Date": current_date,
            "RequiredDate": estimated_delivery,
            "ShippedDate": None,
            "Terms": "",
            "DueDate": estimated_delivery,
            "FOB": "",
            "Reference": "",
            "Memo": "",
            "IsTaxable": True,
            "SalesTaxRate": 0.1,
            "SalesTax": 0.0,
            "Freight": 0.0,
            "Other": 0.0,
            "MiscCharges": 1000.0,
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []
        },
        "products": None
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: SaveOrder wrapper WITHOUT action parameter")
    print(f"🔑 Should combine: Field population + weborder prevention")
    
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
                print(f"✅ SUCCESS! SaveOrder without action order created: {order_id}")
                print(f"🎯 Should be: Regular orders + populated fields!")
                print(f"🔍 Check RFMS to verify BOTH weborder prevention AND data population")
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

def test_minimal_basic_structure():
    """Test with minimal basic structure - back to absolute basics."""
    print("🔙 TESTING MINIMAL BASIC STRUCTURE")
    print("=" * 60)
    print("Back to basics - minimal required fields only")
    
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
    
    po_number = f"MINIMAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: Absolute minimal structure")
    print(f"🔑 Theory: Maybe we're overcomplicating this")
    
    # Absolutely minimal structure - just the essentials
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC"
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Absolutely minimal - just category, PO, job, store, salesperson")
    
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
                print(f"✅ SUCCESS! Minimal order created: {order_id}")
                print(f"🔍 Check if even minimal fields are populated")
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

def test_minimal_plus_customer_fields():
    """Test minimal structure + essential customer fields that likely made AZ002842 work."""
    print("🔧 TESTING MINIMAL + CUSTOMER FIELDS")
    print("=" * 60)
    print("Minimal working structure + customer fields from successful examples")
    
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
    
    po_number = f"MIN-PLUS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: Minimal working + customer fields")
    print(f"🔑 Theory: Customer fields are what populate the order data")
    
    # Minimal structure + customer fields from successful examples
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        # Add customer fields that were in successful structures
        "soldTo": {
            "customerId": 5,  # PROFILE BUILD GROUP
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "lastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone": supervisor_phone,
            "email": f"{supervisor_name.lower().replace(' ', '.')}@example.com"
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
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Minimal working + soldTo/shipTo customer data")
    print(f"🔑 Customer ID: 5 (PROFILE BUILD GROUP)")
    
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
                print(f"✅ SUCCESS! Minimal + customer order created: {order_id}")
                print(f"🔍 Check if customer data is now populated")
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

def test_complete_field_mapping():
    """Test complete field mapping building on the successful customer structure."""
    print("🎯 TESTING COMPLETE FIELD MAPPING")
    print("=" * 60)
    print("Building on successful AZ002854 customer structure + missing fields")
    
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
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "lastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "address2": "",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone": supervisor_phone,  # 🔑 Add phone field
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
                print(f"🔍 Check if ALL fields are now populated:")
                print(f"   ✅ Customer details (inherited from AZ002854)")
                print(f"   🔍 Phone numbers (added)")
                print(f"   🔍 Install date (added)")
                print(f"   🔍 Note fields (added)")
                print(f"   🔍 Order/invoice type (added)")
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

def test_complete_field_mapping():
    """Test complete field mapping building on the successful customer structure."""
    print("🎯 TESTING COMPLETE FIELD MAPPING")
    print("=" * 60)
    print("Building on successful customer structure + missing fields")
    
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
    
    po_number = f"COMPLETE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    install_date = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
    
    print(f"📦 PO Number: {po_number}")
    print(f"🎯 Strategy: Successful customer structure + phone/date/note/type fields")
    print(f"🔑 Theory: Add the missing pieces to complete field population")
    
    # Complete structure with all missing fields added
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": f"{supervisor_name} {supervisor_phone}",
        "storeNumber": 49,
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        # Successful customer structure from AZ002854
        "soldTo": {
            "customerId": 5,  # PROFILE BUILD GROUP
            "firstName": supervisor_name.split()[0] if supervisor_name else "Jackson",
            "lastName": supervisor_name.split()[-1] if len(supervisor_name.split()) > 1 else "Peters",
            "address1": "23 MAYNEVIEW STREET",
            "address2": "",
            "city": "MILTON",
            "state": "QLD",
            "postalCode": "4064",
            "phone": supervisor_phone,  # Add phone here
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
        # Add missing fields that weren't in AZ002854
        "estimatedDeliveryDate": estimated_delivery,
        "privateNotes": f"COMPLETE TEST - PDF Supervisor: {supervisor_name}",
        "publicNotes": f"Complete Field Test: {supervisor_name} - {supervisor_phone}",
        "workOrderNotes": f"Contact: {supervisor_name} - Phone: {supervisor_phone}",
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "lines": [
            {
                "productId": 213322,
                "colorId": 2133,
                "quantity": 1000.0,
                "priceLevel": "Price10",
                "installDate": install_date,  # Add install date
                "notes": f"PDF Supervisor: {supervisor_name}"
            }
        ]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    print(f"📤 Sending to: {BASE_URL}/v2/order/create")
    print(f"🎯 Structure: Complete with phone, dates, notes, and type IDs")
    print(f"🔑 Building on successful customer structure from AZ002854")
    
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
                print(f"🔍 Check if ALL fields are now populated:")
                print(f"   ✅ Customer details (from AZ002854 success)")
                print(f"   🔍 Phone numbers")
                print(f"   🔍 Install date")
                print(f"   🔍 Note fields")
                print(f"   🔍 Order/invoice type")
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
                
                return True
            else:
                print(f"❌ Failed: {result.get('result', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {str(e)}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def main():
    """Main function to run the test."""
    print("🎯 RFMS ORDER CREATION TESTS")
    print("=" * 70)
    
    # Test the comprehensive lines structure first
    print("\n1️⃣ Testing comprehensive lines structure...")
    lines_success = test_comprehensive_lines()
    
    if lines_success:
        print("\n🎉 BREAKTHROUGH! Lines structure solved!")
        print("📋 We now have complete order creation capability!")
        print("✅ Customer fields + phone fields + lines fields = COMPLETE")
        return True
    
    print("\n2️⃣ Testing new order template...")
    saveorder_success = test_save_order_main()
    
    print("\n" + "=" * 70)
    print("\n3️⃣ Testing Profile Build Group payload with provided keyId's...")
    profile_success = test_profile_build_group_main()
    
    print("\n" + "=" * 70)
    print("\n4️⃣ Testing original working flat structure...")
    flat_success = test_exact_working_flat_with_pdf()
    
    print(f"\n" + "=" * 70)
    print("🎯 FINAL RESULTS:")
    print(f"📦 Comprehensive Lines Test: {'✅ SUCCESS' if lines_success else '❌ FAILED'}")
    print(f"📝 Order Template Test: {'✅ SUCCESS' if saveorder_success else '❌ FAILED'}")
    print(f"🏢 Profile Build Group Test: {'✅ SUCCESS' if profile_success else '❌ FAILED'}")
    print(f"📄 Working Flat Structure Test: {'✅ SUCCESS' if flat_success else '❌ FAILED'}")
    
    print("\n📋 Next step: Check the orders in RFMS web interface to confirm data persistence.")

if __name__ == "__main__":
    main() 
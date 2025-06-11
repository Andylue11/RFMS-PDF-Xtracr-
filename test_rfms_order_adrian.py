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
    """Create a test order."""
    print(f"\nCreating test order for customer ID: {customer_id}")
    
    # Generate a unique PO number for this test
    po_number = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Calculate estimated delivery date
    if commencement_date:
        estimated_delivery = commencement_date
    else:
        # Default to today + 5 days if no commencement date provided
        estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Test data for customer details - Adrian Simpson
    test_data = {
        "sold_to": {
            "phone": "0412345678",
            "email": "adrian.simpson@example.com",
            "address": {
                "address1": "42 WATCOMBE STREET",
                "address2": "",
                "city": "WAVELL HEIGHTS",
                "state": "QLD",
                "postalCode": "4012"
            }
        },
        "ship_to": {
            "phone": "0423456789",
            "email": "adrian.simpson@example.com",
            "address": {
                "address1": "42 WATCOMBE STREET",
                "address2": "",
                "city": "WAVELL HEIGHTS",
                "state": "QLD",
                "postalCode": "4012"
            }
        }
    }
    
    # Use the correct RFMS payload structure with discovered field values
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
            "CustomerFirstName": "Adrian",
            "CustomerLastName": "Simpson",
            "CustomerAddress1": test_data["sold_to"]["address"]["address1"],
            "CustomerAddress2": test_data["sold_to"]["address"]["address2"],
            "CustomerCity": test_data["sold_to"]["address"]["city"],
            "CustomerState": test_data["sold_to"]["address"]["state"],
            "CustomerPostalCode": test_data["sold_to"]["address"]["postalCode"],
            "CustomerCounty": "",
            "Phone1": test_data["sold_to"]["phone"],
            "ShipToFirstName": "Adrian",
            "ShipToLastName": "Simpson",
            "ShipToAddress1": test_data["ship_to"]["address"]["address1"],
            "ShipToAddress2": test_data["ship_to"]["address"]["address2"],
            "ShipToCity": test_data["ship_to"]["address"]["city"],
            "ShipToState": test_data["ship_to"]["address"]["state"],
            "ShipToPostalCode": test_data["ship_to"]["address"]["postalCode"],
            "Phone2": test_data["ship_to"]["phone"],
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": test_data["sold_to"]["email"],
            "CustomNote": f"Test order for Adrian Simpson - PO: {po_number}",
            "Note": "TEST - Adrian Simpson order for Wavell Heights",
            "WorkOrderNote": "",
            "PONum": po_number,
            "JobNumber": f"ZV-{po_number}",
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
            "MiscCharges": float(dollar_value),
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

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(
        f"{base_url}/v2/order/create",  # Using v2 endpoint
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    print(f"Order creation response status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.json()

def main():
    """Main function to run the test."""
    print("Starting RFMS Order Creation Test - Adrian Simpson")
    print("================================================")

    # Get session token
    print("\nGetting session token...")
    session_token = get_session_token()
    if not session_token:
        print("Failed to get session token. Exiting.")
        sys.exit(1)

    # Create test order with customer ID 2
    print("\nCreating test order for Adrian Simpson...")
    result = create_test_order(BASE_URL, session_token, 2, 1000.00)
    
    if result:
        print("\nTest completed successfully!")
        print(f"Customer: Adrian Simpson")
        print(f"Address: 42 Watcombe Street, Wavell Heights, QLD 4012")
        print(f"Customer ID: 2")
    else:
        print("\nTest failed!")

if __name__ == "__main__":
    main() 
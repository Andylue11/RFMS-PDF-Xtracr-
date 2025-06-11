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
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

def test_nested_structure(base_url, session_token, customer_id):
    """Test the nested structure that worked before (even if data was empty)."""
    print(f"\n=== TESTING NESTED STRUCTURE ===")
    
    po_number = f"NESTED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
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
            "userOrderTypeId": 18,
            "serviceTypeId": 8,
            "contractTypeId": 1,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": customer_id,
            "CustomerUpSeqNum": customer_id,
            "CustomerFirstName": "Test",
            "CustomerLastName": "User",
            "CustomerAddress1": "123 Test St",
            "CustomerAddress2": "",
            "CustomerCity": "Brisbane",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4000",
            "CustomerCounty": "",
            "Phone1": "0412345678",
            "ShipToFirstName": "Test",
            "ShipToLastName": "User",
            "ShipToAddress1": "123 Test St",
            "ShipToAddress2": "",
            "ShipToCity": "Brisbane",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4000",
            "Phone2": "0423456789",
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 49,
            "Email": "test@example.com",
            "CustomNote": f"Nested structure test - PO: {po_number}",
            "Note": "NESTED - Test with nested structure",
            "WorkOrderNote": "Jackson Peters - 0447012125",
            "PONum": po_number,
            "JobNumber": "Jackson Peters 0447012125",
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "RequiredDate": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "ShippedDate": None,
            "Terms": "",
            "DueDate": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "FOB": "",
            "Reference": "",
            "Memo": "",
            "IsTaxable": True,
            "SalesTaxRate": 0.1,
            "SalesTax": 0.0,
            "Freight": 0.0,
            "Other": 0.0,
            "MiscCharges": 500.0,
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
                "quantity": 1,
                "priceLevel": 10,
                "lineGroupId": 4
            }]
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
    return response.json()

def test_flat_structure(base_url, session_token, customer_id):
    """Test the flat structure from documentation."""
    print(f"\n=== TESTING FLAT STRUCTURE (Documentation) ===")
    
    po_number = f"FLAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    payload = json.dumps({
        "category": "Order",
        "poNumber": po_number,
        "jobNumber": "Jackson Peters 0447012125",
        "quoteDate": datetime.now().strftime("%Y-%m-%d"),
        "estimatedDeliveryDate": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        "soldTo": {
            "customerId": customer_id,
            "firstName": "Test",
            "lastName": "User",
            "address1": "123 Test St",
            "address2": "",
            "city": "Brisbane",
            "state": "QLD",
            "postalCode": "4000",
            "phone": "0412345678"
        },
        "shipTo": {
            "customerId": customer_id,
            "firstName": "Test",
            "lastName": "User",
            "address1": "123 Test St",
            "address2": "",
            "city": "Brisbane", 
            "state": "QLD",
            "postalCode": "4000",
            "phone": "0423456789"
        },
        "storeNumber": int(STORE_NUMBER),
        "privateNotes": "FLAT - Test with flat structure - Jackson Peters",
        "publicNotes": "FLAT - Test order with documentation structure",
        "workOrderNotes": "Jackson Peters - 0447012125",
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        "userOrderTypeId": 18,
        "serviceTypeId": 8,
        "contractTypeId": 1,
        "lines": [
            {
                "productId": 213322,  # Try without quotes
                "colorId": 2133,      # Try without quotes
                "quantity": 1,
                "priceLevel": 10
            }
        ]
    })

    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    print(f"Flat structure response status: {response.status_code}")
    print(f"Flat structure response: {response.text}")
    return response.json()

def main():
    """Main function to run comparison test."""
    print("RFMS API Structure Comparison Test")
    print("=" * 50)

    # Get session token
    print("\nGetting session token...")
    session_token = get_session_token()
    if not session_token:
        print("Failed to get session token. Exiting.")
        sys.exit(1)

    customer_id = 1747
    
    # Test nested structure first
    nested_result = test_nested_structure(BASE_URL, session_token, customer_id)
    
    # Test flat structure
    flat_result = test_flat_structure(BASE_URL, session_token, customer_id)
    
    print(f"\n" + "=" * 50)
    print("COMPARISON SUMMARY:")
    print(f"Nested structure: {nested_result.get('status', 'unknown')}")
    print(f"Flat structure: {flat_result.get('status', 'unknown')}")

if __name__ == "__main__":
    main() 
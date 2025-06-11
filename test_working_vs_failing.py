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

def test_working_payload(session_token):
    """Test the WORKING payload structure that created AZ002794."""
    print("🧪 Testing WORKING Payload Structure (created AZ002794)")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    po_number = f"WORK-{timestamp}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # WORKING payload - this successfully created AZ002794
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
            "CustomerSeqNum": 2,
            "CustomerUpSeqNum": 2,
            "CustomerFirstName": "WORKING",
            "CustomerLastName": "TESTUSER",
            "CustomerAddress1": "123 WORKING STREET",
            "CustomerAddress2": "",
            "CustomerCity": "WORKING CITY",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4000",
            "CustomerCounty": "",
            "Phone1": "0712345678",
            "ShipToFirstName": "WORKING",
            "ShipToLastName": "TESTUSER",
            "ShipToAddress1": "123 WORKING STREET",
            "ShipToAddress2": "",
            "ShipToCity": "WORKING CITY",
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
            "Email": "working.test@example.com",
            "CustomNote": f"Working payload test - PO: {po_number}",
            "Note": "TEST - Working structure order",
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
    
    print(f"📤 Endpoint: {BASE_URL}/v2/order/create")
    print(f"📦 PO Number: {po_number}")
    
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
                print(f"✅ WORKING Order Created: {order_number}")
                return order_number
            else:
                print(f"❌ WORKING payload failed: {result}")
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
    
    return None

def test_devb_fixed_payload(session_token):
    """Test DevB payload with corrections."""
    print("\n🧪 Testing DevB Flat with Corrections")
    print("=" * 60)
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    po_number = f"DEVB-FIX-{timestamp}"
    estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # DevB payload with potential fixes
    payload = json.dumps({
        "category": "Order",  # Add this key that works
        "username": "zoran.vekic",
        "order": {  # Nest under order like working version
            "createOrder": True,
            "poNumber": po_number,
            "adSource": 1,
            "quoteDate": None,
            "estimatedDeliveryDate": estimated_delivery,
            "jobNumber": f"ZV-{po_number}",
            "customerSource": "Customer",
            "CustomerSeqNum": 2,
            "customerUpSeqNum": 0,
            "CustomerFirstName": "DEVB",
            "CustomerLastName": "FIXED",
            "CustomerAddress1": "456 DEVB FIXED STREET",
            "CustomerAddress2": "LEVEL FIX",
            "CustomerCity": "FIXVILLE",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4001",
            "CustomerCounty": "",
            "Phone1": "0799999999",
            "customerPhone2": "0488888888",
            "Email": "devb.fixed@example.com",
            "ShipToFirstName": "DEVB",
            "ShipToLastName": "FIXED",
            "ShipToAddress1": "456 DEVB FIXED STREET",
            "ShipToAddress2": "LEVEL FIX",
            "ShipToCity": "FIXVILLE",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4001",
            "Phone2": "0488888888",
            "storeNumber": 49,
            "privateNotes": f"PRIVATE - DEVB FIXED TEST {timestamp}",
            "publicNotes": f"PUBLIC - DEVB FIXED PAYLOAD {timestamp}",
            "SalesPerson1": "ZORAN VEKIC",
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
            "Lines": [
                {
                    "productId": "213322",
                    "colorId": "2133",
                    "quantity": 1500.0,
                    "priceLevel": 10,
                    "lineGroupId": 4
                }
            ]
        },
        "products": None
    })
    
    print(f"📤 Endpoint: {BASE_URL}/v2/order/create")
    print(f"📦 PO Number: {po_number}")
    
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
                print(f"✅ DEVB FIXED Order Created: {order_number}")
                return order_number
            else:
                print(f"❌ DEVB FIXED payload failed: {result}")
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
    
    return None

def main():
    """Compare working vs failing payload structures."""
    print("🔍 WORKING vs FAILING PAYLOAD COMPARISON")
    print("=" * 60)
    print("Comparing successful payload structure with failing ones")
    
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return
    
    print("✅ Session token obtained")
    
    # Test 1: Known working payload
    working_order = test_working_payload(session_token)
    
    # Test 2: DevB with fixes
    devb_fixed_order = test_devb_fixed_payload(session_token)
    
    print("\n" + "=" * 60)
    print("📊 COMPARISON RESULTS")
    print("=" * 60)
    print(f"Working Payload:   {'✅ SUCCESS' if working_order else '❌ FAILED'}")
    print(f"DevB Fixed Payload: {'✅ SUCCESS' if devb_fixed_order else '❌ FAILED'}")
    
    if working_order:
        print(f"\n✅ Working order created: {working_order}")
    if devb_fixed_order:
        print(f"✅ DevB fixed order created: {devb_fixed_order}")

if __name__ == "__main__":
    main() 
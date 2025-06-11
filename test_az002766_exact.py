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

def test_exact_az002766_structure(base_url, session_token):
    """Test using the EXACT reconstructed payload structure from AZ002766."""
    print(f"\n=== TESTING EXACT AZ002766 RECONSTRUCTED PAYLOAD ===")
    
    po_number = f"AZ766-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    today = datetime.now().strftime("%Y-%m-%d")
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # EXACT reconstructed payload from AZ002766 analysis
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
            "CustomerSeqNum": 2,  # Same as AZ002766
            "CustomerUpSeqNum": 2,
            "CustomerFirstName": "JOHN           **VOID**",  # Exact spacing like AZ002766
            "CustomerLastName": "SMITH",
            "CustomerAddress1": "123 Test Street",
            "CustomerAddress2": "",
            "CustomerCity": "Brisbane",
            "CustomerState": "QLD",
            "CustomerPostalCode": "4000",
            "CustomerCounty": "",
            "Phone1": "0447012125",
            "ShipToFirstName": "JOHN           **VOID**",  # Exact spacing
            "ShipToLastName": "SMITH",
            "ShipToAddress1": "123 Test Street",
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
            "Email": "john.void@example.com",
            "CustomNote": "PDF Extracted - AZ002766 Reconstruction",
            "Note": "EXACT AZ002766 STRUCTURE TEST",
            "WorkOrderNote": "",
            "PONum": po_number,  # PONum not PONumber
            "JobNumber": "JOHN SMITH 0447012125",
            "Date": today,  # Date not DateEntered
            "RequiredDate": future_date,
            "ShippedDate": None,
            "Terms": "",
            "DueDate": future_date,
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

    print(f"🎯 Testing EXACT AZ002766 structure:")
    print(f"   CustomerSeqNum: 2")
    print(f"   CustomerFirstName: 'JOHN           **VOID**'")
    print(f"   CustomerLastName: 'SMITH'")
    print(f"   PONum: {po_number}")

    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{base_url}/v2/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    
    print(f"AZ002766 exact structure response status: {response.status_code}")
    print(f"AZ002766 exact structure response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success":
            order_id = result.get('result')
            print(f"✅ SUCCESS! Order created: {order_id}")
            print(f"🎯 This should have the SAME data persistence as AZ002766!")
            
            # Retrieve to check data
            print(f"\n🔍 Retrieving order to check data persistence...")
            retrieve_response = requests.post(
                f"{base_url}/v2/order/find",
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
                        
                    print(f"📊 RETRIEVAL RESULTS:")
                    print(f"   Order Number: {order_info.get('invoiceNumber', 'N/A')}")
                    print(f"   Customer: {order_info.get('customerFirstName', 'N/A')} {order_info.get('customerLastName', 'N/A')}")
                    print(f"   Phone: {order_info.get('phone1', 'N/A')}")
                    print(f"   Job Number: {order_info.get('jobNumber', 'N/A')}")
                    print(f"   Notes: {order_info.get('note', 'N/A')}")
                    print(f"   Salesperson: {order_info.get('salesPerson1', 'N/A')}")
                    
                    # Check if data is populated
                    if (order_info.get('customerFirstName', 'N/A') != 'N/A' and 
                        order_info.get('customerFirstName', 'N/A') != ''):
                        print(f"🎉 SUCCESS! Data is populated like AZ002766!")
                        return True
                    else:
                        print(f"❌ Data still empty despite exact structure match")
                        return False
                else:
                    print(f"❌ Order not found in retrieval")
                    return False
            else:
                print(f"❌ Retrieval failed: {retrieve_response.status_code}")
                return False
        else:
            print(f"❌ Order creation failed: {result}")
            return False
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")
        return False

def main():
    """Test the exact AZ002766 payload structure."""
    print("🔬 AZ002766 EXACT PAYLOAD RECONSTRUCTION TEST")
    print("=" * 60)
    print("Testing the exact payload structure that created AZ002766")
    print("(the order that successfully had populated data)")
    
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return
    
    success = test_exact_az002766_structure(BASE_URL, session_token)
    
    print(f"\n" + "=" * 60)
    print("🎯 FINAL RESULT:")
    if success:
        print("✅ SUCCESS! The exact AZ002766 structure worked!")
        print("🎉 Data was populated correctly!")
    else:
        print("❌ Even the exact AZ002766 structure didn't populate data")
        print("🔍 This suggests the issue is beyond payload structure")

if __name__ == "__main__":
    main() 
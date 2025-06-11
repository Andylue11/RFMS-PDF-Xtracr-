import os
import json
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

def lookup_order_by_invoice_number(session_token, invoice_number):
    """Try to find an order by invoice number directly."""
    print(f"\nLooking up order by invoice number: {invoice_number}")
    
    # Try different possible payload structures
    payload_options = [
        {"invoiceNumber": invoice_number},
        {"id": invoice_number},
        {"orderNumber": invoice_number}
    ]
    
    for i, payload in enumerate(payload_options):
        print(f"\nAttempt {i+1}: {payload}")
        
        response = requests.post(
            f"{BASE_URL}/v2/order/find",
            auth=(STORE_CODE, session_token),
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                print("✓ Order found!")
                return data
            
    return None

def test_known_orders():
    """Test lookup of orders we know were created."""
    print("RFMS Order Lookup Test")
    print("=" * 40)
    
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("Failed to get session token")
        return
    
    # Known order numbers from our previous tests
    known_orders = ["AZ002792", "AZ002793", "AZ002794", "AZ002797", "AZ002798", "AZ002800", "AZ002801", "AZ002802", "AZ002803"]
    
    for order_id in known_orders:
        result = lookup_order_by_invoice_number(session_token, order_id)
        if result:
            print(f"SUCCESS: Found data for {order_id}")
            break
        else:
            print(f"No data found for {order_id}")
    
    # Also try looking up by some test PO numbers we might have used
    test_po_numbers = ["TEST-20250609021345", "TEST-20250609021634", "NESTED-20250609022826"]
    
    print(f"\n" + "=" * 40)
    print("Testing PO number lookups:")
    
    for po_number in test_po_numbers:
        print(f"\nLooking up PO: {po_number}")
        
        response = requests.post(
            f"{BASE_URL}/v2/order/find",
            auth=(STORE_CODE, session_token),
            headers={'Content-Type': 'application/json'},
            data=json.dumps({"poNumber": po_number})
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Response: {response.text}")

if __name__ == "__main__":
    test_known_orders() 
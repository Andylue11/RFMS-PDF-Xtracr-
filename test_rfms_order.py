import os
import sys
import json
from datetime import datetime
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

def create_test_order(session_token):
    """Create a test order with specific customer IDs."""
    if not session_token:
        print("No session token available")
        return None

    # Prepare the test order payload
    test_order_payload = {
        "username": "zoran.vekic",
        "order": {
            "CustomerSeqNum": 2,  # Sold-to customer ID
            "CustomerUpSeqNum": 2,  # Same as CustomerSeqNum
            "ShipToSeqNum": 1747,  # Ship-to customer ID
            "ShipToUpSeqNum": 1747,  # Same as ShipToSeqNum
            "PONumber": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",  # Generate unique PO number
            "WorkOrderNote": "Test order with specific customer IDs",
            "CustomerType": "INSURANCE",
            "UserOrderType": 12,
            "ServiceType": 9,
            "ContractType": 2,
            "SalesPerson1": "ZORAN VEKIC",
            "Store": 49,
            "InstallStore": 49,
            "OrderDate": datetime.now().strftime("%Y-%m-%d"),
            "DateEntered": datetime.now().strftime("%Y-%m-%d"),
            "GrandInvoiceTotal": 1000.00,  # Test amount
            "MaterialOnly": 0.0,
            "Labor": 0.0,
            "MiscCharges": 1000.00,  # Same as GrandInvoiceTotal
            "Balance": 1000.00  # Same as GrandInvoiceTotal
        }
    }

    try:
        # Make the request to create the order
        response = requests.post(
            f"{BASE_URL}/v2/Order",
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            auth=(STORE_CODE, session_token),
            json=test_order_payload
        )

        if response.status_code == 200:
            result = response.json()
            print("\nOrder created successfully!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"\nFailed to create order. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"\nError creating order: {str(e)}")
        return None

def main():
    """Main function to run the test."""
    print("Starting RFMS Order Creation Test")
    print("--------------------------------")

    # Get session token
    print("\nGetting session token...")
    session_token = get_session_token()
    if not session_token:
        print("Failed to get session token. Exiting.")
        sys.exit(1)

    # Create test order
    print("\nCreating test order...")
    result = create_test_order(session_token)
    
    if result:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")

if __name__ == "__main__":
    main() 
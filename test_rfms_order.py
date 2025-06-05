import os
import sys
import json
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
import base64

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

def find_customer_by_id(base_url, session_token, customer_id):
    """Find customer data by ID."""
    try:
        url = f"{base_url}/v2/customer/{customer_id}"
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, auth=(STORE_CODE, session_token))
        print(f"Customer search response status: {response.status_code}")
        
        if response.status_code == 200:
            customer_data = response.json()
            print(f"Found customer: {customer_data.get('name', 'Unknown')}")
            return customer_data
        else:
            print(f"Failed to find customer. Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error finding customer: {str(e)}")
        return None

def create_test_order(base_url, session_token, customer_id, dollar_value, commencement_date=None):
    """Create a test order."""
    print(f"\nCreating test order for customer ID: {customer_id}")
    
    # Get customer data
    customer_data = find_customer_by_id(base_url, session_token, customer_id)
    if not customer_data:
        print("Failed to get customer data. Exiting.")
        return None
    
    # Generate a unique PO number for this test
    po_number = "1840019-77667"  # Using the One Solutions PO number
    
    # Calculate estimated delivery date
    if commencement_date:
        estimated_delivery = commencement_date
    else:
        # Default to today + 5 days if no commencement date provided
        estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Test data for customer details from One Solutions PDF
    test_data = {
        "sold_to": {
            "phone": "07 3569 3874",  # From PDF
            "email": "admin@onesol.com.au",  # From PDF
            "address": {
                "address1": "1234 MAIN ST",  # Example address
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332"
            }
        },
        "ship_to": {
            "phone": "0466130001",  # From PDF
            "email": "admin@onesol.com.au",  # From PDF
            "address": {
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "CAPALABA",
                "state": "QLD",
                "postalCode": "4157"
            }
        }
    }
    
    payload = json.dumps({
        "category": "Order",
        "poNumber": "1840019-77667",
        "adSource": 1,
        "quoteDate": "",
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": "987ZEF",
        "soldTo.customerId": str(customer_id),
        "soldTo": {
            "lastName": customer_data.get('lastName', 'DOE'),
            "firstName": customer_data.get('firstName', 'JOHN'),
            "address1": customer_data.get('address1', test_data["sold_to"]["address"]["address1"]),
            "address2": customer_data.get('address2', test_data["sold_to"]["address"]["address2"]),
            "city": customer_data.get('city', test_data["sold_to"]["address"]["city"]),
            "state": customer_data.get('state', test_data["sold_to"]["address"]["state"]),
            "postalCode": customer_data.get('postalCode', test_data["sold_to"]["address"]["postalCode"]),
            "Phone1": customer_data.get('phone1', test_data["sold_to"]["phone"]),
            "Phone2": customer_data.get('phone2', test_data["ship_to"]["phone"]),
            "Email": customer_data.get('email', test_data["sold_to"]["email"])
        },
        "shipTo": {
            "lastName": "Adrian",
            "firstName": "Simpson",
            "address1": test_data["ship_to"]["address"]["address1"],
            "address2": test_data["ship_to"]["address"]["address2"],
            "city": test_data["ship_to"]["address"]["city"],
            "state": test_data["ship_to"]["address"]["state"],
            "postalCode": test_data["ship_to"]["address"]["postalCode"]
        },
        "storeNumber": 49,
        "privateNotes": "PRIVATE",
        "publicNotes": "PUBLIC",
        "salesperson1": "Zoran Vekic",
        "UserOrderType": 12,
        "ServiceType": 9,
        "ContractType": 2,
        "PriceLevel": 5,
        "TaxStatus": "Tax",
        "Occupied": False,
        "Voided": False,
        "TaxStatusLocked": False,
        "TaxInclusive": False,
        "lines": [
            {
                "productId": 213322,
                "colorId": 2133,
                "quantity": float(dollar_value),
                "priceLevel": 10,
                "lineGroupId": 4
            }
        ]
    })

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(
        f"{base_url}/v2/order/create",
        headers=headers,
        auth=(STORE_CODE, session_token),
        data=payload
    )
    print(f"Order creation response status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.json()

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

    # Create test order with One Solutions data
    print("\nCreating test order...")
    result = create_test_order(BASE_URL, session_token, 1499, 13630.00)  # Using the dollar value from the PDF
    
    if result:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")

if __name__ == "__main__":
    main() 
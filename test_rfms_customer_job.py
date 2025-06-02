import requests
import json
from datetime import datetime, timedelta

# RFMS API Configuration
STORE_CODE = "store-5291f4e3dca04334afede9f642ec6157"
API_KEY = "49bf22ea017f4b97aabc99def43c0b66"
BASE_URL = "https://api.rfms.online/v2"

def get_session_token():
    """Get session token from RFMS API."""
    print("Getting session token...")
    url = f"{BASE_URL}/Session/Begin"
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, auth=(STORE_CODE, API_KEY), headers=headers)
    print(f"Session response: {response.json()}")
    return response.json().get('sessionToken')

def create_job(base_url, session_token, customer_id, dollar_value, commencement_date=None):
    """Create a test job."""
    print(f"\nCreating test job for customer ID: {customer_id}")
    
    # Generate a unique PO number for this test
    po_number = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Calculate estimated delivery date
    if commencement_date:
        estimated_delivery = commencement_date
    else:
        # Default to today + 5 days if no commencement date provided
        estimated_delivery = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    
    # Test data for customer details
    test_data = {
        "sold_to": {
            "phone": "0412345678",
            "email": "john.smith@example.com",
            "address": {
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "CAPALABA",
                "state": "QLD",
                "postalCode": "4157"
            }
        },
        "ship_to": {
            "phone": "0423456789",
            "email": "ship.to@example.com",
            "address": {
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "CAPALABA",
                "state": "QLD",
                "postalCode": "4157"
            }
        }
    }
    
    payload = {
        "category": "Order",
        "poNumber": po_number,
        "adSource": 1,
        "quoteDate": None,
        "estimatedDeliveryDate": estimated_delivery,
        "jobNumber": f"ZV-{po_number}",
        "soldTo.customerId": customer_id,
        "soldTo": {
            "lastName": "Smith",
            "firstName": "John",
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
            "lastName": "Smith",
            "firstName": "John",
            "address1": test_data["ship_to"]["address"]["address1"],
            "address2": test_data["ship_to"]["address"]["address2"],
            "city": test_data["ship_to"]["address"]["city"],
            "state": test_data["ship_to"]["address"]["state"],
            "postalCode": test_data["ship_to"]["address"]["postalCode"],
            "county": None
        },
        "storeNumber": 49,
        "privateNotes": "PRIVATE - Test job with complete customer details",
        "publicNotes": "PUBLIC - This is a test job with dummy data",
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": None,
        "UserOrderType": 12,
        "ServiceType": 9,
        "ContractType": 2,
        "PriceLevel": 3,
        "TaxStatus": "Tax",
        "Occupied": False,
        "Voided": False,
        "TaxStatusLocked": False,
        "TaxInclusive": False,
        "lines": [
            {
                "productId": "00001",
                "colorId": 000,
                "quantity": float(dollar_value),
                "priceLevel": "Price10",
                "lineGroupId": 1
            }
        ]
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(
        f"{base_url}/order/create",
        auth=(STORE_CODE, session_token),
        headers=headers,
        json=payload
    )
    print(f"Job creation response status: {response.status_code}")
    print(f"Response: {response.text}")
    return response.json()

def main():
    # Get session token
    session_token = get_session_token()
    if not session_token:
        print("Failed to get session token")
        return

    # Test parameters
    customer_id = "5"  # Test customer ID
    dollar_value = "1000.00"  # Test dollar value
    
    # Create test job
    result = create_job(BASE_URL, session_token, customer_id, dollar_value)
    print("\nResult:", json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 
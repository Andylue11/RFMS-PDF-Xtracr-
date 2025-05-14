import requests
import logging
import base64
import json
from datetime import datetime
import urllib.parse
import time
import sys
from pprint import pprint

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://api.rfms.online"

# Credentials for Session Authentication
USERNAME = "store-5291f4e3dca04334afede9f642ec6157"
PASSWORD = "58ddae189c21473bb9064628b1c85161"

# Custom headers for authentication and content type
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def get_session_token(base_url):
    """Get session token for authentication."""
    print("Getting session token...")
    
    # Use Basic Auth with the provided credentials
    auth = (USERNAME, PASSWORD)
    
    try:
        response = requests.post(
            f"{base_url}/v2/Session/Begin",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            result = response.json()
            session_token = result.get('sessionToken')
            print(f"Session token obtained: {session_token}")
            print(f"Session expires: {result.get('sessionExpires')}")
            return session_token
        else:
            print(f"Failed to get session token. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

def find_customers(base_url, session_token, search_term):
    """Find customers by search term."""
    print(f"\nSearching for customers with term: {search_term}")
    
    # Use Username and session token for subsequent requests
    session_auth = (USERNAME, session_token)
    
    payload = {
        "searchText": search_term,
        "includeCustomers": True,
        "includeProspects": False,
        "includeInactive": False,
        "startIndex": 0
    }
    
    try:
        response = requests.post(
            f"{base_url}/v2/customers/find",
            headers=headers,
            auth=session_auth,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                customers = result.get("result", [])
                print(f"Found {len(customers)} customers")
                return customers
            else:
                print("No customers found in response")
                print(f"Response: {result}")
                return []
        else:
            print(f"Failed to search customers. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []
    except Exception as e:
        print(f"Error searching customers: {str(e)}")
        return []

def create_job(base_url, session_token, customer_id):
    """Create a test job."""
    print(f"\nCreating test job for customer ID: {customer_id}")
    
    # Use Username and session token for subsequent requests
    session_auth = (USERNAME, session_token)
    
    # Generate a unique PO number for this test
    po_number = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    dollar_value = 1234.56
    
    payload = {
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
            "IsWebOrder": True,
            "Exported": False,
            "CanEdit": False,
            "LockTaxes": False,
            "CustomerSource": "",
            "CustomerSeqNum": customer_id,
            "CustomerUpSeqNum": customer_id,
            "CustomerFirstName": "",
            "CustomerLastName": "",
            "CustomerAddress1": "",
            "CustomerAddress2": "",
            "CustomerCity": "",
            "CustomerState": "",
            "CustomerPostalCode": "",
            "CustomerCounty": "",
            "Phone1": "",
            "ShipToFirstName": "",
            "ShipToLastName": "",
            "ShipToAddress1": "",
            "ShipToAddress2": "",
            "ShipToCity": "",
            "ShipToState": "",
            "ShipToPostalCode": "",
            "ShipToCounty": "",
            "Phone2": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 1,
            "Email": "",
            "CustomNote": "",
            "Note": "",
            "WorkOrderNote": "Test job created by RFMS-PDF-Xtracr",
            "PickingTicketNote": None,
            "OrderDate": datetime.now().strftime("%Y-%m-%d"),
            "MeasureDate": "",
            "PromiseDate": "",
            "PONumber": po_number,
            "CustomerType": "INSURANCE",
            "JobNumber": "",
            "DateEntered": datetime.now().strftime("%Y-%m-%d"),
            "DatePaid": None,
            "DueDate": "",
            "Model": None,
            "PriceLevel": 0,
            "TaxStatus": "Tax",
            "Occupied": False,
            "Voided": False,
            "AdSource": 0,
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
            "UserOrderType": 3,
            "ServiceType": 1,
            "ContractType": 1,
            "Timeslot": 0,
            "InstallStore": 1,
            "AgeFrom": None,
            "Completed": None,
            "ReferralAmount": 0.0,
            "ReferralLocked": False,
            "PreAuthorization": None,
            "SalesTax": 0.0,
            "GrandInvoiceTotal": dollar_value,
            "MaterialOnly": 0.0,
            "Labor": 0.0,
            "MiscCharges": dollar_value,
            "InvoiceTotal": dollar_value,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": dollar_value,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": [
                {
                    "productId": "PO#$$",
                    "colorId": "PO#$$",
                    "quantity": dollar_value,
                    "priceLevel": "Price4"
                }
            ]
        },
        "products": None
    }
    
    try:
        response = requests.post(
            f"{base_url}/v2/Order",
            headers=headers,
            auth=session_auth,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                job_id = result.get("result", {}).get("id")
                print(f"Job created with ID: {job_id}")
                return result
            else:
                print("No job created in response")
                pprint(result)
                return None
        else:
            print(f"Failed to create job. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error creating job: {str(e)}")
        return None

if __name__ == "__main__":
    base_url = BASE_URL
    
    print("========================================")
    print("RFMS Customer Search and Job Creation Test")
    print(f"Base URL: {base_url}")
    print(f"Username: {USERNAME}")
    print("========================================")
    
    # Get session token
    session_token = get_session_token(base_url)
    
    if not session_token:
        print("Failed to get session token. Exiting.")
        sys.exit(1)
    
    # Search for customers
    search_term = input("Enter customer search term (e.g. Smith): ").strip()
    if not search_term:
        search_term = "Smith"
        print(f"Using default search term: {search_term}")
    
    customers = find_customers(base_url, session_token, search_term)
    
    if not customers:
        print("No customers found. Exiting.")
        sys.exit(1)
        
    # Display found customers
    print("\nFound the following customers:")
    for i, customer in enumerate(customers):
        print(f"{i+1}. {customer.get('customerName', 'Unknown')} - ID: {customer.get('customerSourceId', 'Unknown')}")
    
    # Select a customer for job creation
    selection = input("\nEnter the number of the customer to create a job for, or 'q' to quit: ").strip()
    if selection.lower() == 'q':
        print("Exiting.")
        sys.exit(0)
    
    try:
        index = int(selection) - 1
        if index < 0 or index >= len(customers):
            print("Invalid selection. Exiting.")
            sys.exit(1)
            
        selected_customer = customers[index]
        customer_id = selected_customer.get('customerSourceId')
        
        if not customer_id:
            print("Selected customer has no ID. Exiting.")
            sys.exit(1)
            
        # Create job for selected customer
        job_result = create_job(base_url, session_token, customer_id)
        
        if job_result:
            print("\nJob created successfully!")
        else:
            print("\nFailed to create job.")
    except ValueError:
        print("Invalid selection. Exiting.")
        sys.exit(1)
    
    print("\nTest completed!") 
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

# New credentials
USERNAME = "emily@atozflooring.com"
PASSWORD = "5Hstg9gWmnEg"
STORE = "store-5291f4e3dca04334afede9f642ec6157"
API_KEY = "427e18d70fe142ea825bcba37be113c1"

# Custom headers for authentication and content type
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Test functions
def test_session_auth(base_url):
    """Test authentication with session token."""
    print("\nTesting Session Token Authentication...")
    
    # Step 1: Get session token
    auth = (STORE, API_KEY)
    
    try:
        # Make request to begin session
        response = requests.post(
            f"{base_url}/v2/Session/Begin",
            headers=headers,
            auth=auth
        )
        
        print(f"Session Begin Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Session token obtained")
            print(f"Session Token: {result.get('sessionToken')}")
            print(f"Session Expires: {result.get('sessionExpires')}")
            
            # Step 2: Use session token for subsequent request
            session_token = result.get('sessionToken')
            if not session_token:
                print("FAILED: No session token in response")
                return False
                
            # Create auth tuple with store as username and session token as password
            session_auth = (STORE, session_token)
            
            # Try a simple request with session token
            test_response = requests.get(
                f"{base_url}/v2/submessage/store/{STORE}/messages",
                headers=headers,
                auth=session_auth
            )
            
            print(f"Test request with session token status: {test_response.status_code}")
            if test_response.status_code == 200:
                print("SUCCESS: Authentication with session token is working")
                return True
            else:
                print(f"FAILED: Authentication with session token - {test_response.text}")
                return False
        else:
            print(f"FAILED: Session token request - {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_basic_auth(base_url):
    """Test basic authentication with username/password."""
    print("\nTesting Basic Authentication...")
    
    # Method 1: Basic Auth with username/password
    auth_headers = headers.copy()
    
    # Add basic auth header
    auth_headers['Authorization'] = 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    
    try:
        # Test endpoint requiring authentication
        response = requests.get(
            f"{base_url}/rfapi/v2/submessage/store/{STORE}/messages",
            headers=auth_headers
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Basic Authentication is working")
            return True
        else:
            print(f"FAILED: Basic Authentication - {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_api_key_auth(base_url):
    """Test API key authentication."""
    print("\nTesting API Key Authentication...")
    
    auth_headers = headers.copy()
    
    # Add API key header
    auth_headers['X-API-Key'] = API_KEY
    
    try:
        # Test endpoint requiring authentication
        response = requests.get(
            f"{base_url}/rfapi/v2/submessage/store/{STORE}/messages",
            headers=auth_headers
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: API Key Authentication is working")
            return True
        else:
            print(f"FAILED: API Key Authentication - {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def test_customer_search(base_url, search_term):
    """Test searching for customers."""
    print(f"\nSearching Customers for: '{search_term}'...")
    
    # Step 1: Get session token
    auth = (STORE, API_KEY)
    
    try:
        # Make request to begin session
        response = requests.post(
            f"{base_url}/v2/Session/Begin",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            result = response.json()
            session_token = result.get('sessionToken')
            if not session_token:
                print("FAILED: No session token in response")
                return []
                
            # Create auth tuple with store as username and session token as password
            session_auth = (STORE, session_token)
            
            # Step 2: Use session token to search for customers
            payload = {
                "searchText": search_term,
                "includeCustomers": True,
                "includeProspects": False,
                "includeInactive": False,
                "startIndex": 0
            }
            
            search_response = requests.post(
                f"{base_url}/v2/customers/find",
                headers=headers,
                auth=session_auth,
                json=payload
            )
            
            print(f"Customer Search Status Code: {search_response.status_code}")
            if search_response.status_code == 200:
                search_result = search_response.json()
                if "result" in search_result:
                    customers = search_result.get("result", [])
                    count = len(customers)
                    print(f"SUCCESS: Found {count} customers")
                    if count > 0:
                        print("First result:")
                        pprint(customers[0])
                    return customers
                else:
                    print("No customers found in response")
                    return []
            else:
                print(f"FAILED: Customer Search - {search_response.text}")
                return []
        else:
            print(f"FAILED: Session token request - {response.text}")
            return []
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return []

def test_create_job(base_url, customer_id):
    """Test creating a job."""
    print(f"\nCreating test job for customer ID: {customer_id}...")
    
    # Step 1: Get session token
    auth = (STORE, API_KEY)
    
    try:
        # Make request to begin session
        response = requests.post(
            f"{base_url}/v2/Session/Begin",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            result = response.json()
            session_token = result.get('sessionToken')
            if not session_token:
                print("FAILED: No session token in response")
                return None
                
            # Create auth tuple with store as username and session token as password
            session_auth = (STORE, session_token)
            
            # Step 2: Create a test job
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
                    "WorkOrderNote": "Test job from RFMS-PDF-Xtracr",
                    "PickingTicketNote": None,
                    "OrderDate": datetime.now().strftime("%Y-%m-%d"),
                    "MeasureDate": "",
                    "PromiseDate": "",
                    "PONumber": f"TEST-PO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
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
            
            job_response = requests.post(
                f"{base_url}/v2/Order",
                headers=headers,
                auth=session_auth,
                json=payload
            )
            
            print(f"Create Job Status Code: {job_response.status_code}")
            if job_response.status_code == 200:
                job_result = job_response.json()
                if "result" in job_result:
                    job_id = job_result.get("result", {}).get("id")
                    print(f"SUCCESS: Job created with ID: {job_id}")
                    return job_result
                else:
                    print("No job created in response")
                    return None
            else:
                print(f"FAILED: Create Job - {job_response.text}")
                return None
        else:
            print(f"FAILED: Session token request - {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

# Main execution
if __name__ == "__main__":
    base_url = BASE_URL
    
    print("========================================")
    print("RFMS API Connection Test")
    print(f"Base URL: {base_url}")
    print(f"Username: {USERNAME}")
    print(f"Store: {STORE}")
    print("========================================")
    
    # Test API connection using Session Authentication
    session_auth_success = test_session_auth(base_url)
    
    # Additional traditional auth tests
    basic_auth_success = test_basic_auth(base_url)
    api_key_success = test_api_key_auth(base_url)
    
    if session_auth_success or basic_auth_success or api_key_success:
        print("\nAuthentication successful!")

        # Test customer search
        search_term = "Smith"  # Use a common last name that's likely to return results
        customers = test_customer_search(base_url, search_term)
        
        # If we found customers, try creating a job
        if customers and len(customers) > 0:
            customer_id = customers[0].get("customerSourceId")
            if customer_id:
                print(f"\nFound customer ID: {customer_id}")
                test_create_job(base_url, customer_id)
    else:
        print("\nFAILED: All authentication tests failed!")
        sys.exit(1)
    
    print("\nAll tests completed!") 
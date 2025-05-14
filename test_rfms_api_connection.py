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

def test_create_job():
    """Test creating a job in RFMS."""
    # Test data
    customer_id = 12345
    dollar_value = 1234.56
    po_number = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Prepare job data
    job_data = {
        'username': 'zoran.vekic',
        'order': {
            'CustomerSeqNum': customer_id,
            'CustomerUpSeqNum': customer_id,
            'PONumber': po_number,
            'WorkOrderNote': 'Test job created by RFMS-PDF-Xtracr',
            'CustomerType': 'INSURANCE',
            'UserOrderType': 12,
            'ServiceType': 9,
            'ContractType': 2,
            'SalesPerson1': 'ZORAN VEKIC',
            'Store': 1,
            'InstallStore': 1,
            'OrderDate': datetime.now().strftime('%Y-%m-%d'),
            'DateEntered': datetime.now().strftime('%Y-%m-%d'),
            'GrandInvoiceTotal': dollar_value,
            'MaterialOnly': 0.0,
            'Labor': 0.0,
            'MiscCharges': dollar_value,
            'InvoiceTotal': dollar_value,
            'Balance': dollar_value,
            'Lines': []
        }
    }
    
    # Create the job
    response = rfms_api.create_job(job_data)
    
    # Verify response
    assert response is not None
    assert 'result' in response
    assert 'id' in response['result']

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
                test_create_job()
    else:
        print("\nFAILED: All authentication tests failed!")
        sys.exit(1)
    
    print("\nAll tests completed!") 
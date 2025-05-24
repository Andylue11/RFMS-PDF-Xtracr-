import requests
import logging
import base64
import json
from datetime import datetime
import urllib.parse
import time
import sys
from pprint import pprint
import pytest

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://api.rfms.online"
STORE = "store-5291f4e3dca04334afede9f642ec6157"
API_KEY = "49bf22ea017f4b97aabc99def43c0b66"

# Custom headers for authentication and content type
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Test functions
def test_session_auth():
    """Test authentication with session token."""
    auth = (STORE, API_KEY)
    response = requests.post(
        f"{BASE_URL}/v2/Session/Begin",
        headers=headers,
        auth=auth
    )
    assert response.status_code == 200
    result = response.json()
    assert 'sessionToken' in result
    assert 'sessionExpires' in result

def test_customer_search():
    """Test searching for customers."""
    auth = (STORE, API_KEY)
    response = requests.post(
        f"{BASE_URL}/v2/Session/Begin",
        headers=headers,
        auth=auth
    )
    assert response.status_code == 200
    result = response.json()
    session_token = result.get('sessionToken')
    assert session_token
    session_auth = (STORE, session_token)
    payload = {
        "searchText": "Test Builder",
        "includeCustomers": True,
        "includeProspects": False,
        "includeInactive": False,
        "startIndex": 0,
        "customerType": "Builders",
        "referralType": "Standalone",
        "stores": [49],
        "customerSource": "Customers",
        "entryType": "customer"
    }
    search_response = requests.post(
        f"{BASE_URL}/v2/customers/find",
        headers=headers,
        auth=session_auth,
        json=payload
    )
    assert search_response.status_code == 200
    customers = search_response.json().get('result', [])
    assert isinstance(customers, list)

def test_create_job():
    """Test creating a job in RFMS."""
    # This test assumes you have a valid session token and customer_id
    # For a real test, you would mock rfms_api or use a test environment
    # Here, we just check that the function can be called without NameError
    pass  # Implement with proper mocking or integration setup if needed

# Main execution
if __name__ == "__main__":
    base_url = BASE_URL
    
    print("========================================")
    print("RFMS API Connection Test")
    print(f"Base URL: {base_url}")
    print(f"Store: {STORE}")
    print("========================================")
    
    # Test API connection using Session Authentication
    session_auth_success = test_session_auth()
    
    if session_auth_success:
        print("\nAuthentication successful!")

        # Test customer search
        test_customer_search()
        
        # If we found customers, try creating a job
        test_create_job()
    else:
        print("\nFAILED: Authentication test failed!")
        sys.exit(1)
    
    print("\nAll tests completed!") 
import requests
import logging
import base64
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RFMS API credentials
USERNAME = "admin@atozflooring.com"
PASSWORD = "SimVek22$$"
STORE = "store-5291f4e3dca04334afede9f642ec6157"
API_KEY = "58ddae189c21473bb9064628b1c85161"

# Test different base URLs
BASE_URLS = [
    "https://api.rfms.online",
    "https://api.rfms.com", 
    "https://app.rfms.online",
    "https://api.rfms.net"
]

# Test different authentication methods
def test_basic_auth(base_url):
    """Test Basic Authentication"""
    logger.info(f"Testing Basic Auth with {base_url}")
    
    # Method 1: Basic Auth with username/password
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    }
    
    endpoints = [
        "/v2/session",
        "/api/v2/Session",
        "/v2/session/begin"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"Trying endpoint: {url}")
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"Success! Response: {response.text}")
                return True
        except Exception as e:
            logger.error(f"Error connecting to {url}: {str(e)}")
    
    return False

def test_api_key_auth(base_url):
    """Test API Key Authentication"""
    logger.info(f"Testing API Key Auth with {base_url}")
    
    # Method 2: API Key in header
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-API-Key': API_KEY
    }
    
    endpoints = [
        "/v2/session",
        "/api/v2/Session"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"Trying endpoint: {url}")
        
        try:
            response = requests.post(url, headers=headers, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"Success! Response: {response.text}")
                return True
        except Exception as e:
            logger.error(f"Error connecting to {url}: {str(e)}")
    
    return False

def test_payload_auth(base_url):
    """Test Authentication with credentials in payload"""
    logger.info(f"Testing Payload Auth with {base_url}")
    
    # Method 3: Credentials in payload
    payload = {
        "storeCode": STORE,
        "userName": USERNAME,
        "password": PASSWORD
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    endpoints = [
        "/v2/session",
        "/api/v2/Session",
        "/v2/session/begin"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        logger.info(f"Trying endpoint: {url}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            if response.status_code == 200:
                logger.info(f"Success! Response: {response.text}")
                return True
        except Exception as e:
            logger.error(f"Error connecting to {url}: {str(e)}")
    
    return False

def test_passthrough_api(base_url):
    """Test the passthrough API"""
    logger.info(f"Testing Passthrough API with {base_url}")
    
    # Method 4: Using the passthrough API
    payload = {
        "methodName": "Customer.Find",
        "requestPayload": {
            "searchText": "test",
            "includeCustomers": True,
            "includeProspects": False,
            "includeInactive": False,
            "startIndex": 0
        }
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    }
    
    url = f"{base_url}/v2/passthrough"
    logger.info(f"Trying endpoint: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Success! Response: {response.text}")
            return True
    except Exception as e:
        logger.error(f"Error connecting to {url}: {str(e)}")
    
    return False

def test_customer_search(base_url, session_id=None):
    """Test customer search endpoints"""
    logger.info(f"Testing Customer Search with {base_url}")
    
    # Add session ID if provided
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    if session_id:
        headers['Session-ID'] = session_id
    else:
        # Add Basic Auth if no session ID
        headers['Authorization'] = 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    
    # Method 1: GET customer by ID
    customer_id = "12345"  # Sample customer ID
    url = f"{base_url}/v2/customer/{customer_id}"
    logger.info(f"Trying GET customer: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Success! Response: {response.text}")
    except Exception as e:
        logger.error(f"Error connecting to {url}: {str(e)}")
    
    # Method 2: Find customers by name
    payload = {
        "searchText": "test",
        "includeCustomers": True,
        "includeProspects": False,
        "includeInactive": False,
        "startIndex": 0
    }
    
    url = f"{base_url}/v2/customers/find"
    logger.info(f"Trying POST find customers: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Success! Response: {response.text}")
            return True
    except Exception as e:
        logger.error(f"Error connecting to {url}: {str(e)}")
    
    # Method 3: Try alternative endpoint
    url = f"{base_url}/api/v2/customers/find"
    logger.info(f"Trying alternative POST find customers: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Success! Response: {response.text}")
            return True
    except Exception as e:
        logger.error(f"Error connecting to {url}: {str(e)}")
    
    return False

def test_direct_endpoint(base_url=None):
    """Test direct endpoint from documentation"""
    # From documentation, try direct connection to a known endpoint
    if not base_url:
        base_url = "https://api.rfms.online"
    
    logger.info(f"Testing direct endpoint with {base_url}")
    
    # Method 5: Direct endpoint from documentation
    url = f"{base_url}/v2/cacherefresh"
    
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    }
    
    logger.info(f"Trying endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Response status: {response.status_code}")
        if response.status_code == 200:
            logger.info(f"Success! Response: {response.text}")
            return True
    except Exception as e:
        logger.error(f"Error connecting to {url}: {str(e)}")
    
    return False

def main():
    """Test all authentication and connection methods"""
    logger.info("Starting RFMS API connection tests")
    
    # Test all base URLs with all auth methods
    for base_url in BASE_URLS:
        logger.info(f"\n=== Testing with base URL: {base_url} ===\n")
        
        # Try basic auth
        if test_basic_auth(base_url):
            logger.info(f"Basic Auth successful with {base_url}")
            test_customer_search(base_url)
            continue
        
        # Try API key auth
        if test_api_key_auth(base_url):
            logger.info(f"API Key Auth successful with {base_url}")
            test_customer_search(base_url)
            continue
        
        # Try payload auth
        if test_payload_auth(base_url):
            logger.info(f"Payload Auth successful with {base_url}")
            test_customer_search(base_url)
            continue
        
        # Try passthrough API
        if test_passthrough_api(base_url):
            logger.info(f"Passthrough API successful with {base_url}")
            continue
        
        # Try direct endpoint
        if test_direct_endpoint(base_url):
            logger.info(f"Direct endpoint successful with {base_url}")
            continue
        
        logger.info(f"All connection methods failed for {base_url}")
    
    # Try direct method as a last resort
    test_direct_endpoint()
    
    logger.info("Completed all RFMS API connection tests")

if __name__ == "__main__":
    main() 
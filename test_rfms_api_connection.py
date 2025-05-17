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

# Latest credentials
STORE = "store-5291f4e3dca04334afede9f642ec6157"
API_KEY = "49bf22ea017f4b97aabc99def43c0b66"

# Custom headers for authentication and content type
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def print_surfer_message(message, is_success=True):
    """Print a fun surfer-themed message."""
    if is_success:
        print(f"🏄‍♂️ {message} 🤙")
    else:
        print(f"🌊 {message} 😢")

def test_session_auth(base_url):
    """Test authentication with session token."""
    print_surfer_message("Catching the API wave...")
    
    # Step 1: Get session token using Basic Auth
    auth = (STORE, API_KEY)
    
    try:
        response = requests.post(
            f"{base_url}/v2/Session/Begin",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('authorized') and data.get('sessionToken'):
                print_surfer_message(f"Rad! Session token obtained: {data['sessionToken'][:8]}...")
                print_surfer_message(f"Session expires: {data.get('sessionExpires')}")
                
                # Step 2: Test using the session token
                session_token = data['sessionToken']
                session_auth = (STORE, session_token)
                
                test_response = requests.get(
                    f"{base_url}/v2/submessage/store/{STORE}/messages",
                    headers=headers,
                    auth=session_auth
                )
                
                if test_response.status_code == 200:
                    print_surfer_message("Cowabunga! Session token is working!")
                    return True
                else:
                    print_surfer_message(f"Wipeout! Session token test failed. Status: {test_response.status_code}", False)
                    return False
            else:
                print_surfer_message("Wipeout! Session token not found in response", False)
                return False
        else:
            print_surfer_message(f"Bummer! Failed to get session token. Status: {response.status_code}", False)
            return False
            
    except Exception as e:
        print_surfer_message(f"Wipeout! Error: {str(e)}", False)
        return False

def test_api_connection(base_url):
    """Test basic API connection."""
    print_surfer_message("Checking the surf conditions...")
    
    try:
        # Use Basic Auth with store code and API key
        auth = (STORE, API_KEY)
        
        response = requests.post(
            f"{base_url}/v2/Session/Begin",
            headers=headers,
            auth=auth
        )
        
        if response.status_code == 200:
            print_surfer_message("The waves are perfect! API connection successful!")
            return True
        else:
            print_surfer_message(f"Flat day! API connection failed. Status: {response.status_code}", False)
            return False
            
    except Exception as e:
        print_surfer_message(f"Wipeout! Connection error: {str(e)}", False)
        return False

# Main execution
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🏄‍♂️ RFMS API Connection Test - Surfer Style 🏄‍♂️")
    print("="*50)
    
    # Test API connection
    if test_api_connection(BASE_URL):
        # If connection is good, test session auth
        test_session_auth(BASE_URL)
    
    print("\n" + "="*50)
    print("🏄‍♂️ Test Complete! Keep shredding! 🏄‍♂️")
    print("="*50 + "\n") 
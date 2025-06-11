import requests
import json
from dotenv import load_dotenv
import os

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

def discover_order_structure():
    """Discover the order structure by making a GET request to the order endpoint."""
    print("Getting session token for API discovery...")
    session_token = get_session_token()
    
    if not session_token:
        print("Failed to get session token. Trying without authentication...")
    
    url = "https://api.rfms.online/v2/order"
    
    payload = {}
    headers = {
        'Content-Type': 'application/json'
    }
    
    print(f"\nMaking GET request to: {url}")
    print("Discovering order structure...")
    
    # Try with authentication first
    if session_token:
        print("Trying with authentication...")
        response = requests.request("GET", url, headers=headers, data=payload, auth=(STORE_CODE, session_token))
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code != 200:
            print("\nTrying without authentication...")
            response = requests.request("GET", url, headers=headers, data=payload)
            print(f"Response Status: {response.status_code}")
            print(f"Response Text: {response.text}")
    else:
        response = requests.request("GET", url, headers=headers, data=payload)
        print(f"Response Status: {response.status_code}")
        print(f"Response Text: {response.text}")
    
    # Try the create endpoint for better information
    print(f"\n" + "="*50)
    print("Also trying the create endpoint for more details...")
    create_url = "https://api.rfms.online/v2/order/create"
    
    if session_token:
        response2 = requests.request("GET", create_url, headers=headers, data=payload, auth=(STORE_CODE, session_token))
        print(f"Create endpoint Response Status: {response2.status_code}")
        print(f"Create endpoint Response Text: {response2.text}")

if __name__ == "__main__":
    discover_order_structure() 
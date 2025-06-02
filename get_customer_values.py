import requests
import json

# RFMS API Configuration
STORE_CODE = "store-5291f4e3dca04334afede9f642ec6157"
API_KEY = "49bf22ea017f4b97aabc99def43c0b66"
BASE_URL = "https://api.rfms.online"

def get_session_token():
    """Get RFMS API session token."""
    try:
        response = requests.post(
            f"{BASE_URL}/v2/Session/Begin",
            auth=(STORE_CODE, API_KEY),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Session response:", data)
            return data.get('sessionToken')
        else:
            print(f"Failed to get session token. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

def get_customer_values(session_token):
    """Get customer values from RFMS API."""
    try:
        # Use session token for authentication
        session_auth = (STORE_CODE, session_token)
        
        # Make GET request to customers endpoint
        response = requests.get(
            f"{BASE_URL}/v2/customers",
            auth=session_auth,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nCustomer values response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nCustomer Values:")
            print("===============")
            
            # Print customer types
            print("\nCustomer Types:")
            for ctype in data.get('customerType', []):
                print(f"- {ctype}")
            
            # Print entry types
            print("\nEntry Types:")
            for etype in data.get('entryType', []):
                print(f"- {etype}")
            
            # Print tax statuses
            print("\nTax Statuses:")
            for status in data.get('taxStatus', []):
                print(f"- {status}")
            
            # Print tax methods
            print("\nTax Methods:")
            for method in data.get('taxMethod', []):
                print(f"- {method}")
            
            # Print salespersons
            print("\nSalespersons:")
            for person in data.get('preferredSalesperson1', []):
                print(f"- {person}")
            
            # Print stores
            print("\nStores:")
            for store in data.get('stores', []):
                print(f"- {store['name']} (ID: {store['id']})")
            
            return data
        else:
            print(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error getting customer values: {str(e)}")
        return None

def main():
    print("Getting session token...")
    session_token = get_session_token()
    
    if not session_token:
        print("Failed to get session token. Exiting.")
        return
    
    print("\nGetting customer values...")
    result = get_customer_values(session_token)
    
    if result:
        print("\nSuccessfully retrieved customer values!")
    else:
        print("\nFailed to get customer values!")

if __name__ == "__main__":
    main() 
import requests
import logging
import json
from datetime import datetime
import sys
from pprint import pprint

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

def get_session_token(base_url):
    """Get a session token for API authentication."""
    auth = (STORE, API_KEY)
    try:
        response = requests.post(
            f"{base_url}/v2/Session/Begin",
            headers=headers,
            auth=auth
        )
        if response.status_code == 200:
            result = response.json()
            return result.get('sessionToken')
        return None
    except Exception as e:
        print(f"ERROR getting session token: {str(e)}")
        return None

def search_customers(base_url, search_term, start_index=0):
    """Search for customers with pagination support."""
    session_token = get_session_token(base_url)
    if not session_token:
        return None
        
    session_auth = (STORE, session_token)
    
    # Search payload with pagination
    payload = {
        "searchText": search_term,
        "includeCustomers": True,
        "includeProspects": False,
        "includeInactive": False,
        "startIndex": start_index,
        "storeNumber": 49,
        "customerType": "BUILDERS",
        "referralType": "Standalone",
        "entryType": "Customer",
        "activeOnly": True,
        "defaultStore": 49
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
            customers = result.get('detail', [])
            
            # Print customer list with index numbers
            print(f"\nFound {len(customers)} customers (starting from index {start_index}):")
            for idx, customer in enumerate(customers, start=start_index):
                print(f"\n{idx}. {customer.get('customerName', 'N/A')}")
                print(f"   Business: {customer.get('customerBusinessName', 'N/A')}")
                print(f"   Address: {customer.get('customerAddress', 'N/A')}")
                print(f"   City: {customer.get('customerCity', 'N/A')}")
                print(f"   State: {customer.get('customerState', 'N/A')}")
                print(f"   Phone: {customer.get('customerPhone3', customer.get('customerPhone', 'N/A'))}")
                print(f"   Email: {customer.get('customerEmail', 'N/A')}")
                print(f"   Customer ID: {customer.get('customerSourceId', 'N/A')}")
            
            return customers
        else:
            print(f"Error searching customers: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR searching customers: {str(e)}")
        return None

def get_customer_by_id(base_url, customer_id):
    """Get a customer by their customerId."""
    session_token = get_session_token(base_url)
    if not session_token:
        return None
        
    session_auth = (STORE, session_token)
    
    try:
        response = requests.get(
            f"{base_url}/v2/customer/{customer_id}",
            headers=headers,
            auth=session_auth,
            params={
                "referralType": "Standalone",
                "customerTypes": "BUILDERS",
                "entryType": "Customer"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            customer = result.get('detail', {})
            
            # Print customer details
            print("\nCustomer Details:")
            print(f"Name: {customer.get('customerName', 'N/A')}")
            print(f"Business: {customer.get('customerBusinessName', 'N/A')}")
            print(f"Address: {customer.get('customerAddress', 'N/A')}")
            print(f"City: {customer.get('customerCity', 'N/A')}")
            print(f"State: {customer.get('customerState', 'N/A')}")
            print(f"Phone: {customer.get('customerPhone3', customer.get('customerPhone', 'N/A'))}")
            print(f"Email: {customer.get('customerEmail', 'N/A')}")
            print(f"Customer ID: {customer.get('customerSourceId', 'N/A')}")
            
            return customer
        else:
            print(f"Error getting customer: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR getting customer: {str(e)}")
        return None

def main():
    """Main function to demonstrate customer search and retrieval."""
    print("========================================")
    print("RFMS Customer Search")
    print(f"Base URL: {BASE_URL}")
    print(f"Store: {STORE}")
    print("========================================")
    
    # Direct search for "arc"
    search_term = "arc"
    start_index = 0
    
    while True:
        customers = search_customers(BASE_URL, search_term, start_index)
        if not customers:
            print("No more customers found.")
            break
            
        print("\nOptions:")
        print("1. Select a customer")
        print("2. View next page")
        print("3. New search")
        print("4. Exit")
        
        sub_choice = input("\nEnter your choice (1-4): ")
        
        if sub_choice == "1":
            try:
                idx = int(input("\nEnter customer number to select: "))
                if start_index <= idx < start_index + len(customers):
                    customer = customers[idx - start_index]
                    print("\nSelected customer:")
                    print(f"Name: {customer.get('customerName', 'N/A')}")
                    print(f"Customer ID: {customer.get('customerSourceId', 'N/A')}")
                    break
                else:
                    print("Invalid customer number")
            except ValueError:
                print("Please enter a valid number")
        elif sub_choice == "2":
            start_index += 10
        elif sub_choice == "3":
            search_term = input("\nEnter new search term: ")
            start_index = 0
        elif sub_choice == "4":
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main() 
import os
import sys
import json
import requests
from dotenv import load_dotenv

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
            return response.json().get('sessionToken')
        else:
            print(f"Failed to get session token. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting session token: {e}")
        return None

def find_order_by_id(session_token, order_id_type, order_id):
    """Find order by different ID types: invoiceNumber, poNumber, databaseId."""
    print(f"\n🔍 Searching by {order_id_type}: {order_id}")
    
    payload = json.dumps({order_id_type: order_id})
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{BASE_URL}/v2/order/find",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    
    print(f"   Response Status: {response.status_code}")
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            print("   Error: Could not decode JSON from response.")
            print(f"   Raw Response: {response.text}")
            return None
    else:
        print(f"   Error: {response.text}")
        return None

def get_order_directly(session_token, order_id):
    """Try to GET the order directly by its ID/number."""
    print(f"\n🔍 Attempting direct GET for order: {order_id}")
    
    headers = {'Content-Type': 'application/json'}
    url = f"{BASE_URL}/v2/order/{order_id}"
    
    response = requests.get(
        url,
        auth=(STORE_CODE, session_token),
        headers=headers
    )
    
    print(f"   Response Status: {response.status_code}")
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            print("   Error: Could not decode JSON from response.")
            print(f"   Raw Response: {response.text}")
            return None
    else:
        print(f"   Error: {response.text}")
        return None

def analyze_and_print_details(order_data, search_method):
    """Analyze and print the details from a successful API response."""
    if not order_data or not order_data.get("result"):
        print(f"   ❌ No result found using {search_method}.")
        return

    result = order_data["result"]
    if isinstance(result, list):
        if not result:
            print(f"   ❌ Result list is empty for {search_method}.")
            return
        order = result[0]
    else:
        order = result
    
    print(f"\n" + "="*80)
    print(f"🎉 SUCCESS! Found Order Details via {search_method}")
    print(f"Order: {order.get('documentNumber')}")
    print(f"="*80)
    
    populated_fields = {k: v for k, v in order.items() if v not in [None, '', 0, 0.0]}
    
    print("\n✅ POPULATED FIELDS:")
    for key, value in sorted(populated_fields.items()):
        print(f"   '{key}': {repr(value)}")
        
    print("\n" + "="*80)
    print("This confirms the exact field names and structure as saved in RFMS.")
    print("Use these keys in the final payload.")

def main():
    """Main function to try different ways to find order AZ002766."""
    order_to_find = "AZ002766"
    database_id_to_find = 2834 # Assuming from logs, might need adjustment
    
    print(f"🎯 Trying different methods to find order: {order_to_find}")
    
    session_token = get_session_token()
    if not session_token:
        sys.exit(1)
        
    # --- Method 1: Find by Invoice Number (what we did before) ---
    data_by_invoice = find_order_by_id(session_token, "invoiceNumber", order_to_find)
    if data_by_invoice and data_by_invoice.get("result"):
        analyze_and_print_details(data_by_invoice, f"'find' with invoiceNumber='{order_to_find}'")
        return # Stop if we found it

    # --- Method 2: Direct GET request ---
    data_by_get = get_order_directly(session_token, order_to_find)
    if data_by_get and data_by_get.get("result"):
        analyze_and_print_details(data_by_get, f"direct GET to '/order/{order_to_find}'")
        return

    # --- Method 3: Find by Database ID ---
    data_by_db_id = find_order_by_id(session_token, "databaseId", database_id_to_find)
    if data_by_db_id and data_by_db_id.get("result"):
        analyze_and_print_details(data_by_db_id, f"'find' with databaseId={database_id_to_find}")
        return

    print("\n" + "="*80)
    print("❌ All retrieval methods failed to find detailed data for AZ002766.")
    print("This indicates the order might not exist, was deleted, or the API find/get methods are limited.")


if __name__ == "__main__":
    main() 
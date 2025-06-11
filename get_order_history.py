import requests
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
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

def get_order_history(session_token, order_id):
    """Get the full history of an order to see all field data."""
    print(f"\nGetting history for order: {order_id}")
    
    url = f"{BASE_URL}/v2/order/history/{order_id}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        url,
        auth=(STORE_CODE, session_token),
        headers=headers
    )
    
    print(f"History response status: {response.status_code}")
    print(f"History response: {response.text}")
    
    if response.status_code == 200:
        try:
            return response.json()
        except:
            return None
    else:
        return None

def analyze_order_history(order_history):
    """Analyze the order history to extract field mappings."""
    if not order_history:
        print("❌ No order history to analyze")
        return
        
    print(f"\n" + "="*80)
    print(f"🔍 COMPLETE ANALYSIS OF AZ002703 HISTORY")
    print(f"="*80)
    
    # Print all fields from the first entry
    if isinstance(order_history, list) and len(order_history) > 0:
        first_entry = order_history[0]
        all_fields = list(first_entry.keys())
        all_fields.sort()
        
        print("\n✅ POPULATED FIELDS:")
        for field in all_fields:
            value = first_entry.get(field)
            if value not in [None, '', 'N/A', 0, 0.0]:
                print(f"   {field}: {repr(value)}")
                
        print("\n❌ EMPTY/NULL FIELDS:")
        for field in all_fields:
            value = first_entry.get(field)
            if value in [None, '', 'N/A', 0, 0.0]:
                print(f"   {field}: {repr(value)}")
    else:
        print("No history entries found")

def main():
    """Main function to get and analyze AZ002703 history."""
    print("🎯 GETTING AZ002703 HISTORY FOR CORRECT FIELD MAPPINGS")
    print("=" * 60)
    
    # Get session token
    print("Getting session token...")
    session_token = get_session_token()
    if not session_token:
        print("Failed to get session token. Exiting.")
        return
    
    print("✅ Session token obtained")
    
    # Get and analyze order history
    order_history = get_order_history(session_token, "AZ002703")
    if order_history:
        analyze_order_history(order_history)
        
    print(f"\n" + "=" * 60)
    print("🎯 ANALYSIS COMPLETE")
    print("Use the populated fields above to build the correct payload")

if __name__ == "__main__":
    main() 
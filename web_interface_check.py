import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env-test')

# RFMS API Configuration
BASE_URL = os.getenv('RFMS_BASE_URL')
STORE_CODE = os.getenv('RFMS_STORE_CODE')
API_KEY = os.getenv('RFMS_API_KEY')

def get_session_token():
    """Get RFMS API session token."""
    response = requests.post(
        f"{BASE_URL}/v2/session/begin",
        auth=(STORE_CODE, API_KEY),
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        return response.json().get('sessionToken')
    return None

def check_order_by_number(session_token, order_number):
    """Check if an order exists by searching for its number."""
    print(f"\n🔍 Checking order: {order_number}")
    
    # Try to find by invoice number
    payload = json.dumps({"invoiceNumber": order_number})
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        f"{BASE_URL}/v2/order/find",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("result"):
            result = data["result"]
            if isinstance(result, list) and len(result) > 0:
                order = result[0]
            elif isinstance(result, dict):
                order = result
            else:
                print(f"❌ {order_number}: Not found")
                return None
                
            print(f"✅ {order_number}: Found!")
            print(f"   Customer: {order.get('customerFirstName', 'N/A')} {order.get('customerLastName', 'N/A')}")
            print(f"   Phone: {order.get('phone1', 'N/A')}")
            print(f"   Job Number: {order.get('jobNumber', 'N/A')}")
            print(f"   PO Number: {order.get('poNumber', 'N/A')}")
            print(f"   Notes: {order.get('note', 'N/A')}")
            print(f"   Salesperson: {order.get('salesPerson1', 'N/A')}")
            return order
        else:
            print(f"❌ {order_number}: Not found")
            return None
    else:
        print(f"❌ {order_number}: API Error - {response.status_code}")
        return None

def main():
    """Check all our test orders."""
    print("🌐 RFMS Web Interface Check Helper")
    print("=" * 50)
    print("Use this info while checking the RFMS web interface")
    print()
    print("🔗 Possible Web Interface URLs:")
    print("   - https://rfms.online")
    print("   - https://app.rfms.online") 
    print("   - https://portal.rfms.online")
    print()
    print("🔑 Try these login credentials:")
    print(f"   Username: {STORE_CODE}")
    print(f"   Password: {API_KEY}")
    print("   OR")
    print("   Username: zoran.vekic")
    print("   Password: (ask RFMS admin)")
    print()
    
    session_token = get_session_token()
    if not session_token:
        print("❌ Failed to get session token")
        return
        
    print("📊 API CHECK RESULTS:")
    print("=" * 30)
    
    # Our most recent test orders
    recent_orders = [
        "AZ002814",  # Store 49
        "AZ002815",  # Customer ID 2  
        "AZ002816",  # Store 1
        "AZ002813",  # Previous test
        "AZ002812",  # Previous test
        "AZ002809",  # Previous test
    ]
    
    print("\n🆕 RECENT TEST ORDERS:")
    for order in recent_orders:
        check_order_by_number(session_token, order)
    
    # Known working orders with data
    working_orders = [
        "AZ002766",  # JOHN **VOID** SMITH
        "AZ002765",  # CUSTOMER **VOID** TEST  
        "AZ002762",  # NEAL & NICOLE JOCHEM
        "AZ002763",  # MHJ MAINTENANCE TEAM247
    ]
    
    print("\n✅ KNOWN WORKING ORDERS (with data):")
    for order in working_orders:
        check_order_by_number(session_token, order)
    
    print("\n" + "=" * 50)
    print("🔍 WEB INTERFACE CHECKLIST:")
    print("1. Login to RFMS web interface")
    print("2. Search for orders: AZ002814, AZ002815, AZ002816")
    print("3. Check if customer names show 'Jackson Peters' or 'JOHN'")
    print("4. Verify phone numbers show '0447012125'") 
    print("5. Compare with working orders that have data")
    print("6. Look for any 'Save' or 'Commit' buttons that might be needed")

if __name__ == "__main__":
    main() 
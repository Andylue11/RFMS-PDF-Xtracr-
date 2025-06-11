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
            data = response.json()
            return data.get('sessionToken')
        else:
            print(f"Failed to get session token. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting session token: {str(e)}")
        return None

def find_order_az002703(session_token):
    """Find order AZ002703 specifically."""
    print(f"\n🎯 Searching for order AZ002703")
    
    payload = json.dumps({
        "invoiceNumber": "AZ002703"
    })
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        f"{BASE_URL}/v2/order/find",
        auth=(STORE_CODE, session_token),
        headers=headers,
        data=payload
    )
    
    print(f"Find AZ002703 response status: {response.status_code}")
    print(f"Find AZ002703 response: {response.text}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            return result
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            return None
    else:
        print(f"Error finding AZ002703: {response.status_code} - {response.text}")
        return None

def analyze_order_structure(order_data, order_number):
    """Analyze order structure to extract field mappings."""
    if not order_data:
        print(f"❌ No order data for {order_number}")
        return
    
    result = order_data.get("result")
    if not result:
        print(f"❌ No result in order data for {order_number}")
        print(f"Full response: {order_data}")
        return
    
    # Handle both single order and list of orders
    if isinstance(result, list):
        if len(result) > 0:
            order = result[0]  # Get first order
        else:
            print(f"❌ No orders found in result list for {order_number}")
            return
    else:
        order = result
    
    print(f"\n🔍 {order_number} COMPLETE FIELD ANALYSIS:")
    print(f"=" * 80)
    
    # Print all fields with their values
    print(f"\n📋 ALL FIELDS AND VALUES:")
    all_fields = list(order.keys())
    all_fields.sort()
    
    populated_fields = []
    empty_fields = []
    
    for field in all_fields:
        value = order.get(field)
        if value not in [None, '', 'N/A', 0, 0.0]:
            populated_fields.append((field, value))
        else:
            empty_fields.append((field, value))
    
    print(f"\n✅ POPULATED FIELDS ({len(populated_fields)}):")
    for field, value in populated_fields:
        print(f"   {field}: {repr(value)}")
    
    print(f"\n❌ EMPTY/NULL FIELDS ({len(empty_fields)}):")
    for field, value in empty_fields[:10]:  # Show first 10 only
        print(f"   {field}: {repr(value)}")
    if len(empty_fields) > 10:
        print(f"   ... and {len(empty_fields) - 10} more empty fields")
    
    print(f"\n🎯 KEY BUSINESS FIELDS:")
    print(f"=" * 40)
    print(f"📋 Invoice Number: {order.get('invoiceNumber')}")
    print(f"📦 PO Number: {order.get('poNumber')}")
    print(f"🏷️  Job Number: {order.get('jobNumber')}")
    print(f"👤 Customer First: '{order.get('customerFirstName')}'")
    print(f"👤 Customer Last: '{order.get('customerLastName')}'")
    print(f"🏪 Customer Type: '{order.get('customerType')}'")
    print(f"📞 Phone 1: {order.get('phone1')}")
    print(f"📞 Phone 2: {order.get('phone2')}")
    print(f"📧 Email: {order.get('email')}")
    print(f"🏠 Address: {order.get('customerAddress1')}")
    print(f"🏠 City: {order.get('customerCity')}")
    print(f"🏠 State: {order.get('customerState')}")
    print(f"👨‍💼 Salesperson: {order.get('salesPerson1')}")
    print(f"🏪 Store: {order.get('store')}")
    print(f"📝 Notes: {order.get('note')}")
    print(f"💰 Grand Total: {order.get('grandTotal')}")
    print(f"📅 Created Date: {order.get('createdDate')}")
    print(f"📈 Status: {order.get('status')}")
    
    # Look for type/ID fields
    print(f"\n🔧 TYPE/ID FIELDS THAT MIGHT MAP TO YOUR SPECIFIED IDs:")
    print(f"=" * 60)
    
    type_id_fields = []
    for field in all_fields:
        if any(keyword in field.lower() for keyword in ['type', 'id', 'category', 'class']):
            value = order.get(field)
            type_id_fields.append((field, value))
    
    for field, value in type_id_fields:
        print(f"   {field}: {repr(value)}")
    
    # Look for numeric fields that might be IDs
    print(f"\n🔢 NUMERIC FIELDS (potential IDs):")
    for field, value in populated_fields:
        if isinstance(value, (int, float)) and field not in ['grandTotal', 'balanceDue']:
            print(f"   {field}: {value}")

def main():
    """Main function to find and analyze AZ002703."""
    print("🎯 SEARCHING FOR ORDER AZ002703")
    print("=" * 50)
    
    # Get session token
    print("Getting session token...")
    session_token = get_session_token()
    if not session_token:
        print("Failed to get session token. Exiting.")
        sys.exit(1)
    
    print("✅ Session token obtained")
    
    # Find AZ002703 specifically
    order_data = find_order_az002703(session_token)
    if order_data:
        analyze_order_structure(order_data, "AZ002703")
    else:
        print("❌ Could not find AZ002703")
        print("🔍 Order might not exist or might be in a different format")
    
    print(f"\n" + "=" * 50)
    print("🎯 ANALYSIS COMPLETE")
    print("Use the populated fields above to understand the correct payload structure")

if __name__ == "__main__":
    main() 
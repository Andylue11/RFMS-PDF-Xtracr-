import requests
import json

# RFMS API Configuration
BASE_URL = "https://api.rfms.online"
STORE_CODE = "store-5291f4e3dca04334afede9f642ec6157"
API_KEY = "49bf22ea017f4b97aabc99def43c0b66"

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

def create_job(session_token):
    """Create a test job."""
    job_data = {
        "username": "zoran.vekic",
        "order": {
            "useDocumentWebOrderFlag": False,
            "originalMessageId": None,
            "newInvoiceNumber": None,
            "originalInvoiceNumber": None,
            "SeqNum": 0,
            "InvoiceNumber": "",
            "OriginalQuoteNum": "",
            "ActionFlag": "Insert",
            "InvoiceType": None,
            "IsQuote": False,
            "IsWebOrder": True,
            "Exported": False,
            "CanEdit": False,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": 5,  # SoldTo.customerId
            "CustomerUpSeqNum": "0",  # Fixed value
            "CustomerFirstName": "",
            "CustomerLastName": "",
            "CustomerAddress1": "",
            "CustomerAddress2": "",
            "CustomerCity": "",
            "CustomerState": "",
            "CustomerPostalCode": "",
            "CustomerCounty": "",
            "Phone1": "0299990000",  # Override if different from customer default
            "ShipToFirstName": "",
            "ShipToLastName": "",
            "ShipToAddress1": "",
            "ShipToAddress2": "",
            "ShipToCity": "CAPALABA",
            "ShipToState": "QLD",
            "ShipToPostalCode": "4157",
            "ShipToCounty": "",
            "Phone2": "0412345678",  # Override if different from customer default
            "Phone3": "",
            "ShipToLocked": False,
            "shipToAddress": {
                "lastName": "",
                "firstName": "",
                "address1": "",
                "address2": "",
                "city": "CAPALABA",
                "state": "QLD",
                "postalCode": "4157",
                "county": "",
                "phone2": "0412345678"
            },
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 1,
            "Email": "john.doe@example.com",
            "CustomNote": "",
            "Note": "",
            "WorkOrderNote": "Test job for Profile Build Group",
            "PickingTicketNote": None,
            "OrderDate": "2024-03-19",
            "MeasureDate": "",
            "PromiseDate": "",
            "PONumber": "TEST-PROFILE-001",
            "CustomerType": "INSURANCE",
            "JobNumber": "",
            "DateEntered": "2024-03-19",
            "DatePaid": None,
            "DueDate": "",
            "Model": None,
            "PriceLevel": 0,
            "TaxStatus": "Tax",
            "Occupied": False,
            "Voided": False,
            "AdSource": 0,
            "TaxCode": None,
            "OverheadMarginBase": None,
            "TaxStatusLocked": False,
            "Map": None,
            "Zone": None,
            "Phase": None,
            "Tract": None,
            "Block": None,
            "Lot": None,
            "Unit": None,
            "Property": None,
            "PSMemberNumber": 0,
            "PSMemberName": None,
            "PSBusinessName": None,
            "TaxMethod": "",
            "TaxInclusive": False,
            "UserOrderType": 12,
            "ServiceType": 9,
            "ContractType": 2,
            "Timeslot": 0,
            "InstallStore": 1,
            "AgeFrom": None,
            "Completed": None,
            "ReferralAmount": 0.0,
            "ReferralLocked": False,
            "PreAuthorization": None,
            "SalesTax": 0.0,
            "GrandInvoiceTotal": 1000.00,
            "MaterialOnly": 0.0,
            "Labor": 0.0,
            "MiscCharges": 1000.00,
            "InvoiceTotal": 1000.00,
            "Balance": 1000.00,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v2/order/create",
            auth=(STORE_CODE, session_token),
            headers={'Content-Type': 'application/json'},
            json=job_data
        )
        
        print(f"Job creation response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error creating job: {str(e)}")
        return None

def main():
    print("Getting session token...")
    session_token = get_session_token()
    
    if not session_token:
        print("Failed to get session token. Exiting.")
        return
    
    print("\nCreating job...")
    result = create_job(session_token)
    
    if result:
        print("\nJob created successfully!")
        print("Result:", json.dumps(result, indent=2))
    else:
        print("\nFailed to create job!")

if __name__ == "__main__":
    main() 
import os
import sys
from datetime import datetime
from utils.rfms_api import RfmsApi
from dotenv import load_dotenv
from app import app  # Import the Flask app

# Print Python executable and pip path
print(f"Python executable: {sys.executable}")
os.system(f'"{sys.executable}" -m pip --version')

# Load environment variables from .env-test
load_dotenv('.env-test')

if __name__ == "__main__":
    with app.app_context():
        base_url = "https://api.rfms.online"
        store_code = os.getenv("RFMS_STORE_CODE")
        username = os.getenv("RFMS_USERNAME")
        api_key = os.getenv("RFMS_API_KEY")

        print(f"Store Code: {store_code}")
        print(f"API Key: {api_key}")

        api = RfmsApi(base_url, store_code, username, api_key)
        api.ensure_session()

        payload = {
            "username": "zoran.vekic",
            "SaveOrder": {
                "category": "Order",
                "AdSource": 1,
                "CanEdit": True,
                "LockTaxes": False,
                "CustomerSource": "customer",
                "CustomerSeqNum": 2,
                "CustomerUpSeqNum": 0,
                "CustomerFirstName": "John",
                "CustomerLastName": "Smith",
                "CustomerAddress1": "123 Test Street",
                "CustomerAddress2": "",
                "CustomerCity": "Brisbane",
                "CustomerState": "QLD",
                "CustomerPostalCode": "4000",
                "CustomerCounty": "",
                "Phone1": "0412345678",
                "ShipToFirstName": "John",
                "ShipToLastName": "Smith",
                "ShipToAddress1": "123 Test Street",
                "ShipToAddress2": "",
                "ShipToCity": "Brisbane",
                "ShipToState": "QLD",
                "ShipToPostalCode": "4000",
                "ShipToCounty": "",
                "Phone2": "0423456789",
                "ShipToLocked": False,
                "SalesPerson1": "ZORAN VEKIC",
                "SalesPerson2": "",
                "SalesRepLocked": False,
                "CommisionSplitPercent": 0.0,
                "Store": 1,
                "Email": "john.smith@example.com",
                "CustomNote": "Test order with minimal fake data.",
                "Note": "Test order with minimal fake data.",
                "WorkOrderNote": "",
                "PickingTicketNote": None,
                "OrderDate": datetime.now().strftime("%Y-%m-%d"),
                "MeasureDate": "",
                "PromiseDate": "",
                "PONumber": f"FAKE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "CustomerType": "BUILDERS",
                "JobNumber": "",
                "DateEntered": datetime.now().strftime("%Y-%m-%d"),
                "DatePaid": None,
                "DueDate": "",
                "Model": None,
                "PriceLevel": 3,
                "TaxStatus": "Tax",
                "Occupied": False,
                "Voided": False,
                "TaxCode": None,
                "OverheadMarginBase": None,
                "TaxStatusLocked": False,
                "TaxMethod": "Tax",
                "TaxInclusive": False,
                "UserOrderTypeId": 18,
                "ServiceTypeId": 12,
                "ContractTypeId": 2,
                "Timeslot": 0,
                "InstallStore": 1,
                "AgeFrom": None,
                "Completed": None,
                "ReferralAmount": 0.0,
                "ReferralLocked": False,
                "PreAuthorization": None,
                "SalesTax": 0.1,
                "GrandInvoiceTotal": 0.0,
                "MaterialOnly": 0.0,
                "Labor": 0.0,
                "MiscCharges": 0.0,
                "InvoiceTotal": 0.0,
                "MiscTax": 0.0,
                "RecycleFee": 0.0,
                "TotalPaid": 0.0,
                "Balance": 0.0,
                "DiscountRate": 0.0,
                "DiscountAmount": 0.0,
                "ApplyRecycleFee": False,
                "Attachements": None,
                "PendingAttachments": None,
                "Order": None,
                "LockInfo": None,
                "Message": None,
                "Lines": [
                    {
                        "productId": "213322",
                        "colorId": 2133,
                        "quantity": 1,
                        "priceLevel": "Price10"
                    }
                ]
            },
            "products": None
        }

        try:
            result = api.create_job(payload)
            print("Order creation result:")
            print(result)
        except Exception as e:
            print(f"Error creating order: {e}") 
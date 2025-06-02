import os
from datetime import datetime
from app import app  # Import the Flask app
from utils.rfms_api import RfmsApi

if __name__ == "__main__":
    with app.app_context():
        base_url = "https://api.rfms.online"
        store_code = os.getenv("RFMS_STORE_CODE")
        username = os.getenv("RFMS_USERNAME")
        api_key = os.getenv("RFMS_API_KEY")

        api = RfmsApi(base_url, store_code, username, api_key)
        api.ensure_session()

        payload = {
            "category": "Order",
            "username": "zoran.vekic",
            "poNumber": "987654",
            "soldTo": {
                "customerId": 2
            },
            "shipTo": {
                "customerId": 1745
            },
            "dateEntered": datetime.now().strftime("%Y-%m-%d"),
            "miscCharges": 1000.00,
            "note": "Order created via API for CRM integration.",
            "workOrderNote": "This is a test order for Sold To 2 and Ship To 1745.",
            "customerType": "INSURANCE",
            "userOrderType": 12,
            "serviceType": 9,
            "contractType": 2,
            "salesPerson1": "ZORAN VEKIC",
            "store": 1,
            "installStore": 1,
            "isWebOrder": False
        }

        try:
            result = api.create_job(payload)
            print("Order creation result:")
            print(result)
        except Exception as e:
            print(f"Error creating order: {e}") 
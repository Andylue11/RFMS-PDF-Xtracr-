import os
from utils.rfms_api import RfmsApi
from app import app

# Use a real PO number from a test PDF
TEST_PO_NUMBER = "PO23218"

# Load RFMS API credentials from environment variables
BASE_URL = os.getenv('RFMS_BASE_URL')
STORE_CODE = os.getenv('RFMS_STORE_CODE')
USERNAME = os.getenv('RFMS_USERNAME')
API_KEY = os.getenv('RFMS_API_KEY')

def main():
    print(f"Testing /v2/order/find for PO number: {TEST_PO_NUMBER}")
    with app.app_context():
        api = RfmsApi(BASE_URL, STORE_CODE, USERNAME, API_KEY)
        try:
            api.ensure_session()
        except Exception as e:
            print(f"Failed to establish session: {e}")
        result = api.find_order_by_po_number(TEST_PO_NUMBER)
        print("API response:", result)

if __name__ == "__main__":
    main() 
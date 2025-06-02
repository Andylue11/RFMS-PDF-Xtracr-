import os
from dotenv import load_dotenv
from utils.rfms_api import RfmsApi
import logging
from app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rfms_connection():
    """Test RFMS API connection and customer creation workflow."""
    # Load environment variables
    load_dotenv('.env-test')
    
    # Initialize RFMS API client
    api = RfmsApi(
        base_url=os.getenv('RFMS_BASE_URL'),
        store_code=os.getenv('RFMS_STORE_CODE'),
        username=os.getenv('RFMS_USERNAME'),
        api_key=os.getenv('RFMS_API_KEY')
    )
    
    try:
        # Test 1: Check API status
        logger.info("Testing RFMS API connection...")
        status = api.check_status()
        logger.info(f"API Status: {status}")
        
        # Test 2: Create a test customer
        logger.info("\nTesting customer creation...")
        test_customer = {
            "customerType": "INSURANCE",
            "entryType": "Customer",
            "customerAddress": {
                "lastName": "Doe",
                "firstName": "Test1",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "NSW",
                "postalCode": "2000",
                "country": "Australia"
            },
            "shipToAddress": {
                "lastName": "Doe",
                "firstName": "John",
                "address1": "123 Test St",
                "city": "Test City",
                "state": "NSW",
                "postalCode": "2000",
                "country": "Australia"
            },
            "phone1": "0412345678",
            "email": "test@example.com",
            "taxStatus": "Tax",
            "taxMethod": "SalesTax",
            "storeNumber": "49",
            "CustomerFirstName": "Test1",
            "CustomerLastName": "Doe",
            "CustomerAddress1": "123 Test St",
            "CustomerAddress2": "",
            "CustomerCity": "Test City",
            "CustomerState": "NSW",
            "CustomerPostalCode": "2000",
            "CustomerCounty": "",
            "ShipToFirstName": "John",
            "ShipToLastName": "Doe",
            "ShipToAddress1": "123 Test St",
            "ShipToAddress2": "",
            "ShipToCity": "Test City",
            "ShipToState": "NSW",
            "ShipToPostalCode": "2000",
            "ShipToCounty": "",
            "Phone2": "",
            "Phone3": "",
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": 1
        }
        
        logger.info("Attempting to create customer...")
        result = api.create_customer(test_customer)
        logger.info(f"Customer created successfully: {result}")
        logger.info(f"API Response: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        success = test_rfms_connection()
        if success:
            logger.info("All tests completed successfully!")
        else:
            logger.error("Tests failed!") 
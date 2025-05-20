import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"test_customer_id_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def test_customer_id_search():
    """Test customer ID search functionality."""
    base_url = "http://localhost:5000"
    test_ids = ["1324", "1593", "718"]  # IDs we know exist from previous search
    
    logger.info("Starting customer ID search tests")
    
    for customer_id in test_ids:
        logger.info(f"\nTesting customer ID: {customer_id}")
        try:
            response = requests.get(f"{base_url}/api/customers/search?term={customer_id}")
            logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {data}")
                
                if data:
                    # Validate the response structure
                    required_fields = [
                        'id', 'customer_source_id', 'name', 'first_name', 'last_name',
                        'address1', 'city', 'state', 'zip_code', 'phone', 'email'
                    ]
                    
                    customer = data[0]  # Should be a list with one customer
                    missing_fields = [field for field in required_fields if field not in customer]
                    
                    if missing_fields:
                        logger.error(f"Missing required fields: {missing_fields}")
                    else:
                        logger.info("Result structure validation passed")
                else:
                    logger.warning(f"No customer found with ID: {customer_id}")
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error testing customer ID {customer_id}: {str(e)}")

if __name__ == "__main__":
    test_customer_id_search() 
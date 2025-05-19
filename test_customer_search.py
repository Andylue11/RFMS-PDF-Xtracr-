import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"test_customer_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:5000"  # Change this if your app runs on a different port
TEST_SEARCH_TERMS = [
    "smith",  # Common name for fuzzy search
    "12345",  # Test numeric ID search
    "test",   # Test no results case
    ""        # Test empty search
]

def test_customer_search():
    """Test the customer search functionality."""
    logger.info("Starting customer search tests")
    
    for search_term in TEST_SEARCH_TERMS:
        logger.info(f"\nTesting search term: '{search_term}'")
        
        try:
            # Make the API request
            response = requests.get(
                f"{BASE_URL}/api/customers/search",
                params={"term": search_term}
            )
            
            # Log the response status
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if the response is valid JSON
            try:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)}")
                
                # Validate response structure
                if isinstance(data, list):
                    logger.info(f"Found {len(data)} results")
                    
                    # If we have results, validate their structure
                    if data:
                        first_result = data[0]
                        required_fields = [
                            'id', 'customer_source_id', 'name', 'first_name', 
                            'last_name', 'business_name', 'address1', 'city', 
                            'state', 'zip_code', 'phone', 'email'
                        ]
                        
                        missing_fields = [field for field in required_fields if field not in first_result]
                        if missing_fields:
                            logger.error(f"Missing required fields in result: {missing_fields}")
                        else:
                            logger.info("Result structure validation passed")
                else:
                    logger.error("Response is not a list as expected")
                    
            except json.JSONDecodeError:
                logger.error("Response is not valid JSON")
                logger.error(f"Response content: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            
    logger.info("\nCustomer search tests completed")

if __name__ == "__main__":
    test_customer_search() 
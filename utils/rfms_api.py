import requests
import logging
import json
import os
import base64
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

class RfmsApi:
    """
    Client for interacting with the RFMS API v2.
    
    This class handles authentication and provides methods for various API endpoints.
    """
    
    def __init__(self, base_url=None, store_code=None, api_key=None):
        """
        Initialize the RFMS API client.
        
        Args:
            base_url (str): The base URL for the RFMS API
            store_code (str): The store code for authentication
            api_key (str): The API key for authentication
        """
        self.base_url = base_url or os.getenv('RFMS_BASE_URL', 'https://api.rfms.online')
        self.store_code = store_code or os.getenv('RFMS_STORE_CODE')
        self.api_key = api_key or os.getenv('RFMS_API_KEY')
        self.session_token = None
        self.session_expiry = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.timeout = 10
        self.max_retries = 2
        self.auth = None  # Will store the current auth tuple
        
        if not self.store_code or not self.api_key:
            raise ValueError("RFMS_STORE_CODE and RFMS_API_KEY environment variables must be set")
        
        logger.info(f"Initialized RFMS API client for store: {self.store_code}")
    
    def ensure_session(self):
        """
        Ensure that we have a valid session token for API calls.
        Only gets a new session if we don't have one or if the current one is expired.
        
        Returns:
            bool: True if session is valid, False otherwise
        """
        # If we have a valid session token and it's not expired, use it
        if self.session_token and self.session_expiry and datetime.now() < self.session_expiry:
            self.auth = (self.store_code, self.session_token)
            return True
        
        # Get a new session
        return self.get_session()
    
    def get_session(self):
        """
        Get a new session token from the RFMS API.
        Initial auth uses store code and API key, then uses store code and session token.
        
        Returns:
            bool: True if successful, False otherwise
        """
        endpoint = f"{self.base_url}/v2/Session/Begin"
        
        try:
            logger.info(f"Getting new session token from {endpoint}")
            logger.info(f"Using store_code: {self.store_code}")
            
            # Initial auth with store code and API key
            auth = (self.store_code, self.api_key)
            
            response = requests.post(
                endpoint, 
                headers=self.headers,
                auth=auth,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authorized') and data.get('sessionToken'):
                    self.session_token = data['sessionToken']
                    self.session_expiry = data.get('sessionExpires')
                    logger.info(f"Session token obtained: {self.session_token[:8]}...")
                    logger.info(f"Session expires: {self.session_expiry}")
                    
                    # Set up auth for future requests using store code as username and session token as password
                    self.auth = (self.store_code, self.session_token)
                    return True
                else:
                    logger.error("Session token not found in response or not authorized")
                    logger.error(f"Response: {data}")
                    return False
            else:
                logger.error(f"Failed to get session token. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error getting session token: {str(e)}")
            return False
    
    def execute_request(self, method, url, payload=None, retry_count=0):
        """
        Execute an API request with retry logic and error handling.
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            url (str): Request URL
            payload (dict): Request payload (for POST/PUT)
            retry_count (int): Current retry count
            
        Returns:
            dict: Response data if successful
            
        Raises:
            Exception: If request fails after all retries
        """
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        
        try:
            logger.debug(f"Executing {method} request to {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, auth=self.auth, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=payload, auth=self.auth, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=payload, auth=self.auth, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, auth=self.auth, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check for successful response
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response from {url}")
                    raise Exception("Invalid JSON response from API")
            
            # Handle unauthorized response (401) by getting a new session and retrying
            elif response.status_code == 401 and retry_count < self.max_retries:
                logger.warning("Session expired or unauthorized, requesting new session")
                self.session_token = None
                self.session_expiry = None
                return self.execute_request(method, url, payload, retry_count + 1)
            
            # Handle other errors
            else:
                error_message = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_message += f": {error_data['error']}"
                except:
                    error_message += f": {response.text}"
                
                logger.error(error_message)
                raise Exception(error_message)
        
        except Exception as e:
            logger.error(f"Error executing request: {str(e)}")
            raise
    
    def check_status(self):
        """
        Check if the RFMS API is available.
        
        Returns:
            str: 'online' if API is available, 'offline' otherwise
        """
        # Attempt to connect to the API to determine real status
        url = f"{self.base_url}/v2/Session/Begin"
        
        try:
            # Initial auth with store code and API key
            auth = (self.store_code, self.api_key)
            
            response = requests.post(
                url, 
                headers=self.headers,
                auth=auth,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('authorized') and data.get('sessionToken'):
                    # Store the session token for future use
                    self.session_token = data['sessionToken']
                    self.session_expiry = data.get('sessionExpires')
                    self.auth = (self.store_code, self.session_token)
                    return 'online'
            
            logger.warning(f"API connection failed with status code: {response.status_code}")
            return 'offline'
                
        except Exception as e:
            logger.error(f"Error checking API status: {str(e)}")
            return 'offline'
    
    def find_customers(self, search_term):
        """
        Find customers using the advanced search endpoint.
        
        Args:
            search_term (str): The search term to find customers
            
        Returns:
            list: List of customer objects matching the search term
        """
        logger.info(f"Finding customers with search term: {search_term}")
        
        # Use advanced search endpoint for better search capabilities
        url = f"{self.base_url}/v2/customers/find/advanced"
        
        # Prepare advanced search parameters with more flexible options
        search_params = {
            "searchText": search_term,
            "stores": [self.store_code],  # Search in current store
            "activeOnly": False,  # Include inactive customers
            "includeCustomers": True,
            "includeProspects": True,  # Include prospects
            "includeInactive": True,  # Include inactive customers
            "startIndex": 0,
            "maxResults": 50  # Limit results to prevent overwhelming response
        }
        
        try:
            # Ensure we have a valid session
            if not self.ensure_session():
                logger.error("Failed to establish session for customer search")
                return []
            
            # Make the request with proper headers
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-API-Key': self.api_key
            }
            
            # Use store code as username and session token as password
            auth = (self.store_code, self.session_token)
            
            response = requests.post(
                url,
                headers=headers,
                auth=auth,
                json=search_params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    customers = data.get("result", [])
                    logger.info(f"Found {len(customers)} customers for search term: {search_term}")
                    return self._format_customer_list(customers)
                else:
                    logger.warning(f"No customers found for search term: {search_term}")
                    return []
            else:
                logger.error(f"Failed to search customers. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error finding customers: {str(e)}")
            return []
    
    def find_customer_by_id(self, customer_id):
        """
        Find a customer by ID using the customer endpoint.
        
        Args:
            customer_id (str): The customer ID to search for
            
        Returns:
            list: List containing the customer object if found
        """
        url = f"{self.base_url}/v2/customer/{customer_id}"
        
        try:
            logger.info(f"Finding customer by ID: {customer_id}")
            data = self.execute_request('GET', url)
            
            if not data or "result" not in data:
                logger.warning(f"No customer found with ID: {customer_id}")
                return []
            
            customer = data.get('result', {})
            if customer:
                # Format the customer data according to the API response structure
                formatted_customer = {
                    'id': customer.get('customerId', ''),
                    'customer_source_id': customer.get('customerId', ''),
                    'name': f"{customer.get('customerAddress', {}).get('firstName', '')} {customer.get('customerAddress', {}).get('lastName', '')}".strip(),
                    'first_name': customer.get('customerAddress', {}).get('firstName', ''),
                    'last_name': customer.get('customerAddress', {}).get('lastName', ''),
                    'business_name': customer.get('customerAddress', {}).get('businessName', ''),
                    'address1': customer.get('customerAddress', {}).get('address1', ''),
                    'address2': customer.get('customerAddress', {}).get('address2', ''),
                    'city': customer.get('customerAddress', {}).get('city', ''),
                    'state': customer.get('customerAddress', {}).get('state', ''),
                    'zip_code': customer.get('customerAddress', {}).get('postalCode', ''),
                    'phone': customer.get('phone1', ''),
                    'email': customer.get('email', ''),
                    'customer_type': customer.get('customerType', ''),
                    'tax_status': customer.get('taxStatus', ''),
                    'tax_method': customer.get('taxMethod', ''),
                    'preferred_salesperson1': customer.get('preferredSalesperson1', ''),
                    'preferred_salesperson2': customer.get('preferredSalesperson2', ''),
                    'store_number': customer.get('storeNumber', ''),
                    'internal_notes': customer.get('notes', '')
                }
                return [formatted_customer]
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding customer by ID: {str(e)}")
            return []
    
    def find_customer_by_name(self, name):
        """
        Find customers by name, supporting partial matching.
        
        Args:
            name (str): The customer name to search for
            
        Returns:
            list: List of customer objects matching the name
        """
        url = f"{self.base_url}/api/v2/customers/find"
        
        # According to documentation, use searchText for name-based search
        payload = {
            "searchText": name,
            "includeCustomers": True,
            "includeProspects": False,
            "includeInactive": False,
            "startIndex": 0
        }
        
        try:
            logger.info(f"Finding customers by name: {name}")
            data = self.execute_request('POST', url, payload)
            
            customers = data.get('result', {}).get('customers', [])
            
            if customers:
                # Format each customer for UI display
                formatted_customers = []
                for customer in customers:
                    formatted_customers.append({
                        'id': customer.get('customerId', ''),
                        'name': customer.get('name', ''),
                        'address': f"{customer.get('address1', '')}, {customer.get('city', '')}, {customer.get('state', '')} {customer.get('postalCode', '')}",
                        'phone': customer.get('phone', ''),
                        'email': customer.get('email', '')
                    })
                return formatted_customers
            
            # No customers found
            logger.warning(f"No customers found with name: {name}")
            return []
            
        except Exception as e:
            logger.error(f"Error finding customers by name: {str(e)}")
            return []
    
    def get_customer(self, customer_id):
        """
        Get a customer by ID using the RFMS API.
        Uses GET request with store code and session token authentication.
        
        Args:
            customer_id (str): The customer ID to retrieve
            
        Returns:
            dict: Customer object if found, None otherwise
        """
        logger.info(f"Getting customer with ID: {customer_id}")
        
        url = f"{self.base_url}/v2/customer/{customer_id}"
        
        try:
            # Ensure we have a valid session
            if not self.ensure_session():
                logger.error("Failed to establish session for customer retrieval")
                return None
            
            # Make the request with exact headers
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Use store code as username and session token as password
            auth = (self.store_code, self.session_token)
            
            response = requests.get(
                url,
                headers=headers,
                auth=auth,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    customer = data.get("result", {})
                    logger.info(f"Successfully retrieved customer: {customer.get('customerId', '')}")
                    return self._format_customer(customer)
                else:
                    logger.warning(f"No customer found with ID: {customer_id}")
                    return None
            else:
                logger.error(f"Failed to get customer. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting customer: {str(e)}")
            return None
    
    def _format_customer(self, customer):
        """
        Format a single customer object from the API response.
        
        Args:
            customer (dict): Raw customer data from API
            
        Returns:
            dict: Formatted customer object
        """
        return {
            'id': customer.get('customerId', ''),
            'customer_source_id': customer.get('customerId', ''),
            'name': f"{customer.get('customerAddress', {}).get('firstName', '')} {customer.get('customerAddress', {}).get('lastName', '')}".strip(),
            'first_name': customer.get('customerAddress', {}).get('firstName', ''),
            'last_name': customer.get('customerAddress', {}).get('lastName', ''),
            'business_name': customer.get('customerAddress', {}).get('businessName', ''),
            'address1': customer.get('customerAddress', {}).get('address1', ''),
            'address2': customer.get('customerAddress', {}).get('address2', ''),
            'city': customer.get('customerAddress', {}).get('city', ''),
            'state': customer.get('customerAddress', {}).get('state', ''),
            'zip_code': customer.get('customerAddress', {}).get('postalCode', ''),
            'phone': customer.get('phone1', ''),
            'email': customer.get('email', ''),
            'customer_type': customer.get('customerType', ''),
            'tax_status': customer.get('taxStatus', ''),
            'tax_method': customer.get('taxMethod', ''),
            'preferred_salesperson1': customer.get('preferredSalesperson1', ''),
            'preferred_salesperson2': customer.get('preferredSalesperson2', ''),
            'store_number': customer.get('storeNumber', '1'),  # Default to store 1
            'internal_notes': customer.get('notes', ''),
            'ship_to': {
                'name': f"{customer.get('shipToAddress', {}).get('firstName', '')} {customer.get('shipToAddress', {}).get('lastName', '')}".strip(),
                'first_name': customer.get('shipToAddress', {}).get('firstName', ''),
                'last_name': customer.get('shipToAddress', {}).get('lastName', ''),
                'business_name': customer.get('shipToAddress', {}).get('businessName', ''),
                'address1': customer.get('shipToAddress', {}).get('address1', ''),
                'address2': customer.get('shipToAddress', {}).get('address2', ''),
                'city': customer.get('shipToAddress', {}).get('city', ''),
                'state': customer.get('shipToAddress', {}).get('state', ''),
                'zip_code': customer.get('shipToAddress', {}).get('postalCode', ''),
                'county': customer.get('shipToAddress', {}).get('county', '')
            }
        }
    
    def create_customer(self, customer_data):
        """
        Create a new customer in RFMS.
        
        Args:
            customer_data (dict): Customer data
            
        Returns:
            dict: Created customer object
        """
        url = f"{self.base_url}/api/v2/Customer"
        
        # Perform data validation before sending
        required_fields = ['business_name', 'first_name', 'last_name', 'address1', 'city', 'state']
        missing_fields = [field for field in required_fields if not customer_data.get(field) and not customer_data.get('customer_name')]
        
        if missing_fields and not customer_data.get('customer_name'):
            raise ValueError(f"Missing required customer data: {', '.join(missing_fields)}")
        
        # Prepare payload according to RFMS API format
        payload = {
            "customer": {
                "name": customer_data.get('business_name', '') or customer_data.get('customer_name', ''),
                "salutation": customer_data.get('salutation', ''),
                "firstName": customer_data.get('first_name', ''),
                "lastName": customer_data.get('last_name', ''),
                "address1": customer_data.get('address1', ''),
                "city": customer_data.get('city', ''),
                "state": customer_data.get('state', ''),
                "postalCode": customer_data.get('zip_code', ''),
                "country": customer_data.get('country', 'Australia'),
                "phone": customer_data.get('phone', ''),
                "email": customer_data.get('email', ''),
                "type": "BUILDERS",  # As per your requirements
                "activeDate": datetime.now().strftime("%Y-%m-%d"),
                "storeCode": self.store_code
            }
        }
        
        try:
            data = self.execute_request('POST', url, payload)
            return data.get('result', {}).get('customer', {})
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise Exception(f"Error creating customer: {str(e)}")
    
    def create_quote(self, quote_data):
        """
        Create a new quote in RFMS.
        
        Args:
            quote_data (dict): Quote data
            
        Returns:
            dict: Created quote object
        """
        url = f"{self.base_url}/api/v2/Quote"
        
        # Validate required fields
        if not quote_data.get('customer_id'):
            raise ValueError("Missing required field: customer_id")
            
        # Prepare payload according to RFMS API format
        payload = {
            "quote": {
                "customerId": quote_data.get('customer_id'),
                "opportunityName": quote_data.get('opportunity_name', 'New Opportunity'),
                "storeCode": self.store_code,
                "salesPerson": quote_data.get('sales_person', ''),
                "workOrderNotes": quote_data.get('scope_of_work', ''),
                "billToAddress": {
                    "name": quote_data.get('bill_to_name', ''),
                    "address1": quote_data.get('bill_to_address1', ''),
                    "address2": quote_data.get('bill_to_address2', ''),
                    "city": quote_data.get('bill_to_city', ''),
                    "state": quote_data.get('bill_to_state', ''),
                    "postalCode": quote_data.get('bill_to_zip', ''),
                    "country": quote_data.get('bill_to_country', 'Australia')
                },
                "shipToAddress": {
                    "name": quote_data.get('ship_to_name', ''),
                    "address1": quote_data.get('ship_to_address1', ''),
                    "address2": quote_data.get('ship_to_address2', ''),
                    "city": quote_data.get('ship_to_city', ''),
                    "state": quote_data.get('ship_to_state', ''),
                    "postalCode": quote_data.get('ship_to_zip', ''),
                    "country": quote_data.get('ship_to_country', 'Australia')
                }
            }
        }
        
        try:
            data = self.execute_request('POST', url, payload)
            return data.get('result', {}).get('quote', {})
        except Exception as e:
            logger.error(f"Error creating quote: {str(e)}")
            raise Exception(f"Error creating quote: {str(e)}")
    
    def create_job(self, job_data):
        """
        Create a new job in RFMS.
        
        Args:
            job_data (dict): Job data
            
        Returns:
            dict: Created job object
        """
        try:
            # Ensure required fields are present
            if not all(key in job_data['order'] for key in ['CustomerSeqNum', 'PONumber', 'MiscCharges']):
                raise ValueError("Missing required fields in job data")
            
            # Get session token
            session_token = self.session_token
            if not session_token:
                raise Exception("Failed to get session token")
            
            # Prepare the request
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Use session token for authentication
            auth = (self.store_code, session_token)
            
            # Make the request
            response = requests.post(
                f"{self.base_url}/v2/Order",
                headers=headers,
                auth=auth,
                json=job_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Failed to create job: {response.text}")
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    def add_to_billing_group(self, order_ids):
        """
        Add orders to a billing group.
        
        Args:
            order_ids (list): List of order IDs to add to a billing group
            
        Returns:
            dict: Result of the operation
        """
        url = f"{self.base_url}/api/v2/BillingGroup"
        
        # Validate order_ids
        if not order_ids or not isinstance(order_ids, list) or len(order_ids) < 1:
            raise ValueError("At least one order ID is required")
            
        # Prepare payload
        payload = {
            "orderIds": order_ids
        }
        
        try:
            data = self.execute_request('POST', url, payload)
            return data.get('result', {})
        except Exception as e:
            logger.error(f"Error adding orders to billing group: {str(e)}")
            raise Exception(f"Error adding orders to billing group: {str(e)}")
    
    def find_customers_advanced(self, search_params):
        """
        Advanced customer search with multiple filter options.
        
        Args:
            search_params (dict): Search parameters including:
                - searchText (str): Text to search in customer name
                - stores (list): List of store IDs
                - activeOnly (bool): Filter active customers only
                - dateCreatedFrom (str): Date in YYYY-MM-DD format
                - dateCreatedTo (str): Date in YYYY-MM-DD format
                - lastPurchaseFrom (str): Date in YYYY-MM-DD format
                - lastPurchaseTo (str): Date in YYYY-MM-DD format
                - customerTypes (list): List of customer types
                - businessSoldName (str): Business name for sold to
                - businessShipName (str): Business name for ship to
                
        Returns:
            list: List of matching customer objects
        """
        url = f"{self.base_url}/v2/customers/find/advanced"
        
        try:
            response_data = self.execute_request('POST', url, search_params)
            
            if not response_data or "result" not in response_data:
                logger.warning("No customers found in advanced search")
                return []
            
            customers = response_data.get("result", [])
            return self._format_customer_list(customers)
            
        except Exception as e:
            logger.error(f"Error in advanced customer search: {str(e)}")
            return []
    
    def get_customer_values(self):
        """
        Get available customer values for dropdowns and filters.
        
        Returns:
            dict: Available values for:
                - customerType
                - entryType
                - taxStatus
                - taxMethod
                - preferredSalesperson1
                - preferredSalesperson2
                - stores
        """
        url = f"{self.base_url}/v2/customers"
        
        try:
            response_data = self.execute_request('GET', url)
            
            if not response_data:
                logger.warning("Failed to get customer values")
                return {}
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting customer values: {str(e)}")
            return {}
    
    def _format_customer_list(self, customers):
        """
        Helper method to format customer data consistently.
        
        Args:
            customers (list): List of customer objects from API
            
        Returns:
            list: Formatted customer objects
        """
        formatted_customers = []
        
        for customer in customers:
            formatted_customer = {
                'id': customer.get('customerSourceId', ''),
                'customer_source_id': customer.get('customerSourceId', ''),
                'name': customer.get('customerName', ''),
                'first_name': customer.get('customerFirstName', ''),
                'last_name': customer.get('customerLastName', ''),
                'business_name': customer.get('customerBusinessName', ''),
                'address1': customer.get('customerAddress', ''),
                'address2': customer.get('customerAddress2', ''),
                'city': customer.get('customerCity', ''),
                'state': customer.get('customerState', ''),
                'zip_code': customer.get('customerZIP', ''),
                'phone': customer.get('customerPhone', ''),
                'email': customer.get('customerEmail', ''),
                'customer_type': customer.get('customerType', ''),
                'tax_status': customer.get('taxStatus', ''),
                'tax_method': customer.get('taxMethod', ''),
                'preferred_salesperson1': customer.get('preferredSalesperson1', ''),
                'preferred_salesperson2': customer.get('preferredSalesperson2', ''),
                'store_number': customer.get('defaultStore', ''),
                'internal_notes': customer.get('internalNotes', ''),
                'ship_to': {
                    'name': customer.get('shipToName', ''),
                    'first_name': customer.get('shipToFirstName', ''),
                    'last_name': customer.get('shipToLastName', ''),
                    'business_name': customer.get('shipToBusinessName', ''),
                    'address1': customer.get('shipToAddress', ''),
                    'address2': customer.get('shipToAddress2', ''),
                    'city': customer.get('shipToCity', ''),
                    'state': customer.get('shipToState', ''),
                    'zip_code': customer.get('shipToZIP', ''),
                    'county': customer.get('shipToCounty', '')
                }
            }
            formatted_customers.append(formatted_customer)
        
        return formatted_customers 
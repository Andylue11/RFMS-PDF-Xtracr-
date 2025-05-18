import requests
import logging
import json
import os
from datetime import datetime, timedelta
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

class RfmsApi:
    """
    Client for interacting with the RFMS API v2.
    
    This class handles authentication and provides methods for various API endpoints.
    """
    
    def __init__(self, base_url, store_code, username, api_key):
        """
        Initialize the RFMS API client.
        
        Args:
            base_url (str): The base URL for the RFMS API
            store_code (str): The store code for authentication
            username (str): The username for authentication
            api_key (str): The API key for authentication
        """
        self.base_url = base_url
        self.store_code = store_code
        self.username = username
        self.api_key = api_key
        self.session_id = None
        self.session_expiry = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        # Default timeout for requests (10 seconds)
        self.timeout = 10
        # Number of retries for failed requests
        self.max_retries = 2
    
    def ensure_session(self):
        """
        Ensure that we have a valid session ID for API calls.
        
        If there is no session ID or it has expired, get a new one.
        
        Returns:
            bool: True if session is valid, False otherwise
        """
        # Check if we have a session and it's not expired
        if self.session_id and self.session_expiry and datetime.now() < self.session_expiry:
            return True
        
        # Get a new session
        return self.get_session()
    
    def get_session(self):
        """
        Get a new session ID from the RFMS API.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Try multiple endpoint formats to find the correct one
        endpoints = [
            f"{self.base_url}/v2/session",
            f"{self.base_url}/api/v2/Session"
        ]
        
        # Use username/api_key authentication
        payload = {
            "storeCode": self.store_code,
            "userName": self.username,
            "password": self.api_key
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Try each endpoint until successful or all fail
        for endpoint in endpoints:
            try:
                logger.info(f"Attempting to connect to RFMS API at {endpoint}")
                logger.info(f"With credentials: Username: {self.username}, StoreCode: {self.store_code}")
                
                response = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
                logger.info(f"RFMS API response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_id = data.get('sessionId')
                    
                    if not self.session_id:
                        logger.error("Session ID not found in response")
                        continue
                    
                    # Set session expiry to 1 hour from now
                    self.session_expiry = datetime.now() + timedelta(hours=1)
                    
                    # Update headers with session ID
                    self.headers['Session-ID'] = self.session_id
                    
                    logger.info(f"Successfully obtained RFMS API session: {self.session_id}")
                    return True
            
            except Timeout:
                logger.error(f"Timeout connecting to RFMS API at {endpoint}")
            except ConnectionError:
                logger.error(f"Connection error connecting to RFMS API at {endpoint}")
            except Exception as e:
                logger.error(f"Error getting RFMS API session from {endpoint}: {str(e)}")
        
        # All endpoints failed
        logger.error("All session endpoints failed")
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
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=payload, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check for successful response
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON response from {url}")
                    raise Exception("Invalid JSON response from API")
            
            # Handle session expiry (401) by getting a new session and retrying
            elif response.status_code == 401 and retry_count < self.max_retries:
                logger.warning("Session expired, requesting new session")
                self.session_id = None
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
        
        except Timeout:
            if retry_count < self.max_retries:
                logger.warning(f"Request timeout, retrying ({retry_count + 1}/{self.max_retries})")
                return self.execute_request(method, url, payload, retry_count + 1)
            else:
                logger.error("Request timed out after all retries")
                raise Exception("API request timed out after multiple attempts")
        
        except ConnectionError:
            if retry_count < self.max_retries:
                logger.warning(f"Connection error, retrying ({retry_count + 1}/{self.max_retries})")
                return self.execute_request(method, url, payload, retry_count + 1)
            else:
                logger.error("Connection failed after all retries")
                raise Exception("API connection failed after multiple attempts")
        
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
        url = f"{self.base_url}/api/v2/Session"
        
        try:
            response = requests.post(
                url, 
                headers=self.headers, 
                json={
                    "storeCode": self.store_code,
                    "userName": self.username,
                    "password": self.api_key
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return 'online'
            else:
                logger.warning(f"API connection failed with status code: {response.status_code}")
                return 'offline'
        
        except Timeout:
            logger.error("API status check timed out")
            return 'offline'
        except ConnectionError:
            logger.error("API connection error during status check")
            return 'offline'
        except Exception as e:
            logger.error(f"Error checking API status: {str(e)}")
            return 'offline'
    
    def find_customers(self, search_term):
        """
        Search for customers by name or custom ID.
        
        Args:
            search_term (str): The search term for finding customers
            
        Returns:
            list: List of customer objects matching the search term
        """
        logger.info(f"Finding customers with search term: {search_term}")
        
        # Determine if search_term is numeric (likely a CustomerID) or text
        if search_term.isdigit():
            logger.info("Numeric search term detected, treating as CustomerID")
            return self.find_customer_by_id(search_term)
        else:
            logger.info("Text search term detected, treating as customer name")
            return self.find_customer_by_name(search_term)
    
    def find_customer_by_id(self, customer_id):
        """
        Find a customer by ID.
        
        Args:
            customer_id (str): The customer ID to search for
            
        Returns:
            list: List containing the customer object if found
        """
        url = f"{self.base_url}/api/v2/Customer/{customer_id}"
        
        try:
            logger.info(f"Finding customer by ID: {customer_id}")
            data = self.execute_request('GET', url)
            
            customer = data.get('result', {}).get('customer', {})
            if customer:
                # Format the customer data for UI display
                formatted_customer = {
                    'id': customer.get('customerId', ''),
                    'name': customer.get('name', ''),
                    'address': f"{customer.get('address1', '')}, {customer.get('city', '')}, {customer.get('state', '')} {customer.get('postalCode', '')}",
                    'phone': customer.get('phone', ''),
                    'email': customer.get('email', '')
                }
                return [formatted_customer]
            
            # No customer found
            logger.warning(f"No customer found with ID: {customer_id}")
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
        Get a customer by ID.
        
        Args:
            customer_id (str): The customer ID to retrieve
            
        Returns:
            dict: Customer object
        """
        url = f"{self.base_url}/api/v2/Customer/{customer_id}"
        
        try:
            data = self.execute_request('GET', url)
            return data.get('result', {}).get('customer', {})
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {str(e)}")
            raise Exception(f"Error getting customer {customer_id}: {str(e)}")
    
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
        Create a new job (order) in RFMS.
        
        Args:
            job_data (dict): Job data
            
        Returns:
            dict: Created job object
        """
        url = f"{self.base_url}/api/v2/Order"
        
        # Validate required fields
        if not job_data.get('customer_id'):
            raise ValueError("Missing required field: customer_id")
            
        # Prepare payload according to RFMS API format
        payload = {
            "order": {
                "customerId": job_data.get('customer_id'),
                "quoteId": job_data.get('quote_id'),  # Optional, if converting a quote
                "opportunityName": job_data.get('job_name', 'New Job'),
                "poNumber": job_data.get('po_number', ''),
                "storeCode": self.store_code,
                "salesPerson": job_data.get('sales_person', ''),
                "workOrderNotes": job_data.get('description_of_works', ''),
                "billToAddress": {
                    "name": job_data.get('bill_to_name', ''),
                    "address1": job_data.get('bill_to_address1', ''),
                    "address2": job_data.get('bill_to_address2', ''),
                    "city": job_data.get('bill_to_city', ''),
                    "state": job_data.get('bill_to_state', ''),
                    "postalCode": job_data.get('bill_to_zip', ''),
                    "country": job_data.get('bill_to_country', 'Australia')
                },
                "shipToAddress": {
                    "name": job_data.get('ship_to_name', ''),
                    "address1": job_data.get('ship_to_address1', ''),
                    "address2": job_data.get('ship_to_address2', ''),
                    "city": job_data.get('ship_to_city', ''),
                    "state": job_data.get('ship_to_state', ''),
                    "postalCode": job_data.get('ship_to_zip', ''),
                    "country": job_data.get('ship_to_country', 'Australia')
                }
            }
        }
        
        try:
            data = self.execute_request('POST', url, payload)
            return data.get('result', {}).get('order', {})
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise Exception(f"Error creating job: {str(e)}")
    
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
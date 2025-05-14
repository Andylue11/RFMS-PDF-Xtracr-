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
        self.session_token = None
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
        Ensure that we have a valid session token for API calls.
        
        If there is no session token or it has expired, get a new one.
        
        Returns:
            bool: True if session is valid, False otherwise
        """
        # Check if we have a session and it's not expired
        if self.session_token and self.session_expiry and datetime.now() < self.session_expiry:
            return True
        
        # Get a new session
        return self.get_session()
    
    def get_session(self):
        """
        Get a new session token from the RFMS API.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # According to updated docs, use this endpoint
        endpoint = f"{self.base_url}/v2/Session/Begin"
        
        # Set up basic auth with store_code as username and API key as password
        # (no need to use the regular username/password)
        auth = (self.store_code, self.api_key)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            logger.info(f"Attempting to connect to RFMS API at {endpoint}")
            logger.info(f"With store code: {self.store_code}")
            
            response = requests.post(endpoint, headers=headers, auth=auth, timeout=self.timeout)
            logger.info(f"RFMS API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get('sessionToken')
                
                if not self.session_token:
                    logger.error("Session token not found in response")
                    return False
                
                # Set session expiry based on returned value or default to 20 minutes
                if 'sessionExpires' in data:
                    try:
                        # Parse the expiry date from the response
                        expiry_str = data.get('sessionExpires')
                        self.session_expiry = datetime.strptime(expiry_str, "%a, %d %b %Y %H:%M:%S %Z")
                    except Exception as e:
                        logger.warning(f"Could not parse session expiry: {str(e)}")
                        # Default to 20 minutes from now as mentioned in documentation
                        self.session_expiry = datetime.now() + timedelta(minutes=20)
                else:
                    # Default to 20 minutes from now as mentioned in documentation
                    self.session_expiry = datetime.now() + timedelta(minutes=20)
                
                # For future requests, use store_code as username and session_token as password
                self.auth = (self.store_code, self.session_token)
                
                logger.info(f"Successfully obtained RFMS API session token: {self.session_token}")
                logger.info(f"Session expires at: {self.session_expiry}")
                return True
            
            else:
                logger.error(f"Failed to get session token. Status code: {response.status_code}")
                try:
                    logger.error(f"Response: {response.json()}")
                except:
                    logger.error(f"Response text: {response.text}")
                return False
                
        except Timeout:
            logger.error(f"Timeout connecting to RFMS API at {endpoint}")
        except ConnectionError:
            logger.error(f"Connection error connecting to RFMS API at {endpoint}")
        except Exception as e:
            logger.error(f"Error getting RFMS API session from {endpoint}: {str(e)}")
        
        # All attempts failed
        logger.error("Session initialization failed")
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
            
            # Use Basic Auth with store_code:session_token
            headers = self.headers.copy()
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, auth=self.auth, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=payload, auth=self.auth, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=payload, auth=self.auth, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, auth=self.auth, timeout=self.timeout)
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
        url = f"{self.base_url}/v2/Session/Begin"
        
        try:
            # Set up basic auth with store_code as username and api_key as password
            auth = (self.store_code, self.api_key)
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                url, 
                headers=headers,
                auth=auth,
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
        
        # Based on POST to rfms.txt, we need to use this endpoint
        url = f"{self.base_url}/v2/customers/find"
        
        # According to the documentation, use a POST request
        payload = {
            "searchText": search_term,
            "includeCustomers": True,
            "includeProspects": False,
            "includeInactive": False,
            "startIndex": 0
        }
        
        try:
            response_data = self.execute_request('POST', url, payload)
            
            # Check if we got valid results
            if not response_data or "result" not in response_data or not response_data.get("result"):
                logger.warning(f"No customers found for search term: {search_term}")
                return []
            
            customers = response_data.get("result", [])
            formatted_customers = []
            
            # Format the customer data according to the POST to rfms.txt example
            for customer in customers:
                formatted_customer = {
                    'id': customer.get('customerSourceId', ''),  # This will be used as CustomerSeqNum
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
                    'country': customer.get('customerCountry', '')
                }
                formatted_customers.append(formatted_customer)
            
            logger.info(f"Found {len(formatted_customers)} customers for search term: {search_term}")
            return formatted_customers
            
        except Exception as e:
            logger.error(f"Error finding customers: {str(e)}")
            return []
    
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
        url = f"{self.base_url}/v2/Order"
        
        # Validate required fields
        if not job_data.get('sold_to_customer_id'):
            raise ValueError("Missing required field: sold_to_customer_id")
            
        # Prepare payload according to RFMS API format and New job Payload.txt
        payload = {
            "username": job_data.get('salesperson1', 'zoran.vekic'),
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
                "CustomerSource": job_data.get('customer_source', ''),
                "CustomerSeqNum": job_data.get('sold_to_customer_id', ''),  # From documentation: customerID or customerSourceID
                "CustomerUpSeqNum": job_data.get('ship_to_customer_id', job_data.get('sold_to_customer_id', '')),
                "CustomerFirstName": job_data.get('customer_first_name', ''),
                "CustomerLastName": job_data.get('customer_last_name', ''),
                "CustomerAddress1": job_data.get('customer_address1', ''),
                "CustomerAddress2": job_data.get('customer_address2', ''),
                "CustomerCity": job_data.get('customer_city', ''),
                "CustomerState": job_data.get('customer_state', ''),
                "CustomerPostalCode": job_data.get('customer_postal_code', ''),
                "CustomerCounty": job_data.get('customer_county', ''),
                "Phone1": job_data.get('customer_phone', ''),
                "ShipToFirstName": job_data.get('ship_to_first_name', ''),
                "ShipToLastName": job_data.get('ship_to_last_name', ''),
                "ShipToAddress1": job_data.get('ship_to_address1', ''),
                "ShipToAddress2": job_data.get('ship_to_address2', ''),
                "ShipToCity": job_data.get('ship_to_city', ''),
                "ShipToState": job_data.get('ship_to_state', ''),
                "ShipToPostalCode": job_data.get('ship_to_postal_code', ''),
                "ShipToCounty": job_data.get('ship_to_county', ''),
                "Phone2": job_data.get('ship_to_phone', ''),
                "ShipToLocked": False,
                "SalesPerson1": job_data.get('salesperson1', 'ZORAN VEKIC'),
                "SalesPerson2": job_data.get('salesperson2', ''),
                "SalesRepLocked": False,
                "CommisionSplitPercent": 0.0,
                "Store": job_data.get('store_number', 1),
                "Email": job_data.get('email', ''),
                "CustomNote": job_data.get('custom_note', ''),
                "Note": job_data.get('note', ''),
                "WorkOrderNote": job_data.get('description_of_works', ''),
                "PickingTicketNote": None,
                "OrderDate": job_data.get('order_date', datetime.now().strftime('%Y-%m-%d')),
                "MeasureDate": job_data.get('measure_date', ''),
                "PromiseDate": job_data.get('promise_date', ''),
                "PONumber": job_data.get('po_number', ''),
                "CustomerType": job_data.get('customer_type', 'INSURANCE'),
                "JobNumber": job_data.get('job_number', ''),
                "DateEntered": job_data.get('date_entered', datetime.now().strftime('%Y-%m-%d')),
                "DatePaid": None,
                "DueDate": job_data.get('due_date', ''),
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
                "UserOrderType": job_data.get('user_order_type_id', 3),
                "ServiceType": job_data.get('service_type_id', 1),
                "ContractType": job_data.get('contract_type_id', 1),
                "Timeslot": 0,
                "InstallStore": job_data.get('install_store', 1),
                "AgeFrom": None,
                "Completed": None,
                "ReferralAmount": 0.0,
                "ReferralLocked": False,
                "PreAuthorization": None,
                "SalesTax": 0.0,
                "GrandInvoiceTotal": job_data.get('dollar_value', 0.0),
                "MaterialOnly": 0.0,
                "Labor": 0.0,
                "MiscCharges": job_data.get('dollar_value', 0.0),  # As per API Communication document, PO $ value goes here
                "InvoiceTotal": job_data.get('dollar_value', 0.0),
                "MiscTax": 0.0,
                "RecycleFee": 0.0,
                "TotalPaid": 0.0,
                "Balance": job_data.get('dollar_value', 0.0),
                "DiscountRate": 0.0,
                "DiscountAmount": 0.0,
                "ApplyRecycleFee": False,
                "Attachements": None,
                "PendingAttachments": None,
                "Order": None,
                "LockInfo": None,
                "Message": None,
                "Lines": job_data.get('lines', [])
            },
            "products": None
        }
        
        try:
            data = self.execute_request('POST', url, payload)
            if data and 'result' in data:
                return data.get('result', {})
            return data
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
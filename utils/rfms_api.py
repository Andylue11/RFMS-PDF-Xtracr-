import requests
import logging
import json
import os
from datetime import datetime

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
        url = f"{self.base_url}/api/v2/Session"
        
        payload = {
            "storeCode": self.store_code,
            "userName": self.username,
            "apiKey": self.api_key
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.session_id = data.get('sessionId')
            
            # Set session expiry to a reasonable time (e.g., 1 hour from now)
            self.session_expiry = datetime.now().replace(hour=datetime.now().hour + 1)
            
            # Update headers with session ID
            self.headers['Session-ID'] = self.session_id
            
            logger.info("Successfully obtained RFMS API session")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting RFMS API session: {str(e)}")
            return False
    
    def check_status(self):
        """
        Check if the RFMS API is available.
        
        Returns:
            str: 'online' if API is available, 'offline' otherwise
        """
        if self.ensure_session():
            return 'online'
        return 'offline'
    
    def find_customers(self, search_term):
        """
        Search for customers by name or custom ID.
        
        Args:
            search_term (str): The search term for finding customers
            
        Returns:
            list: List of customer objects matching the search term
        """
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        
        url = f"{self.base_url}/api/v2/Customer/Find"
        
        # Determine if search_term is a CustomId or a name
        if search_term.isdigit():
            payload = {"customId": search_term}
        else:
            payload = {"name": search_term}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('customers', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error finding customers: {str(e)}")
            raise Exception(f"Error finding customers: {str(e)}")
    
    def get_customer(self, customer_id):
        """
        Get a customer by ID.
        
        Args:
            customer_id (str): The customer ID to retrieve
            
        Returns:
            dict: Customer object
        """
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        
        url = f"{self.base_url}/api/v2/Customer/{customer_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('customer', {})
        
        except requests.exceptions.RequestException as e:
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
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        
        url = f"{self.base_url}/api/v2/Customer"
        
        # Prepare payload according to RFMS API format
        payload = {
            "customer": {
                "name": customer_data.get('business_name', ''),
                "salutation": customer_data.get('salutation', ''),
                "firstName": customer_data.get('first_name', ''),
                "lastName": customer_data.get('last_name', ''),
                "address1": customer_data.get('address', ''),
                "city": customer_data.get('city', ''),
                "state": customer_data.get('state', ''),
                "postalCode": customer_data.get('zip_code', ''),
                "country": customer_data.get('country', 'USA'),
                "phone": customer_data.get('phone', ''),
                "email": customer_data.get('email', ''),
                "type": "INSURED CUSTOMER",  # As per requirements
                "activeDate": datetime.now().strftime("%Y-%m-%d"),
                "storeCode": self.store_code
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('customer', {})
        
        except requests.exceptions.RequestException as e:
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
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        
        url = f"{self.base_url}/api/v2/Quote"
        
        # Prepare payload according to RFMS API format
        payload = {
            "quote": {
                "customerId": quote_data.get('customer_id'),
                "poNumber": quote_data.get('po_number', ''),
                "storeCode": self.store_code,
                "workOrderNotes": quote_data.get('scope_of_work', ''),
                "lines": [
                    {
                        "lineType": "UNREFERENCED",
                        "description": quote_data.get('scope_of_work', 'Services'),
                        "quantity": 1,
                        "price": quote_data.get('dollar_value', 0),
                        "lineNumber": 1
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('quote', {})
        
        except requests.exceptions.RequestException as e:
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
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        
        url = f"{self.base_url}/api/v2/Order"
        
        # Prepare payload according to RFMS API format
        payload = {
            "order": {
                "customerId": job_data.get('customer_id'),
                "poNumber": job_data.get('po_number', ''),
                "storeCode": self.store_code,
                "workOrderNotes": job_data.get('scope_of_work', ''),
                "orderType": "PO",  # As per requirements
                "lines": [
                    {
                        "lineType": "UNREFERENCED",
                        "description": job_data.get('scope_of_work', 'Services'),
                        "quantity": 1,
                        "price": job_data.get('dollar_value', 0),
                        "lineNumber": 1
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('order', {})
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating job: {str(e)}")
            raise Exception(f"Error creating job: {str(e)}")
    
    def add_to_billing_group(self, order_ids):
        """
        Add orders to a billing group.
        
        Args:
            order_ids (list): List of order IDs to add to the billing group
            
        Returns:
            dict: Result of the operation
        """
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        
        url = f"{self.base_url}/api/v2/BillingGroup"
        
        # Prepare payload according to RFMS API format
        payload = {
            "billingGroup": {
                "storeCode": self.store_code,
                "name": f"BG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "orderIds": order_ids
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return data.get('billingGroup', {})
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating billing group: {str(e)}")
            raise Exception(f"Error creating billing group: {str(e)}") 
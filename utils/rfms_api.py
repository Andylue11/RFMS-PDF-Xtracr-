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
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.timeout = 10
        self.max_retries = 2
        self.auth = None  # Will store the current auth tuple

    def _get_auth(self, for_handshake=False):
        if for_handshake:
            return (self.store_code, self.api_key)
        else:
            return (self.store_code, self.session_token)

    def _get_headers(self, extra_headers=None, include_session=False):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def ensure_session(self):
        """
        Ensure that we have a valid session token for API calls.
        Only gets a new session if we don't have one or if the current one is expired.
        Returns:
            bool: True if session is valid, False otherwise
        """
        now = datetime.now()
        skew = timedelta(seconds=10)
        logger.debug(
            f"[SESSION] Checking session token: {self.session_token}, expiry: {self.session_expiry}, now: {now}"
        )
        if (
            self.session_token
            and self.session_expiry
            and now < self.session_expiry - skew
        ):
            logger.debug(
                f"[SESSION] Reusing existing RFMS API session token: {self.session_token}"
            )
            return True
        logger.info(
            f"[SESSION] Session token missing or expired. Previous token: {self.session_token}, expiry: {self.session_expiry}, now: {now}. Triggering handshake."
        )
        return self.get_session()

    def get_session(self):
        """
        Get a new session token from the RFMS API using Basic Auth.
        Returns:
            bool: True if successful, False otherwise
        """
        url = f"{self.base_url}/v2/Session/Begin"
        headers = self._get_headers(include_session=False)
        auth = self._get_auth(for_handshake=True)
        logger.debug(
            f"[SESSION] get_session called. Current token: {self.session_token}, expiry: {self.session_expiry}, now: {datetime.now()}"
        )
        try:
            logger.info(
                f"Attempting to begin session at {url} with store code {self.store_code}"
            )
            logger.debug(
                f"[RFMS API] Outgoing handshake auth: (username: {auth[0]}, password: {'*' * len(auth[1])})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                url, headers=headers, auth=auth, timeout=self.timeout
            )
            logger.info(f"RFMS API response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("sessionToken")
                self.session_expiry = None
                if not self.session_token:
                    logger.error(
                        f"Session begin succeeded but no sessionToken in response: {data}"
                    )
                    return False
                if "sessionExpires" in data:
                    try:
                        self.session_expiry = datetime.strptime(
                            data["sessionExpires"], "%a, %d %b %Y %H:%M:%S GMT"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse sessionExpires: {data.get('sessionExpires')}, error: {e}"
                        )
                        self.session_expiry = None
                if not self.session_expiry:
                    self.session_expiry = datetime.now() + timedelta(minutes=15)
                logger.info(
                    f"Successfully obtained RFMS API session token: {self.session_token}, expires at: {self.session_expiry}"
                )
                return True
            else:
                logger.error(
                    f"Session begin failed: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error getting RFMS API session: {str(e)}")
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
        logger.info(f"[RFMS API] {method} {url} | Payload: {payload}")
        if not self.ensure_session():
            raise Exception("Failed to establish RFMS API session")
        headers = self._get_headers()
        auth = self._get_auth()
        logger.debug(
            f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
        )
        logger.debug(f"[RFMS API] Outgoing headers: {headers}")
        try:
            logger.debug(f"Executing {method} request to {url}")

            if method.upper() == "GET":
                response = requests.get(
                    url, headers=headers, auth=auth, timeout=self.timeout
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=headers, auth=auth, json=payload, timeout=self.timeout
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=headers, auth=auth, json=payload, timeout=self.timeout
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=headers, auth=auth, timeout=self.timeout
                )
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
                logger.warning(
                    "Session expired or unauthorized, requesting new session"
                )
                self.session_token = None
                self.session_expiry = None
                return self.execute_request(method, url, payload, retry_count + 1)

            # Handle other errors
            else:
                error_message = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
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
        url = f"{self.base_url}/v2/Session/Begin"
        try:
            headers = self._get_headers(include_session=False)
            auth = self._get_auth(for_handshake=True)
            logger.debug(
                f"[RFMS API] Outgoing handshake auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                url, headers=headers, auth=auth, timeout=self.timeout
            )
            if response.status_code == 200:
                return "online"
            else:
                logger.warning(
                    f"API connection failed with status code: {response.status_code}"
                )
                return "offline"
        except Timeout:
            logger.error("API status check timed out")
            return "offline"
        except ConnectionError:
            logger.error("API connection error during status check")
            return "offline"
        except Exception as e:
            logger.error(f"Error checking API status: {str(e)}")
            return "offline"

    def find_customers(self, search_term):
        logger.info(f"Finding customers with search term: {search_term}")
        self.ensure_session()
        url = f"{self.base_url}/v2/customers/find"
        payload = {
            "searchText": search_term,
            "includeCustomers": True,
            "includeProspects": False,
            "includeInactive": False,
            "startIndex": 0,
            "storeNumber": 49,
            "entryType": "Customer",
            "referralType": "standalone",
        }
        try:
            data = self.execute_request("POST", url, payload)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ["customers", "result", "data"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
            return []
        except Exception as e:
            logger.error(f"Error finding customers: {str(e)}")
            return []

    def probe_customers_endpoint(self, search_term):
        self.ensure_session()
        url = f"{self.base_url}/v2/customers"
        payload = {"searchText": search_term}
        try:
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                url, headers=headers, auth=auth, json=payload, timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error probing /v2/customers: {response.text}")
                return response.text
        except Exception as e:
            logger.error(f"Error probing /v2/customers: {str(e)}")
            return str(e)

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
            data = self.execute_request("GET", url)
            logger.info(f"[RAW API RESPONSE] /v2/customer/{{customer_id}}: {data}")
            if not data or "result" not in data:
                logger.warning(f"No customer found with ID: {customer_id}")
                return []
            result = data.get("result", {})
            detail = data.get("detail", {})
            customer_address = result.get("customerAddress", {})

            # Helper to pick the first non-empty field
            def pick_any_field(*fields):
                for f in fields:
                    if f and isinstance(f, str) and f.strip():
                        return f.strip()
                return ""

            # Helper to check for valid address
            def is_po_box(addr):
                return addr and isinstance(addr, str) and 'po box' in addr.lower()
            def is_street(addr):
                if not addr or not isinstance(addr, str):
                    return False
                lower = addr.lower()
                # Exclude ABN and other non-address markers
                if 'abn:' in lower or 'gst:' in lower or 'tax' in lower:
                    return False
                # Heuristic: must contain a number or 'unit' or 'suite' or 'lot' or 'street' or 'road' or 'ave' or 'drive' or 'blvd' or 'lane'
                keywords = ['unit', 'suite', 'lot', 'street', 'st', 'road', 'rd', 'ave', 'avenue', 'drive', 'dr', 'blvd', 'lane']
                if any(k in lower for k in keywords) or any(c.isdigit() for c in addr):
                    return True
                return False

            def pick_address_fields(addr1, addr2, extra=None):
                addr1 = addr1.strip() if addr1 else ''
                addr2 = addr2.strip() if addr2 else ''
                extra = extra.strip() if extra else ''
                # Prefer valid street or PO Box, skip ABN
                if is_street(addr1):
                    return addr1, addr2 if addr2 else extra
                if is_po_box(addr1):
                    return addr1, addr2 if addr2 else extra
                if is_street(addr2):
                    return addr2, extra
                if is_po_box(addr2):
                    return addr2, extra
                if is_street(extra):
                    return extra, ''
                if is_po_box(extra):
                    return extra, ''
                return '', ''

            address1, address2 = pick_address_fields(
                customer_address.get("address1"),
                customer_address.get("address2"),
                detail.get("customerAddress2")
            )
            # Validation: reject if both are empty
            if not address1:
                logger.warning("No valid address found for customer; rejecting address fields.")
                address1 = address2 = ''

            city = pick_any_field(
                customer_address.get("city"),
                detail.get("customerCity"),
            )
            state = pick_any_field(
                customer_address.get("state"),
                detail.get("customerState"),
            )
            zip_code = pick_any_field(
                customer_address.get("postalCode"),
                detail.get("customerZIP"),
            )
            # Phone extraction: check all possible fields in order
            phone = pick_any_field(
                detail.get("customerPhone"),
                detail.get("customerPhone2"),
                detail.get("customerPhone3"),
                result.get("phone1"),
                result.get("phone2"),
                result.get("phone3"),
                customer_address.get("phone"),
            )
            # Email extraction: check all possible fields in order
            email = pick_any_field(
                detail.get("customerEmail"),
                result.get("email"),
                customer_address.get("email"),
            )
            use_sold_to_business_name = detail.get("useSoldToBusinessName", False)
            formatted_customer = {
                "id": result.get("customerId") or detail.get("customerSourceId"),
                "customer_source_id": result.get("customerId") or detail.get("customerSourceId"),
                "name": pick_any_field(
                    detail.get("customerName"), customer_address.get("businessName")
                ),
                "first_name": pick_any_field(
                    detail.get("customerFirstName"), customer_address.get("firstName")
                ),
                "last_name": pick_any_field(
                    detail.get("customerLastName"), customer_address.get("lastName")
                ),
                "business_name": pick_any_field(
                    customer_address.get("businessName"),
                    detail.get("customerBusinessName"),
                ),
                "address": f"{address1}, {city}, {state} {zip_code}",
                "address1": address1,
                "address2": address2,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                "email": email,
                "phone": phone,
                "use_sold_to_business_name": use_sold_to_business_name,
                "internal_notes": detail.get("internalNotes", ""),
                "customer_type": result.get(
                    "customerType", detail.get("customerType", "")
                ),
                "preferred_salesperson1": result.get(
                    "preferredSalesperson1", detail.get("preferredSalesperson1", "")
                ),
                "preferred_salesperson2": result.get(
                    "preferredSalesperson2", detail.get("preferredSalesperson2", "")
                ),
                "store_number": result.get(
                    "storeNumber", detail.get("defaultStore", "")
                ),
            }
            return [formatted_customer]
        except Exception as e:
            logger.error(f"Error finding customer by ID: {str(e)}")
            return []

    def find_customer_by_name(self, name):
        logger.info(f"Finding customers by name: {name}")
        self.ensure_session()
        url = f"{self.base_url}/v2/customers/find"
        payload = {
            "searchText": name,
            "includeCustomers": True,
            "includeProspects": False,
            "includeInactive": False,
            "startIndex": 0,
            "storeNumber": 49,
            "entryType": "Customer",
            "referralType": "standalone",
        }
        try:
            data = self.execute_request("POST", url, payload)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                for key in ["customers", "result", "data"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
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
            if not self.ensure_session():
                logger.error("Failed to establish session for customer retrieval")
                return None
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.get(
                url, headers=headers, auth=auth, timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    customer = data.get("result", {})
                    logger.info(
                        f"Successfully retrieved customer: {customer.get('customerId', '')}"
                    )
                    return self._format_customer(customer)
                else:
                    logger.warning(f"No customer found with ID: {customer_id}")
                    return None
            else:
                logger.error(
                    f"Failed to get customer. Status code: {response.status_code}"
                )
                logger.error(f"Response: {response.text}")
                return None
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
        required_fields = [
            "business_name",
            "first_name",
            "last_name",
            "address1",
            "city",
            "state",
        ]
        missing_fields = [
            field
            for field in required_fields
            if not customer_data.get(field) and not customer_data.get("customer_name")
        ]
        if missing_fields and not customer_data.get("customer_name"):
            raise ValueError(
                f"Missing required customer data: {', '.join(missing_fields)}"
            )
        payload = {
            "customer": {
                "name": customer_data.get("business_name", "")
                or customer_data.get("customer_name", ""),
                "salutation": customer_data.get("salutation", ""),
                "firstName": customer_data.get("first_name", ""),
                "lastName": customer_data.get("last_name", ""),
                "address1": customer_data.get("address1", ""),
                "city": customer_data.get("city", ""),
                "state": customer_data.get("state", ""),
                "postalCode": customer_data.get("zip_code", ""),
                "country": customer_data.get("country", "Australia"),
                "phone": customer_data.get("phone", ""),
                "email": customer_data.get("email", ""),
                "type": "INSURANCE",
                "activeDate": datetime.now().strftime("%Y-%m-%d"),
                "storeCode": 49,
            }
        }
        try:
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                url, headers=headers, auth=auth, json=payload, timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("result", {}).get("customer", {})
            else:
                logger.error(f"Error creating customer: {response.text}")
                raise Exception(f"Error creating customer: {response.text}")
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
        if not quote_data.get("customer_id"):
            raise ValueError("Missing required field: customer_id")
        payload = {
            "quote": {
                "customerId": quote_data.get("customer_id"),
                "opportunityName": quote_data.get(
                    "opportunity_name", "New Opportunity"
                ),
                "storeCode": self.store_code,
                "salesPerson": quote_data.get("sales_person", ""),
                "workOrderNotes": quote_data.get("scope_of_work", ""),
                "billToAddress": {
                    "name": quote_data.get("bill_to_name", ""),
                    "address1": quote_data.get("bill_to_address1", ""),
                    "address2": quote_data.get("bill_to_address2", ""),
                    "city": quote_data.get("bill_to_city", ""),
                    "state": quote_data.get("bill_to_state", ""),
                    "postalCode": quote_data.get("bill_to_zip", ""),
                    "country": quote_data.get("bill_to_country", "Australia"),
                },
                "shipToAddress": {
                    "name": quote_data.get("ship_to_name", ""),
                    "address1": quote_data.get("ship_to_address1", ""),
                    "address2": quote_data.get("ship_to_address2", ""),
                    "city": quote_data.get("ship_to_city", ""),
                    "state": quote_data.get("ship_to_state", ""),
                    "postalCode": quote_data.get("ship_to_zip", ""),
                    "country": quote_data.get("ship_to_country", "Australia"),
                },
            }
        }
        try:
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                url, headers=headers, auth=auth, json=payload, timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("result", {}).get("quote", {})
            else:
                logger.error(f"Error creating quote: {response.text}")
                raise Exception(f"Error creating quote: {response.text}")
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
            if not all(
                key in job_data["order"]
                for key in ["CustomerSeqNum", "PONumber", "MiscCharges"]
            ):
                raise ValueError("Missing required fields in job data")
            session_token = self.session_token
            if not session_token:
                raise Exception("Failed to get session token")
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                f"{self.base_url}/v2/Order", headers=headers, auth=auth, json=job_data
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
        if not order_ids or not isinstance(order_ids, list) or len(order_ids) < 1:
            raise ValueError("At least one order ID is required")
        payload = {"orderIds": order_ids}
        try:
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                url, headers=headers, auth=auth, json=payload, timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("result", {})
            else:
                logger.error(f"Error adding orders to billing group: {response.text}")
                raise Exception(
                    f"Error adding orders to billing group: {response.text}"
                )
        except Exception as e:
            logger.error(f"Error adding orders to billing group: {str(e)}")
            raise Exception(f"Error adding orders to billing group: {str(e)}")

    def find_customers_advanced(self, search_params):
        url = f"{self.base_url}/v2/customers/find"
        try:
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.post(
                url,
                headers=headers,
                auth=auth,
                json=search_params,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.json().get("result", {})
            else:
                logger.error(f"Error in advanced customer search: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error in advanced customer search: {str(e)}")
            return {}

    def get_customer_values(self):
        url = f"{self.base_url}/v2/customer/values"
        try:
            headers = self._get_headers()
            auth = self._get_auth()
            logger.debug(
                f"[RFMS API] Outgoing auth: (username: {auth[0]}, password: {'*' * len(str(auth[1]))})"
            )
            logger.debug(f"[RFMS API] Outgoing headers: {headers}")
            response = requests.get(
                url, headers=headers, auth=auth, timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json().get("result", {})
            else:
                logger.error(f"Error getting customer values: {response.text}")
                return {}
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
                "id": customer.get("customerSourceId", ""),
                "customer_source_id": customer.get("customerSourceId", ""),
                "name": customer.get("customerName", ""),
                "first_name": customer.get("customerFirstName", ""),
                "last_name": customer.get("customerLastName", ""),
                "business_name": customer.get("customerBusinessName", ""),
                "address1": customer.get("customerAddress", ""),
                "address2": customer.get("customerAddress2", ""),
                "city": customer.get("customerCity", ""),
                "state": customer.get("customerState", ""),
                "zip_code": customer.get("customerZIP", ""),
                "phone": customer.get("customerPhone", ""),
                "email": customer.get("customerEmail", ""),
                "customer_type": customer.get("customerType", ""),
                "tax_status": customer.get("taxStatus", ""),
                "tax_method": customer.get("taxMethod", ""),
                "preferred_salesperson1": customer.get("preferredSalesperson1", ""),
                "preferred_salesperson2": customer.get("preferredSalesperson2", ""),
                "store_number": customer.get("defaultStore", ""),
                "internal_notes": customer.get("internalNotes", ""),
                "ship_to": {
                    "name": customer.get("shipToName", ""),
                    "first_name": customer.get("shipToFirstName", ""),
                    "last_name": customer.get("shipToLastName", ""),
                    "business_name": customer.get("shipToBusinessName", ""),
                    "address1": customer.get("shipToAddress", ""),
                    "address2": customer.get("shipToAddress2", ""),
                    "city": customer.get("shipToCity", ""),
                    "state": customer.get("shipToState", ""),
                    "zip_code": customer.get("shipToZIP", ""),
                    "county": customer.get("shipToCounty", ""),
                },
            }
            formatted_customers.append(formatted_customer)

        return formatted_customers

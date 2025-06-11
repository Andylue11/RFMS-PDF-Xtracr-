# utils/payload_service.py
import os
import json
from datetime import datetime, timedelta

# Define custom exception for payload errors if needed
class PayloadError(ValueError):
    pass

def build_rfms_customer_payload(data):
    """
    Builds the payload for creating a new customer in RFMS.
    Accepts 'data' which is the JSON from the request.
    """
    if data is None:
        raise PayloadError("No data provided for customer creation")

    # Accept both old and new payloads
    if "customer" not in data and "ship_to" not in data:
        customer = data
        ship_to = data
    else:
        customer = data.get("customer", {})
        ship_to = data.get("ship_to", {})

    # Required fields validation
    first_name = customer.get("first_name") or ship_to.get("first_name", "")
    last_name = customer.get("last_name") or ship_to.get("last_name", "")
    if not first_name or not last_name:
        raise PayloadError("Customer first name and last name are required.")

    # Use environment variable for store number if available
    store_number = os.getenv("RFMS_STORE_NUMBER", "49")
    store = int(os.getenv("RFMS_STORE", 1))

    payload = {
        "customerType": customer.get("customer_type", "INSURANCE"),
        "entryType": customer.get("entry_type", "Customer"),
        "customerAddress": {
            "firstName": first_name,
            "lastName": last_name,
            "businessName": customer.get("customer_name") or customer.get("business_name") or ship_to.get("name") or "",
            "address1": customer.get("address1") or ship_to.get("address1", ""),
            "address2": customer.get("address2") or ship_to.get("address2", ""),
            "city": customer.get("city") or ship_to.get("city", ""),
            "state": customer.get("state") or ship_to.get("state", ""),
            "postalCode": customer.get("zip_code") or ship_to.get("zip_code", ""),
            "country": customer.get("country") or ship_to.get("country", "Australia"),
        },
        "shipToAddress": {
            "firstName": ship_to.get("first_name") or customer.get("first_name", ""),
            "lastName": ship_to.get("last_name") or customer.get("last_name", ""),
            "businessName": ship_to.get("name") or ship_to.get("business_name") or customer.get("business_name") or "",
            "address1": ship_to.get("address1") or ship_to.get("address", "") or customer.get("address1", ""),
            "address2": ship_to.get("address2") or customer.get("address2", ""),
            "city": ship_to.get("city") or customer.get("city", ""),
            "state": ship_to.get("state") or customer.get("state", ""),
            "postalCode": ship_to.get("zip_code") or customer.get("zip_code", ""),
            "country": ship_to.get("country") or customer.get("country", "Australia"),
        },
        "phone1": customer.get("phone") or customer.get("phone1") or "",
        "phone2": customer.get("phone2") or "",
        "phone3": customer.get("phone3") or "",
        "phone4": customer.get("phone4") or "",
        "phone5": customer.get("phone5") or "",
        "email": customer.get("email", ""),
        "taxStatus": customer.get("taxStatus", "Tax"),
        "taxMethod": customer.get("taxMethod", "SalesTax"),
        "storeNumber": customer.get("storeNumber", store_number),
        "activeDate": datetime.now().strftime("%Y-%m-%d"),
        "preferredSalesperson1": customer.get("preferredSalesperson1", ""),
        "preferredSalesperson2": customer.get("preferredSalesperson2", ""),
        # Flat fields for legacy/compatibility
        "CustomerFirstName": first_name,
        "CustomerLastName": last_name,
        "CustomerAddress1": customer.get("address1") or ship_to.get("address1", ""),
        "CustomerAddress2": customer.get("address2") or ship_to.get("address2", ""),
        "CustomerCity": customer.get("city") or ship_to.get("city", ""),
        "CustomerState": customer.get("state") or ship_to.get("state", ""),
        "CustomerPostalCode": customer.get("zip_code") or ship_to.get("zip_code", ""),
        "CustomerCounty": customer.get("county", ""),
        "ShipToFirstName": ship_to.get("first_name") or customer.get("first_name", ""),
        "ShipToLastName": ship_to.get("last_name") or customer.get("last_name", ""),
        "ShipToAddress1": ship_to.get("address1") or ship_to.get("address", "") or customer.get("address1", ""),
        "ShipToAddress2": ship_to.get("address2") or customer.get("address2", ""),
        "ShipToCity": ship_to.get("city") or customer.get("city", ""),
        "ShipToState": ship_to.get("state") or customer.get("state", ""),
        "ShipToPostalCode": ship_to.get("zip_code") or customer.get("zip_code", ""),
        "ShipToCounty": ship_to.get("county", ""),
        "Phone2": customer.get("phone2") or "",
        "Phone3": customer.get("phone3") or "",
        "ShipToLocked": customer.get("ShipToLocked", False),
        "SalesPerson1": customer.get("SalesPerson1", "ZORAN VEKIC"),
        "SalesPerson2": customer.get("SalesPerson2", ""),
        "SalesRepLocked": customer.get("SalesRepLocked", False),
        "CommisionSplitPercent": float(customer.get("CommisionSplitPercent", 0.0)),
        "Store": store,
    }
    return payload

def export_data_to_rfms(api_client, export_data, logger):
    """
    Builds the comprehensive RFMS payload and makes the API call.
    Uses the new comprehensive format while maintaining mapping relationships.
    'export_data' is the JSON from the /api/export-to-rfms request.
    'api_client' is the initialized RfmsApi instance.
    'logger' is the Flask app logger.
    """
    sold_to_data = export_data["sold_to"]
    sold_to_customer_id = sold_to_data.get("id") or sold_to_data.get("customer_source_id")
    if not sold_to_customer_id:
        raise PayloadError("Missing Sold To customer ID for export.")

    ship_to_data = export_data["ship_to"]
    job_details_data = export_data["job_details"]

    # Extract phone numbers with proper fallbacks
    supervisor_phone1 = (
        job_details_data.get("supervisor_phone") or 
        job_details_data.get("supervisor_mobile") or 
        ship_to_data.get("pdf_phone1") or 
        ship_to_data.get("phone") or 
        "0447012125"  # Default fallback
    )
    
    supervisor_phone2 = (
        ship_to_data.get("pdf_phone2") or 
        ship_to_data.get("phone2") or 
        ship_to_data.get("mobile") or 
        "0732341234"  # Default fallback
    )

    # Extract supervisor name with fallback
    supervisor_name = job_details_data.get("supervisor_name", "")
    if not supervisor_name:
        supervisor_name = f"{sold_to_data.get('first_name', 'Unknown')} {sold_to_data.get('last_name', 'Supervisor')}"

    # Default values for ship_to
    ship_to_first_name = ship_to_data.get("first_name", "").strip() or "Site"
    ship_to_last_name = ship_to_data.get("last_name", "").strip() or "Customer"
    ship_to_address1 = (ship_to_data.get("address1", "") or ship_to_data.get("address", "")).strip() or "Address Required"
    ship_to_city = ship_to_data.get("city", "").strip() or "Brisbane"
    ship_to_state = ship_to_data.get("state", "").strip() or "QLD"
    ship_to_postal_code = ship_to_data.get("zip_code", "").strip() or "4000"

    # Custom note logic for alternate contacts
    custom_note_lines = []
    alt_contact = export_data.get("alternate_contact", {})
    alt_contacts_list = export_data.get("alternate_contacts", [])
    
    if alt_contact and (alt_contact.get("name") or alt_contact.get("phone") or alt_contact.get("email")):
        best_contact_str = f"Best Contact: {alt_contact.get('name', '')} {alt_contact.get('phone', '')}"
        if alt_contact.get("phone2"):
            best_contact_str += f", {alt_contact.get('phone2')}"
        if alt_contact.get("email"):
            best_contact_str += f" ({alt_contact.get('email')})"
        custom_note_lines.append(best_contact_str)
    
    for contact in alt_contacts_list:
        if contact.get("name") or contact.get("phone") or contact.get("email"):
            line = f"{contact.get('type', 'Contact')}: {contact.get('name', '')} {contact.get('phone', '')}"
            if contact.get("phone2"):
                line += f", {contact.get('phone2')}"
            if contact.get("email"):
                line += f" ({contact.get('email')})"
            custom_note_lines.append(line)
    
    custom_note = "\n".join(custom_note_lines).strip()

    # Environment/config values
    store_number = int(os.getenv("RFMS_STORE_NUMBER", "49"))
    username = os.getenv("RFMS_USERNAME", "zoran.vekic")

    # Generate PO number and job number
    po_number = job_details_data.get("po_number", f"PDF-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    job_number = f"{supervisor_name} {supervisor_phone1}".strip() or po_number

    # Date calculations
    current_date = datetime.now().strftime("%Y-%m-%d")
    estimated_delivery = (
        job_details_data.get("promise_date") or 
        job_details_data.get("completion_date") or 
        (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    )

    # Build the comprehensive RFMS payload using our successful format
    # This uses the AZ002876 structure + comprehensive lines format
    order_payload = {
        "category": "Order",  # Prevents weborders
        "poNumber": po_number,
        "jobNumber": job_number,
        "storeNumber": store_number,
        "salesperson1": "ZORAN VEKIC",
        "salesperson2": "",
        
        # 🔑 SUCCESSFUL CUSTOMER STRUCTURE (AZ002854/AZ002876 format)
        "soldTo": {
            "customerId": sold_to_customer_id,
            "firstName": sold_to_data.get("first_name", supervisor_name.split()[0] if supervisor_name else "Unknown"),
            "lastName": sold_to_data.get("last_name", supervisor_name.split()[-1] if supervisor_name else "Customer"),
            "address1": sold_to_data.get("address1", ""),
            "address2": sold_to_data.get("address2", ""),
            "city": sold_to_data.get("city", ""),
            "state": sold_to_data.get("state", ""),
            "postalCode": sold_to_data.get("zip_code", ""),
            "phone1": supervisor_phone1,  # Primary phone (mobile) - ONLY in soldTo
            "phone2": supervisor_phone2,  # Secondary phone (office) - ONLY in soldTo
            "email": sold_to_data.get("email", f"{supervisor_name.lower().replace(' ', '.')}@example.com")
        },
        
        "shipTo": {
            "firstName": ship_to_first_name,
            "lastName": ship_to_last_name,
            "address1": ship_to_address1,
            "address2": ship_to_data.get("address2", ""),
            "city": ship_to_city,
            "state": ship_to_state,
            "postalCode": ship_to_postal_code
            # NO phone fields in shipTo per successful AZ002876 format
        },
        
        # 🔑 ALL SUCCESSFUL FIELDS from incremental testing
        "privateNotes": f"PDF Extracted - Supervisor: {supervisor_name}",
        "publicNotes": f"Customer Phones: Mobile {supervisor_phone1}, Office {supervisor_phone2}",
        "workOrderNotes": f"Contact: {supervisor_name} - Mobile: {supervisor_phone1} | Office: {supervisor_phone2}",
        "estimatedDeliveryDate": estimated_delivery,
        
        # 🔑 WORKING TYPE IDs (from successful tests)
        "userOrderTypeId": 18,  # RESIDENTIAL INSURANCE 
        "serviceTypeId": 8,     # SUPPLY & INSTALL
        "contractTypeId": 1,    # 30 DAY ACCOUNT
        "adSource": 1,
        
        # 🔥 COMPREHENSIVE LINES STRUCTURE (User's format)
        "lines": [
            {
                "id": "",
                "isUseTaxLine": False,
                "notes": f"PDF Supervisor: {supervisor_name}",
                "internalNotes": f"Contact: {supervisor_phone1}",
                "productId": 213322,  # Default product ID
                "colorId": 2133,      # Default color ID
                "quantity": float(job_details_data.get("dollar_value", 1000.0)),
                "serialNumber": "",
                "ecProductId": None,
                "ecColorId": None,
                "delete": False,
                "priceLevel": 10,
                "lineStatus": "none",
                "lineGroupId": 4
            }
        ]
    }

    # Add custom notes if available
    if custom_note:
        order_payload["privateNotes"] += f"\n{custom_note}"

    logger.info(f"Constructed comprehensive RFMS Order Payload: {json.dumps(order_payload, indent=2)}")

    # Main job creation using comprehensive format
    job_result = api_client.create_job(order_payload)
    job_id = job_result.get("result") or job_result.get("id")
    
    if not job_id:
        raise Exception(f"Failed to create main job in RFMS. Response: {job_result}")
    
    logger.info(f"Main job created in RFMS with comprehensive format - Order ID: {job_id}")

    final_result = {
        "success": True,
        "message": "Successfully exported main job to RFMS using comprehensive format",
        "job": job_result,
        "order_id": job_id,
        "sold_to_customer_id": sold_to_customer_id,
        "format_used": "comprehensive_lines_az002876_structure"
    }

    # Handle billing group if applicable (second job)
    if export_data.get("billing_group") and export_data.get("second_job_details"):
        second_job_details = export_data["second_job_details"]
        
        # Create second order payload based on the successful structure
        second_order_payload = order_payload.copy()
        second_order_payload["poNumber"] = second_job_details.get("po_number", f"PDF2-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        # Update quantity/dollar value for second job
        second_order_payload["lines"] = [
            {
                "id": "",
                "isUseTaxLine": False,
                "notes": f"Second Job - PDF Supervisor: {supervisor_name}",
                "internalNotes": f"Second Job Contact: {supervisor_phone1}",
                "productId": 213322,
                "colorId": 2133,
                "quantity": float(second_job_details.get("dollar_value", 1000.0)),
                "serialNumber": "",
                "ecProductId": None,
                "ecColorId": None,
                "delete": False,
                "priceLevel": 10,
                "lineStatus": "none",
                "lineGroupId": 4
            }
        ]
        
        # Update notes for second job
        second_order_payload["publicNotes"] = second_job_details.get("description_of_works", "").strip()
        second_supervisor_name = second_job_details.get("supervisor_name", supervisor_name)
        second_supervisor_phone = second_job_details.get("supervisor_phone", "") or second_job_details.get("supervisor_mobile", supervisor_phone1)
        second_job_number = f"{second_supervisor_name} {second_supervisor_phone}".strip() or second_job_details.get("po_number", "")
        second_order_payload["jobNumber"] = second_job_number
        
        logger.info(f"Creating second job in RFMS (billing group): {second_order_payload['poNumber']}")
        second_job_result = api_client.create_job(second_order_payload)
        second_job_id = second_job_result.get("result") or second_job_result.get("id")
        
        if not second_job_id:
            raise Exception(f"Failed to create second job in RFMS. Response: {second_job_result}")
        
        logger.info(f"Second job created in RFMS with ID: {second_job_id}")
        
        # Add to billing group
        billing_group_result = api_client.add_to_billing_group([job_id, second_job_id])
        final_result["second_job"] = second_job_result
        final_result["second_order_id"] = second_job_id
        final_result["billing_group"] = billing_group_result
        final_result["message"] = "Successfully exported main job, second job, and created billing group using comprehensive format."
    
    return final_result 
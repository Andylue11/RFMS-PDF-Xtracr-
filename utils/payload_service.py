# utils/payload_service.py
import os
import json
from datetime import datetime

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
    Builds the payload for exporting order/job data to RFMS and makes the API call.
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

    # Default values and phone logic
    ship_to_first_name = ship_to_data.get("first_name", "").strip() or "Unknown"
    ship_to_last_name = ship_to_data.get("last_name", "").strip() or "Customer"
    ship_to_address1 = (ship_to_data.get("address1", "") or ship_to_data.get("address", "")).strip() or "Address Required"
    ship_to_city = ship_to_data.get("city", "").strip() or "Brisbane"
    ship_to_state = ship_to_data.get("state", "").strip() or "QLD"
    ship_to_postal_code = ship_to_data.get("zip_code", "").strip() or "4000"

    phone3_value = ship_to_data.get("phone3", "")
    phone4_value = ship_to_data.get("phone4", "")
    pdf_phone1 = ship_to_data.get("pdf_phone1", "") or ship_to_data.get("phone", "")
    pdf_phone2 = ship_to_data.get("pdf_phone2", "") or ship_to_data.get("phone2", "") or ship_to_data.get("mobile", "")
    job_phone1 = phone3_value if phone3_value else pdf_phone1
    job_phone2 = phone4_value if phone4_value else pdf_phone2

    # Custom note logic (expand as needed)
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
    store = int(os.getenv("RFMS_STORE", 1))
    username = os.getenv("RFMS_USERNAME", "zoran.vekic")

    order_payload = {
        "username": username,
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
            "IsWebOrder": False,
            "Exported": False,
            "CanEdit": True,
            "LockTaxes": False,
            "CustomerSource": "Customer",
            "CustomerSeqNum": sold_to_customer_id,
            "CustomerUpSeqNum": sold_to_customer_id,
            "CustomerFirstName": sold_to_data.get("first_name", ""),
            "CustomerLastName": sold_to_data.get("last_name", ""),
            "CustomerAddress1": sold_to_data.get("address1", ""),
            "CustomerAddress2": sold_to_data.get("address2", ""),
            "CustomerCity": sold_to_data.get("city", ""),
            "CustomerState": sold_to_data.get("state", ""),
            "CustomerPostalCode": sold_to_data.get("zip_code", ""),
            "CustomerCounty": "",
            "Phone1": job_phone1,
            "ShipToFirstName": ship_to_first_name,
            "ShipToLastName": ship_to_last_name,
            "ShipToAddress1": ship_to_address1,
            "ShipToAddress2": ship_to_data.get("address2", ""),
            "ShipToCity": ship_to_city,
            "ShipToState": ship_to_state,
            "ShipToPostalCode": ship_to_postal_code,
            "Phone2": job_phone2,
            "Phone3": ship_to_data.get("phone3", "") or ship_to_data.get("work_phone", ""),
            "ShipToLocked": False,
            "SalesPerson1": "ZORAN VEKIC",
            "SalesPerson2": "",
            "SalesRepLocked": False,
            "CommisionSplitPercent": 0.0,
            "Store": store,
            "Email": ship_to_data.get("email", ""),
            "CustomNote": custom_note,
            "Note": job_details_data.get("description_of_works", "").strip(),
            "WorkOrderNote": "",
            "PickingTicketNote": None,
            "OrderDate": "",
            "MeasureDate": job_details_data.get("measure_date", "") or job_details_data.get("commencement_date", ""),
            "PromiseDate": job_details_data.get("promise_date", "") or job_details_data.get("completion_date", ""),
            "PONumber": job_details_data.get("po_number", ""),
            "CustomerType": "INSURANCE",
            "JobNumber": f"{job_details_data.get('supervisor_name', '')} {job_details_data.get('supervisor_phone', '') or job_details_data.get('supervisor_mobile', '')}".strip() or job_details_data.get("po_number", ""),
            "DateEntered": datetime.now().strftime("%Y-%m-%d"),
            "DatePaid": None,
            "DueDate": "",
            "Model": None,
            "PriceLevel": 3,
            "TaxStatus": "Tax",
            "Occupied": False,
            "Voided": False,
            "AdSource": 1,
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
            "UserOrderType": 12,
            "ServiceType": 9,
            "ContractType": 2,
            "Timeslot": 0,
            "InstallStore": store,
            "AgeFrom": None,
            "Completed": None,
            "ReferralAmount": 0.0,
            "ReferralLocked": False,
            "PreAuthorization": None,
            "SalesTax": 0.0,
            "GrandInvoiceTotal": 0.0,
            "MaterialOnly": 0.0,
            "Labor": 0.0,
            "MiscCharges": float(job_details_data.get("dollar_value", 0)),
            "InvoiceTotal": 0.0,
            "MiscTax": 0.0,
            "RecycleFee": 0.0,
            "TotalPaid": 0.0,
            "Balance": 0.0,
            "DiscountRate": 0.0,
            "DiscountAmount": 0.0,
            "ApplyRecycleFee": False,
            "Attachements": None,
            "PendingAttachments": None,
            "Order": None,
            "LockInfo": None,
            "Message": None,
            "Lines": []
        },
        "products": None
    }

    logger.info(f"Constructed Order Payload for RFMS: {json.dumps(order_payload, indent=2)}")

    # Main job creation
    job_result = api_client.create_job(order_payload)
    job_id = job_result.get("id")
    if not job_id:
        raise Exception(f"Failed to create main job in RFMS. Response: {job_result}")
    logger.info(f"Main job created in RFMS with ID: {job_id}")

    final_result = {
        "success": True,
        "message": "Successfully exported main job to RFMS",
        "job": job_result,
        "sold_to_customer_id": sold_to_customer_id
    }

    # Handle billing group if applicable
    if export_data.get("billing_group") and export_data.get("second_job_details"):
        second_job_details = export_data["second_job_details"]
        second_order_payload = order_payload.copy()
        second_order_payload["order"] = order_payload["order"].copy()
        second_order_payload["order"]["PONumber"] = second_job_details.get("po_number", "")
        second_order_payload["order"]["MiscCharges"] = float(second_job_details.get("dollar_value", 0))
        second_order_payload["order"]["Note"] = second_job_details.get("description_of_works", "").strip()
        second_order_payload["order"]["MeasureDate"] = second_job_details.get("measure_date", "") or second_job_details.get("commencement_date", "")
        second_order_payload["order"]["PromiseDate"] = second_job_details.get("promise_date", "") or second_job_details.get("completion_date", "")
        second_supervisor_name = second_job_details.get("supervisor_name", "")
        second_supervisor_phone = second_job_details.get("supervisor_phone", "") or second_job_details.get("supervisor_mobile", "")
        second_job_number = f"{second_supervisor_name} {second_supervisor_phone}".strip() or second_job_details.get("po_number", "")
        second_order_payload["order"]["JobNumber"] = second_job_number
        logger.info(f"Creating second job in RFMS (billing group): {second_order_payload['order'].get('PONumber')}")
        second_job_result = api_client.create_job(second_order_payload)
        second_job_id = second_job_result.get("id")
        if not second_job_id:
            raise Exception(f"Failed to create second job in RFMS. Response: {second_job_result}")
        logger.info(f"Second job created in RFMS with ID: {second_job_id}")
        billing_group_result = api_client.add_to_billing_group([job_id, second_job_id])
        final_result["second_job"] = second_job_result
        final_result["billing_group"] = billing_group_result
        final_result["message"] = "Successfully exported main job, second job, and created billing group."
    return final_result 
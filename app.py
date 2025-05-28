# === WATCHER HEADER START ===
# File: app.py
# Managed by file watcher
# === WATCHER HEADER END ===
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    flash,
    redirect,
    url_for,
    session,
)
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
from datetime import datetime
import tempfile
import json

# Load environment variables FIRST before any other imports that might use them
load_dotenv(dotenv_path=".env")

# Import models and database
from models import db, Customer, Quote, Job, PdfData
from models.customer import ApprovedCustomer

# Import utility modules
from utils.pdf_extractor import extract_data_from_pdf
from utils.rfms_api import RfmsApi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)

# App configuration
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URI", "sqlite:///rfms_xtracr.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload size
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

# Disable caching in development
@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize database with app
db.init_app(app)

# Validate RFMS API credentials before initializing
rfms_base_url = os.getenv("RFMS_BASE_URL", "https://api.rfms.online")
rfms_store_code = os.getenv("RFMS_STORE_CODE")
rfms_username = os.getenv("RFMS_USERNAME")
rfms_api_key = os.getenv("RFMS_API_KEY")

# Log credential status for debugging
logger.info(f"RFMS API Configuration:")
logger.info(f"  Base URL: {rfms_base_url}")
logger.info(f"  Store Code: {'Loaded' if rfms_store_code else 'Missing'}")
logger.info(f"  Username: {'Loaded' if rfms_username else 'Missing'}")
logger.info(f"  API Key: {'Loaded' if rfms_api_key else 'Missing'}")

# Check for missing credentials
missing_credentials = []
if not rfms_store_code:
    missing_credentials.append("RFMS_STORE_CODE")
if not rfms_username:
    missing_credentials.append("RFMS_USERNAME")
if not rfms_api_key:
    missing_credentials.append("RFMS_API_KEY")

if missing_credentials:
    logger.error(f"Missing required RFMS API credentials: {', '.join(missing_credentials)}")
    logger.error("Please check your .env file and ensure all RFMS_* variables are set")
    # Initialize with None values to prevent crashes, but log the issue
    rfms_api = None
else:
    # Initialize RFMS API client with validated credentials
    rfms_api = RfmsApi(
        base_url=rfms_base_url,
        store_code=rfms_store_code,
        username=rfms_username,
        api_key=rfms_api_key,
    )
    logger.info("RFMS API client initialized successfully")

# Helper function to check RFMS API availability
def ensure_rfms_api():
    """Ensure RFMS API is available and properly configured."""
    if rfms_api is None:
        raise Exception("RFMS API not configured. Please check your environment variables.")
    return rfms_api

# Helper functions
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


# Routes
@app.route("/")
def index():
    """Render the main dashboard page."""
    # Get recent PDF uploads
    recent_pdfs = PdfData.query.order_by(PdfData.created_at.desc()).limit(5).all()

    # Calculate stats
    total_uploads = PdfData.query.count()
    processed_uploads = PdfData.query.filter_by(processed=True).count()
    quotes_created = Quote.query.count()
    jobs_created = Job.query.count()

    stats = {
        "total_uploads": total_uploads,
        "processed_uploads": processed_uploads,
        "quotes_created": quotes_created,
        "jobs_created": jobs_created,
    }

    return render_template("index.html", recent_pdfs=recent_pdfs, stats=stats)


@app.route("/upload-pdf", methods=["POST"])
def upload_pdf_api():
    """Handle PDF upload and extraction via API endpoint."""
    # Ensure RFMS session is ready for downstream actions
    session_ok = ensure_rfms_api().ensure_session()
    logger.info(
        f"RFMS session ready after PDF upload: {session_ok}, token: {rfms_api.session_token}, expiry: {rfms_api.session_expiry}"
    )
    if not session_ok:
        return (
            jsonify({"error": "Could not establish RFMS session. Please try again."}),
            500,
        )
    if "pdf_file" not in request.files:
        logger.warning("No file part in upload request.")
        return jsonify({"error": "No file part"}), 400

    file = request.files["pdf_file"]

    if file.filename == "":
        logger.warning("No selected file in upload request.")
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create a temporary file path or use BytesIO directly if extractor supports it
        # Since the extractor takes a file path, saving to a temporary file is necessary

        # Use a temporary file that will be automatically deleted
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name

        try:
            # Extract data from PDF using the utility function
            extracted_data = extract_data_from_pdf(temp_path)
            logger.info(f"Successfully extracted data for {filename}")

            # Clean up the temporary file
            os.remove(temp_path)

            # Return the extracted data as JSON
            return jsonify(extracted_data), 200

        except Exception as e:
            logger.error(f"Error extracting data from PDF {filename}: {str(e)}")
            # Clean up the temporary file in case of error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"error": f"Error extracting data: {str(e)}"}), 500

    else:
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400


@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle PDF upload and extraction."""
    if "pdf_file" not in request.files:
        flash("No file part")
        return redirect(request.url)

    file = request.files["pdf_file"]

    if file.filename == "":
        flash("No selected file")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        try:
            # Extract data from PDF
            extracted_data = extract_data_from_pdf(file_path)

            # Save extracted data to session for preview
            session["extracted_data"] = extracted_data

            # Save to database for persistence
            pdf_data = PdfData(
                filename=filename,
                customer_name=extracted_data.get("customer_name", ""),
                business_name=extracted_data.get("business_name", ""),
                po_number=extracted_data.get("po_number", ""),
                scope_of_work=extracted_data.get("scope_of_work", ""),
                dollar_value=extracted_data.get("dollar_value", 0),
                extracted_data=extracted_data,
                created_at=datetime.now(),
            )

            db.session.add(pdf_data)
            db.session.commit()

            # Create first job
            first_job_data = {
                "username": "zoran.vekic",
                "order": {
                    "CustomerSeqNum": pdf_data.customer_id,
                    "CustomerUpSeqNum": pdf_data.customer_id,
                    "PONumber": pdf_data.po_number,
                    "WorkOrderNote": pdf_data.scope_of_work,
                    "CustomerType": "INSURANCE",
                    "UserOrderType": 12,
                    "ServiceType": 9,
                    "ContractType": 2,
                    "SalesPerson1": "ZORAN VEKIC",
                    "Store": 1,
                    "InstallStore": 1,
                    "OrderDate": datetime.now().strftime("%Y-%m-%d"),
                    "DateEntered": datetime.now().strftime("%Y-%m-%d"),
                    "GrandInvoiceTotal": pdf_data.dollar_value,
                    "MaterialOnly": 0.0,
                    "Labor": 0.0,
                    "MiscCharges": pdf_data.dollar_value,
                    "InvoiceTotal": pdf_data.dollar_value,
                    "Balance": pdf_data.dollar_value,
                    "Lines": [],
                },
            }

            # Create second job with same data
            second_job_data = first_job_data.copy()
            second_job_data["order"]["PONumber"] = f"{pdf_data.po_number}-2"

            return redirect(url_for("preview_data", pdf_id=pdf_data.id))

        except Exception as e:
            logger.error(f"Error extracting data from PDF: {str(e)}")
            flash(f"Error extracting data: {str(e)}")
            return redirect(request.url)

    flash("Invalid file type. Please upload a PDF.")
    return redirect(request.url)


@app.route("/preview/<int:pdf_id>")
def preview_data(pdf_id):
    """Preview extracted data before creating quote/job."""
    pdf_data = PdfData.query.get_or_404(pdf_id)
    return render_template("preview.html", pdf_data=pdf_data)


@app.route("/api/customers/search", methods=["POST"])
def search_customers():
    """Search for customers in RFMS API by name or customer ID.
    For name searches, uses the locked-in builder search payload with pagination support:
        - includeCustomers: True
        - includeInactive: True
        - storeNumber: '49,1'
        - customerType: 'BUILDERS'
        - customerSource: 'Customer'
        - startIndex: (for pagination, default 0)
    The returned customer ID or customerSourceId should be used for the RFMS ID field in the UI and for uploads.
    """
    data = request.get_json()
    search_term = data.get("term", "") if data else ""
    start_index = int(data.get("start_index", 0)) if data else 0

    if not search_term:
        logger.warning("Empty search term provided")
        return (
            jsonify(
                {
                    "error": "Search term is required and must be sent as JSON in a POST request."
                }
            ),
            400,
        )

    try:
        logger.info(f"Searching for customers with term: {search_term}, start_index: {start_index}")
        # Check for approved customer in DB
        approved_matches = []
        if search_term:
            approved_matches = ApprovedCustomer.query.filter(
                (ApprovedCustomer.name.ilike(f"%{search_term}%")) |
                (ApprovedCustomer.business_name.ilike(f"%{search_term}%")) |
                (ApprovedCustomer.first_name.ilike(f"%{search_term}%")) |
                (ApprovedCustomer.last_name.ilike(f"%{search_term}%"))
            ).all()
            if approved_matches:
                logger.info(f"[APPROVED_CUSTOMER] Cache hit for search '{search_term}': {[a.rfms_customer_id for a in approved_matches]}")
                return jsonify([a.to_dict() for a in approved_matches])

        # If the term is all digits, treat as customer ID
        if search_term.isdigit():
            # find_customer_by_id already returns formatted dicts
            formatted_customers = ensure_rfms_api().find_customer_by_id(search_term)
        else:
            # Use locked-in builder search for name lookups, with pagination
            customers = ensure_rfms_api().find_customer_by_name(search_term, include_inactive=True, start_index=start_index)
            formatted_customers = ensure_rfms_api()._format_customer_list(customers)

        if not isinstance(formatted_customers, list) or not formatted_customers:
            logger.info(
                f"No customers found or bad response for search term: {search_term}"
            )
            logger.info(f"API response to frontend: []")
            return jsonify([])

        logger.info(
            f"Found {len(formatted_customers)} customers for search term: {search_term} (start_index: {start_index})"
        )
        logger.info(f"API response to frontend: {formatted_customers}")
        logger.info(f"[SEARCH_CUSTOMERS] Returning customer IDs: {[c['id'] for c in formatted_customers]}")
        return jsonify(formatted_customers)
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_customer", methods=["POST"])
def create_customer():
    """Create a new customer in RFMS."""
    data = request.json
    if data is None:
        return jsonify({"error": "No data provided"}), 400

    # Accept both old and new payloads
    if "customer" not in data and "ship_to" not in data:
        customer = data
        ship_to = data
    else:
        customer = data.get("customer", {})
        ship_to = data.get("ship_to", {})

    # Build the RFMS API payload structure correctly - using the successful structure from test_rfms_workflow.py
    payload = {
        "customerType": "INSURANCE",
        "entryType": "Customer",
        "customerAddress": {
            "firstName": customer.get("first_name") or ship_to.get("first_name", ""),
            "lastName": customer.get("last_name") or ship_to.get("last_name", ""),
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
        "taxStatus": "Tax",
        "taxMethod": "SalesTax",
        "storeNumber": "49",  # Use string format as in successful test
        "activeDate": datetime.now().strftime("%Y-%m-%d"),
        "preferredSalesperson1": customer.get("preferredSalesperson1", ""),
        "preferredSalesperson2": customer.get("preferredSalesperson2", ""),
        # Add all the flat fields that were in the successful payload
        "CustomerFirstName": customer.get("first_name") or ship_to.get("first_name", ""),
        "CustomerLastName": customer.get("last_name") or ship_to.get("last_name", ""),
        "CustomerAddress1": customer.get("address1") or ship_to.get("address1", ""),
        "CustomerAddress2": customer.get("address2") or ship_to.get("address2", ""),
        "CustomerCity": customer.get("city") or ship_to.get("city", ""),
        "CustomerState": customer.get("state") or ship_to.get("state", ""),
        "CustomerPostalCode": customer.get("zip_code") or ship_to.get("zip_code", ""),
        "CustomerCounty": "",
        "ShipToFirstName": ship_to.get("first_name") or customer.get("first_name", ""),
        "ShipToLastName": ship_to.get("last_name") or customer.get("last_name", ""),
        "ShipToAddress1": ship_to.get("address1") or ship_to.get("address", "") or customer.get("address1", ""),
        "ShipToAddress2": ship_to.get("address2") or customer.get("address2", ""),
        "ShipToCity": ship_to.get("city") or customer.get("city", ""),
        "ShipToState": ship_to.get("state") or customer.get("state", ""),
        "ShipToPostalCode": ship_to.get("zip_code") or customer.get("zip_code", ""),
        "ShipToCounty": "",
        "Phone2": customer.get("phone2") or "",
        "Phone3": customer.get("phone3") or "",
        "ShipToLocked": False,
        "SalesPerson1": "ZORAN VEKIC",
        "SalesPerson2": "",
        "SalesRepLocked": False,
        "CommisionSplitPercent": 0.0,
        "Store": 1
    }
    
    logger.info(f"[CREATE_CUSTOMER] Outgoing payload: {json.dumps(payload, indent=2)}")
    try:
        result = ensure_rfms_api().create_customer(payload)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_quote", methods=["POST"])
def create_quote():
    """Create a new quote in RFMS."""
    quote_data = request.json
    customer_id = quote_data.get('customer_id')
    logger.info(f"[CREATE_QUOTE] Using customer ID: {customer_id}")
    if not customer_id:
        logger.error("[CREATE_QUOTE] Missing customer_id in quote_data")
        return jsonify({"error": "Missing customer_id in quote data."}), 400
    try:
        result = ensure_rfms_api().create_quote(quote_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating quote: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/create_job", methods=["POST"])
def create_job():
    """Create a new job in RFMS."""
    job_data = request.json
    customer_id = None
    if job_data and 'order' in job_data:
        customer_id = job_data['order'].get('CustomerSeqNum')
    logger.info(f"[CREATE_JOB] Using customer ID: {customer_id}")
    if not customer_id:
        logger.error("[CREATE_JOB] Missing customer ID in job_data['order']")
        return jsonify({"error": "Missing customer ID in job data."}), 400
    try:
        result = ensure_rfms_api().create_job(job_data)

        # Handle billing group if applicable
        if job_data.get("is_billing_group", False):
            prefix = job_data.get("po_prefix", "")
            suffix = job_data.get("po_suffix", "")
            second_value = job_data.get("second_value", 0)

            # Create second job with suffix
            second_job_data = job_data.copy()
            second_job_data["po_number"] = f"{prefix}-{suffix}"
            second_job_data["dollar_value"] = second_value

            second_result = ensure_rfms_api().create_job(second_job_data)

            # Add both jobs to a billing group
            group_result = ensure_rfms_api().add_to_billing_group(
                [result["id"], second_result["id"]]
            )
            return jsonify(
                {
                    "first_job": result,
                    "second_job": second_result,
                    "billing_group": group_result,
                }
            )

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/check_status")
def check_api_status():
    """Check RFMS API connectivity status."""
    try:
        status = ensure_rfms_api().check_status()
        return jsonify({"status": status})
    except Exception as e:
        logger.error(f"API status check failed: {str(e)}")
        return jsonify({"status": "offline", "error": str(e)}), 500


@app.route("/api/export-to-rfms", methods=["POST"])
def export_to_rfms():
    """Export customer, job, and order data to RFMS API."""
    try:
        data = request.json
        if not data:
            logger.warning("No data provided for RFMS export")
            return jsonify({"error": "No data provided for export"}), 400
        
        required_sections = ["sold_to", "ship_to", "job_details"]
        for section in required_sections:
            if section not in data:
                logger.warning(f"Missing required section: {section}")
                return jsonify({"error": f"Missing required section: {section}"}), 400
        
        logger.info("Starting export to RFMS")
        
        # Get the Sold To customer data (from search results)
        sold_to_data = data["sold_to"]
        sold_to_customer_id = sold_to_data.get("id") or sold_to_data.get("customer_source_id")
        
        logger.info(f"[EXPORT_TO_RFMS] Using Sold To customer ID: {sold_to_customer_id}")
        if not sold_to_customer_id:
            logger.error("[EXPORT_TO_RFMS] Missing Sold To customer ID")
            return jsonify({"error": "Missing Sold To customer ID"}), 400
        
        # Get Ship To data (from PDF extraction)
        ship_to_data = data["ship_to"]
        job_data = data["job_details"]
        alt_contact = data.get("alternate_contact", {})
        alt_contacts_list = data.get("alternate_contacts", [])
        
        # Use the sold-to customer for both sold-to and ship-to since it contains both addresses
        # The successful customer creation structure includes both customerAddress and shipToAddress
        ship_to_customer_id = sold_to_customer_id  # Use same customer ID for both
        
        logger.info(f"Using same customer ID for both Sold To and Ship To: {sold_to_customer_id}")
        
        # Build CustomNote from alternate contacts
        custom_note_lines = []
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
        
        # Description of works for Note field
        description = job_data.get("description_of_works", "")
        note_field = description.strip()
        
        # Extract dates
        measure_date = job_data.get("measure_date", "") or job_data.get("commencement_date", "")
        promise_date = job_data.get("promise_date", "") or job_data.get("completion_date", "")
        
        # Build JobNumber from supervisor name and phone
        supervisor_name = job_data.get("supervisor_name", "")
        supervisor_phone = job_data.get("supervisor_phone", "") or job_data.get("supervisor_mobile", "")
        job_number = f"{supervisor_name} {supervisor_phone}".strip() or job_data.get("po_number", "")
        
        # Phone mapping from PDF data
        phone1 = ship_to_data.get("phone", "")
        phone2 = ship_to_data.get("phone2", "") or ship_to_data.get("mobile", "")
        phone3 = ship_to_data.get("phone3", "") or ship_to_data.get("work_phone", "")
        
        # Ship To data from PDF extraction for the order fields
        ship_to_first_name = ship_to_data.get("first_name", "").strip() or "Unknown"
        ship_to_last_name = ship_to_data.get("last_name", "").strip() or "Customer"
        ship_to_address1 = (ship_to_data.get("address1", "") or ship_to_data.get("address", "")).strip() or "Address Required"
        ship_to_city = ship_to_data.get("city", "").strip() or "Brisbane"  # Use Brisbane as default
        ship_to_state = ship_to_data.get("state", "").strip() or "QLD"
        ship_to_postal_code = ship_to_data.get("zip_code", "").strip() or "4000"
        
        # Build the order payload according to the user's exact structure
        order_payload = {
            "username": "zoran.vekic",
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
                "CanEdit": False,
                "LockTaxes": False,
                "CustomerSource": "Customer",
                "CustomerSeqNum": sold_to_customer_id,
                "CustomerUpSeqNum": sold_to_customer_id,  # Use same customer for both
                # Customer data from selected "Sold To" customer
                "CustomerFirstName": sold_to_data.get("first_name", ""),
                "CustomerLastName": sold_to_data.get("last_name", ""),
                "CustomerAddress1": sold_to_data.get("address1", ""),
                "CustomerAddress2": sold_to_data.get("address2", ""),
                "CustomerCity": sold_to_data.get("city", ""),
                "CustomerState": sold_to_data.get("state", ""),
                "CustomerPostalCode": sold_to_data.get("zip_code", ""),
                "CustomerCounty": "",
                "Phone1": phone1,
                # Ship To data - use PDF extracted site address data
                "ShipToFirstName": ship_to_first_name,
                "ShipToLastName": ship_to_last_name,
                "ShipToAddress1": ship_to_address1,
                "ShipToAddress2": ship_to_data.get("address2", ""),
                "ShipToCity": ship_to_city,
                "ShipToState": ship_to_state,
                "ShipToPostalCode": ship_to_postal_code,
                "Phone2": phone2,
                "Phone3": phone3,
                "ShipToLocked": False,
                "SalesPerson1": "ZORAN VEKIC",
                "SalesPerson2": "",
                "SalesRepLocked": False,
                "CommisionSplitPercent": 0.0,
                "Store": 1,  # Changed back to 1 with correct endpoint
                "Email": ship_to_data.get("email", ""),
                "CustomNote": custom_note,  # Best Contacts etc...
                "Note": note_field,  # Description of works
                "WorkOrderNote": "",
                "PickingTicketNote": None,
                "OrderDate": "",
                "MeasureDate": measure_date,  # Commencement date from extracted pdf data
                "PromiseDate": promise_date,  # Completion date from extracted pdf data if available
                "PONumber": job_data.get("po_number", ""),  # PO Number from extracted pdf data
                "CustomerType": "INSURANCE",
                "JobNumber": job_number,  # Supervisor name and phone number from extracted pdf data
                "DateEntered": datetime.now().strftime("%Y-%m-%d"),  # Today's date
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
                "InstallStore": 1,  # Changed back to 1 with correct endpoint
                "AgeFrom": None,
                "Completed": None,
                "ReferralAmount": 0.0,
                "ReferralLocked": False,
                "PreAuthorization": None,
                "SalesTax": 0.0,
                "GrandInvoiceTotal": 0.0,
                "MaterialOnly": 0.0,
                "Labor": 0.0,
                "MiscCharges": float(job_data.get("dollar_value", 0)),  # Dollar Value from extracted pdf data
                "InvoiceTotal": 0.0,
                "MiscTax": 0.0,
                "RecycleFee": 0.0,
                "TotalPaid": 0.0,
                "Balance": 0.0,
                "DiscountRate": 0.0,
                "DiscountAmount": 0.0,
                "ApplyRecycleFee": False,
                "Attachements": None,  # Saved PDF - TODO: implement PDF attachment
                "PendingAttachments": None,
                "Order": None,
                "LockInfo": None,
                "Message": None,
                "Lines": []
            },
            "products": None
        }
        
        logger.info(f"Creating job in RFMS: {order_payload['order'].get('PONumber')}")
        logger.info(f"Using Sold To customer ID: {sold_to_customer_id}, Ship To customer ID: {ship_to_customer_id}")
        
        try:
            job_result = ensure_rfms_api().create_job(order_payload)
            job_id = job_result.get("id")
            logger.info(f"Job created in RFMS with ID: {job_id}")
            
            result = {
                "success": True,
                "message": "Successfully exported data to RFMS",
                "job": job_result,
                "ship_to_customer_id": ship_to_customer_id,
                "sold_to_customer_id": sold_to_customer_id
            }
            
            # Handle billing group if applicable
            if data.get("billing_group") and data.get("second_job_details"):
                second_job_data = data["second_job_details"]
                
                # Build second job payload with same structure
                second_order_payload = order_payload.copy()
                second_order_payload["order"] = order_payload["order"].copy()
                
                # Update specific fields for second job
                second_order_payload["order"]["PONumber"] = second_job_data.get("po_number", "")
                second_order_payload["order"]["MiscCharges"] = float(second_job_data.get("dollar_value", 0))
                second_order_payload["order"]["Note"] = second_job_data.get("description_of_works", "").strip()
                second_order_payload["order"]["MeasureDate"] = second_job_data.get("measure_date", "") or second_job_data.get("commencement_date", "")
                second_order_payload["order"]["PromiseDate"] = second_job_data.get("promise_date", "") or second_job_data.get("completion_date", "")
                
                # Build JobNumber for second job
                second_supervisor_name = second_job_data.get("supervisor_name", "")
                second_supervisor_phone = second_job_data.get("supervisor_phone", "") or second_job_data.get("supervisor_mobile", "")
                second_job_number = f"{second_supervisor_name} {second_supervisor_phone}".strip() or second_job_data.get("po_number", "")
                second_order_payload["order"]["JobNumber"] = second_job_number
                
                logger.info(f"Creating second job in RFMS: {second_order_payload['order'].get('PONumber')}")
                second_job_result = ensure_rfms_api().create_job(second_order_payload)
                second_job_id = second_job_result.get("id")
                logger.info(f"Second job created in RFMS with ID: {second_job_id}")
                
                # Add both jobs to a billing group
                billing_group_result = ensure_rfms_api().add_to_billing_group([job_id, second_job_id])
                result["second_job"] = second_job_result
                result["billing_group"] = billing_group_result
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error creating job in RFMS: {str(e)}")
            return jsonify({"error": f"Error creating job in RFMS: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error during RFMS export: {str(e)}")
        return jsonify({"error": f"Error during RFMS export: {str(e)}"}), 500


@app.route("/clear_data", methods=["POST"])
def clear_data():
    """Clear current extracted data for next upload."""
    session.pop("extracted_data", None)
    return redirect(url_for("index"))


@app.route("/api/approved_customer", methods=["POST"])
def save_approved_customer():
    data = request.json
    rfms_customer_id = data.get("customer_source_id") or data.get("id")
    if not rfms_customer_id:
        return jsonify({"error": "Missing customer_source_id"}), 400
    # Check if already exists
    approved = ApprovedCustomer.query.filter_by(rfms_customer_id=rfms_customer_id).first()
    if approved:
        # Update fields
        approved.name = data.get("name", approved.name)
        approved.first_name = data.get("first_name", approved.first_name)
        approved.last_name = data.get("last_name", approved.last_name)
        approved.business_name = data.get("business_name", approved.business_name)
        approved.address = data.get("address1", approved.address)
        approved.city = data.get("city", approved.city)
        approved.state = data.get("state", approved.state)
        approved.zip_code = data.get("zip_code", approved.zip_code)
        approved.country = data.get("country", approved.country)
        approved.phone = data.get("phone", approved.phone)
        approved.email = data.get("email", approved.email)
        db.session.commit()
        logger.info(f"[APPROVED_CUSTOMER] Updated: {approved}")
        return jsonify({"status": "updated", "customer": approved.to_dict()})
    # Create new
    approved = ApprovedCustomer(
        rfms_customer_id=rfms_customer_id,
        name=data.get("name"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        business_name=data.get("business_name"),
        address=data.get("address1"),
        city=data.get("city"),
        state=data.get("state"),
        zip_code=data.get("zip_code"),
        country=data.get("country"),
        phone=data.get("phone"),
        email=data.get("email"),
    )
    db.session.add(approved)
    db.session.commit()
    logger.info(f"[APPROVED_CUSTOMER] Saved: {approved}")
    return jsonify({"status": "saved", "customer": approved.to_dict()})


if __name__ == "__main__":
    with app.app_context():
        # Create database tables
        db.create_all()

    debug_mode = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

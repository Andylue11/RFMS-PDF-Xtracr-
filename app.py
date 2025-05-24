from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
from datetime import datetime
import tempfile

# Import models and database
from models import db, Customer, Quote, Job, PdfData

# Import utility modules
from utils.pdf_extractor import extract_data_from_pdf
from utils.rfms_api import RfmsApi

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///rfms_xtracr.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database with app
db.init_app(app)

# Initialize RFMS API client
rfms_api = RfmsApi(
    base_url=os.getenv('RFMS_BASE_URL', 'https://api.rfms.online'),
    store_code=os.getenv('RFMS_STORE_CODE'),
    username=os.getenv('RFMS_USERNAME'),
    api_key=os.getenv('RFMS_API_KEY')
)

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
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
        'total_uploads': total_uploads,
        'processed_uploads': processed_uploads,
        'quotes_created': quotes_created,
        'jobs_created': jobs_created
    }
    
    return render_template('index.html', recent_pdfs=recent_pdfs, stats=stats)

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf_api():
    """Handle PDF upload and extraction via API endpoint."""
    # Ensure RFMS session is ready for downstream actions
    session_ok = rfms_api.ensure_session()
    logger.info(f"RFMS session ready after PDF upload: {session_ok}, token: {rfms_api.session_token}, expiry: {rfms_api.session_expiry}")
    if not session_ok:
        return jsonify({"error": "Could not establish RFMS session. Please try again."}), 500
    if 'pdf_file' not in request.files:
        logger.warning("No file part in upload request.")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['pdf_file']
    
    if file.filename == '':
        logger.warning("No selected file in upload request.")
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create a temporary file path or use BytesIO directly if extractor supports it
        # Since the extractor takes a file path, saving to a temporary file is necessary
        
        # Use a temporary file that will be automatically deleted
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
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

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF upload and extraction."""
    if 'pdf_file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['pdf_file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Extract data from PDF
            extracted_data = extract_data_from_pdf(file_path)
            
            # Save extracted data to session for preview
            session['extracted_data'] = extracted_data
            
            # Save to database for persistence
            pdf_data = PdfData(
                filename=filename,
                customer_name=extracted_data.get('customer_name', ''),
                business_name=extracted_data.get('business_name', ''),
                po_number=extracted_data.get('po_number', ''),
                scope_of_work=extracted_data.get('scope_of_work', ''),
                dollar_value=extracted_data.get('dollar_value', 0),
                extracted_data=extracted_data,
                created_at=datetime.now()
            )
            
            db.session.add(pdf_data)
            db.session.commit()
            
            # Create first job
            first_job_data = {
                'username': 'zoran.vekic',
                'order': {
                    'CustomerSeqNum': pdf_data.customer_id,
                    'CustomerUpSeqNum': pdf_data.customer_id,
                    'PONumber': pdf_data.po_number,
                    'WorkOrderNote': pdf_data.scope_of_work,
                    'CustomerType': 'INSURANCE',
                    'UserOrderType': 12,
                    'ServiceType': 9,
                    'ContractType': 2,
                    'SalesPerson1': 'ZORAN VEKIC',
                    'Store': 1,
                    'InstallStore': 1,
                    'OrderDate': datetime.now().strftime('%Y-%m-%d'),
                    'DateEntered': datetime.now().strftime('%Y-%m-%d'),
                    'GrandInvoiceTotal': pdf_data.dollar_value,
                    'MaterialOnly': 0.0,
                    'Labor': 0.0,
                    'MiscCharges': pdf_data.dollar_value,
                    'InvoiceTotal': pdf_data.dollar_value,
                    'Balance': pdf_data.dollar_value,
                    'Lines': []
                }
            }

            # Create second job with same data
            second_job_data = first_job_data.copy()
            second_job_data['order']['PONumber'] = f"{pdf_data.po_number}-2"

            return redirect(url_for('preview_data', pdf_id=pdf_data.id))
        
        except Exception as e:
            logger.error(f"Error extracting data from PDF: {str(e)}")
            flash(f"Error extracting data: {str(e)}")
            return redirect(request.url)
    
    flash('Invalid file type. Please upload a PDF.')
    return redirect(request.url)

@app.route('/preview/<int:pdf_id>')
def preview_data(pdf_id):
    """Preview extracted data before creating quote/job."""
    pdf_data = PdfData.query.get_or_404(pdf_id)
    return render_template('preview.html', pdf_data=pdf_data)

@app.route('/api/customers/search', methods=['POST'])
def search_customers():
    """Search for customers in RFMS API by name or customer ID."""
    data = request.get_json()
    search_term = data.get('term', '') if data else ''
    
    if not search_term:
        logger.warning("Empty search term provided")
        return jsonify({"error": "Search term is required and must be sent as JSON in a POST request."}), 400

    try:
        logger.info(f"Searching for customers with term: {search_term}")
        # If the term is all digits, treat as customer ID
        if search_term.isdigit():
            customers = rfms_api.find_customer_by_id(search_term)
        else:
            customers = rfms_api.find_customer_by_name(search_term)
        
        if not isinstance(customers, list) or not customers:
            logger.info(f"No customers found or bad response for search term: {search_term}")
            logger.info(f"API response to frontend: []")
            return jsonify([])

        # Format response for frontend
        formatted_customers = []
        for customer in customers:
            if not isinstance(customer, dict):
                continue
            formatted_customer = {
                'id': customer.get('id'),
                'customer_source_id': customer.get('customer_source_id', customer.get('id')),
                'name': customer.get('name', ''),
                'first_name': customer.get('first_name', ''),
                'last_name': customer.get('last_name', ''),
                'business_name': customer.get('business_name', ''),
                'address': customer.get('address', ''),
                'address1': customer.get('address1', ''),
                'address2': customer.get('address2', ''),
                'city': customer.get('city', ''),
                'state': customer.get('state', ''),
                'zip_code': customer.get('zip_code', ''),
                'country': customer.get('country', '')
            }
            formatted_customers.append(formatted_customer)
        
        logger.info(f"Found {len(formatted_customers)} customers for search term: {search_term}")
        logger.info(f"API response to frontend: {formatted_customers}")
        return jsonify(formatted_customers)
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_customer', methods=['POST'])
def create_customer():
    """Create a new customer in RFMS."""
    customer_data = request.json
    try:
        result = rfms_api.create_customer(customer_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_quote', methods=['POST'])
def create_quote():
    """Create a new quote in RFMS."""
    quote_data = request.json
    try:
        result = rfms_api.create_quote(quote_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating quote: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/create_job', methods=['POST'])
def create_job():
    """Create a new job in RFMS."""
    job_data = request.json
    try:
        result = rfms_api.create_job(job_data)
        
        # Handle billing group if applicable
        if job_data.get('is_billing_group', False):
            prefix = job_data.get('po_prefix', '')
            suffix = job_data.get('po_suffix', '')
            second_value = job_data.get('second_value', 0)
            
            # Create second job with suffix
            second_job_data = job_data.copy()
            second_job_data['po_number'] = f"{prefix}-{suffix}"
            second_job_data['dollar_value'] = second_value
            
            second_result = rfms_api.create_job(second_job_data)
            
            # Add both jobs to a billing group
            group_result = rfms_api.add_to_billing_group([result['id'], second_result['id']])
            return jsonify({
                "first_job": result,
                "second_job": second_result,
                "billing_group": group_result
            })
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/check_status')
def check_api_status():
    """Check RFMS API connectivity status."""
    try:
        status = rfms_api.check_status()
        return jsonify({"status": status})
    except Exception as e:
        logger.error(f"API status check failed: {str(e)}")
        return jsonify({"status": "offline", "error": str(e)}), 500

@app.route('/api/export-to-rfms', methods=['POST'])
def export_to_rfms():
    """Export customer, job, and order data to RFMS API."""
    try:
        data = request.json
        if not data:
            logger.warning("No data provided for RFMS export")
            return jsonify({"error": "No data provided for export"}), 400
        required_sections = ['sold_to', 'ship_to', 'job_details']
        for section in required_sections:
            if section not in data:
                logger.warning(f"Missing required section: {section}")
                return jsonify({"error": f"Missing required section: {section}"}), 400
        logger.info("Starting export to RFMS")
        # 1. Create or update the Ship To customer in RFMS
        ship_to_data = data['ship_to']
        # Build the customer creation payload for Ship To
        customer_payload = {
            "customerType": ship_to_data.get('customer_type', 'INSURANCE'),
            "entryType": "Customer",
            "customerAddress": {
                "lastName": ship_to_data.get('last_name', ''),
                "firstName": ship_to_data.get('first_name', ''),
                "address1": ship_to_data.get('address1', ''),
                "address2": ship_to_data.get('address2', ''),
                "city": ship_to_data.get('city', ''),
                "state": ship_to_data.get('state', ''),
                "postalCode": ship_to_data.get('zip_code', ''),
                "county": ship_to_data.get('county', '')
            },
            "phone1": ship_to_data.get('phone', ''),
            "phone2": ship_to_data.get('phone2', ''),
            "email": ship_to_data.get('email', ''),
            "taxStatus": "Tax",
            "taxMethod": "SalesTax",
            "preferredSalesperson1": "Zoran Vekic",
            "preferredSalesperson2": "",
            "storeNumber": 49
        }
        logger.info(f"Creating/updating Ship To customer: {ship_to_data.get('name')}")
        try:
            ship_to_result = rfms_api.create_customer(customer_payload)
            ship_to_customer_id = ship_to_result.get('id')
            logger.info(f"Ship To customer created/updated with ID: {ship_to_customer_id}")
        except Exception as e:
            logger.error(f"Error creating Ship To customer: {str(e)}")
            return jsonify({"error": f"Error creating Ship To customer: {str(e)}"}), 500
        # 2. Get the Sold To customer ID (assumes it was already obtained via search)
        sold_to_data = data['sold_to']
        sold_to_customer_id = sold_to_data.get('id')
        if not sold_to_customer_id:
            logger.warning("Missing Sold To customer ID")
            return jsonify({"error": "Missing Sold To customer ID"}), 400
        # 3. Create the job in RFMS
        job_data = data['job_details']
        alt_contact = data.get('alternate_contact', {})
        description = job_data.get('description_of_works', '')
        alt_contacts_list = data.get('alternate_contacts', [])
        # Private notes is now the PDF-extracted description
        private_notes = description.rstrip('\n')
        # Note/WorkOrderNote are now just the contact info
        notes_lines = []
        if alt_contact and (alt_contact.get('name') or alt_contact.get('phone') or alt_contact.get('phone2') or alt_contact.get('email')):
            best_contact_str = f"Best Contact: {alt_contact.get('name', '')} {alt_contact.get('phone', '')}"
            if alt_contact.get('phone2'):
                best_contact_str += f", {alt_contact.get('phone2')}"
            if alt_contact.get('email'):
                best_contact_str += f" ({alt_contact.get('email')})"
            notes_lines.append(best_contact_str)
        for contact in alt_contacts_list:
            if contact.get('name') or contact.get('phone') or contact.get('phone2') or contact.get('email'):
                line = f"{contact.get('type', 'Contact')}: {contact.get('name', '')} {contact.get('phone', '')}"
                if contact.get('phone2'):
                    line += f", {contact.get('phone2')}"
                if contact.get('email'):
                    line += f" ({contact.get('email')})"
                notes_lines.append(line)
        notes_field = '\n'.join(notes_lines).rstrip('\n')
        # Extract measure/start date if present
        measure_date = job_data.get('measure_date', '')
        # Supervisor Name/Phone for JobNumber
        supervisor_name = job_data.get('supervisor_name', '')
        supervisor_phone = job_data.get('supervisor_phone', '')
        job_number = supervisor_name or supervisor_phone or job_data.get('po_number', '')
        # Phone1 from PDF data (main contact phone)
        phone1 = ship_to_data.get('phone', '').split()[0] if ship_to_data.get('phone') else ''
        # Phone2 from Ship To phone2 if present
        phone2 = ship_to_data.get('phone', '').split()[1] if ship_to_data.get('phone') and len(ship_to_data.get('phone').split()) > 1 else ''
        # Build the order payload for the first job
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
                "IsWebOrder": True,
                "Exported": False,
                "CanEdit": False,
                "LockTaxes": False,
                "CustomerSource": "",
                "CustomerSeqNum": sold_to_customer_id,
                "CustomerUpSeqNum": sold_to_customer_id,
                "CustomerFirstName": "",
                "CustomerLastName": "",
                "CustomerAddress1": "",
                "CustomerAddress2": "",
                "CustomerCity": "",
                "CustomerState": "",
                "CustomerPostalCode": "",
                "CustomerCounty": "",
                "Phone1": phone1,
                "ShipToFirstName": ship_to_data.get('first_name', ''),
                "ShipToLastName": ship_to_data.get('last_name', ''),
                "ShipToAddress1": ship_to_data.get('address1', ''),
                "ShipToAddress2": ship_to_data.get('address2', ''),
                "ShipToCity": ship_to_data.get('city', ''),
                "ShipToState": ship_to_data.get('state', ''),
                "ShipToPostalCode": ship_to_data.get('zip_code', ''),
                "ShipToCounty": "",
                "Phone2": phone2,
                "ShipToLocked": False,
                "SalesPerson1": "Zoran Vekic",
                "SalesPerson2": "",
                "SalesRepLocked": False,
                "CommisionSplitPercent": 0.0,
                "Store": 49,
                "Email": ship_to_data.get('email', ''),
                "CustomNote": "",
                "Note": notes_field,
                "WorkOrderNote": notes_field,
                "PrivateNotes": private_notes,
                "PickingTicketNote": None,
                "OrderDate": "",
                "MeasureDate": measure_date,
                "PromiseDate": "",
                "PONumber": job_data.get('po_number', ''),
                "CustomerType": "INSURANCE",
                "JobNumber": job_number,
                "DateEntered": datetime.now().strftime('%Y-%m-%d'),
                "DatePaid": None,
                "DueDate": "",
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
                "UserOrderType": 12,
                "ServiceType": 9,
                "ContractType": 2,
                "Timeslot": 0,
                "InstallStore": 49,
                "AgeFrom": None,
                "Completed": None,
                "ReferralAmount": 0.0,
                "ReferralLocked": False,
                "PreAuthorization": None,
                "SalesTax": 0.0,
                "GrandInvoiceTotal": "",
                "MaterialOnly": 0.0,
                "Labor": 0.0,
                "MiscCharges": job_data.get('dollar_value', 0),
                "InvoiceTotal": job_data.get('dollar_value', 0),
                "MiscTax": 0.0,
                "RecycleFee": 0.0,
                "TotalPaid": 0.0,
                "Balance": job_data.get('dollar_value', 0),
                "DiscountRate": 0.0,
                "DiscountAmount": 0.0,
                "ApplyRecycleFee": False,
                "Attachements": None,
                "PendingAttachments": None,
                "Order": None,
                "LockInfo": None,
                "Message": None,
                "Lines": [{
                    'productId': f'PO#$$',
                    'colorId': f'PO#$$',
                    'quantity': job_data.get('dollar_value', 0),
                    'priceLevel': 'Price4'
                }]
            }
        }
        logger.info(f"Creating job in RFMS: {order_payload['order'].get('PONumber')}")
        try:
            job_result = rfms_api.create_job(order_payload)
            job_id = job_result.get('id')
            logger.info(f"Job created in RFMS with ID: {job_id}")
            result = {
                'success': True,
                'message': 'Successfully exported data to RFMS',
                'ship_to_customer': ship_to_result,
                'job': job_result
            }
            # Billing group logic
            if data.get('billing_group') and data.get('second_job_details'):
                second_job_data = data['second_job_details']
                # Repeat the mapping for the second job
                second_description = second_job_data.get('description_of_works', '')
                # Private notes for second job is the PDF-extracted description
                second_private_notes = second_description.rstrip('\n')
                # Note/WorkOrderNote for second job is just the contact info (reuse logic if needed)
                second_notes_field = notes_field
                second_measure_date = second_job_data.get('measure_date', '')
                second_supervisor_name = second_job_data.get('supervisor_name', '')
                second_supervisor_phone = second_job_data.get('supervisor_phone', '')
                second_job_number = second_supervisor_name or second_supervisor_phone or second_job_data.get('po_number', '')
                second_order_payload = {
                    "username": "zoran.vekic",
                    "order": {
                        **order_payload['order'],
                        "PONumber": second_job_data.get('po_number', ''),
                        "MiscCharges": second_job_data.get('dollar_value', 0),
                        "InvoiceTotal": second_job_data.get('dollar_value', 0),
                        "Balance": second_job_data.get('dollar_value', 0),
                        "MeasureDate": second_measure_date,
                        "JobNumber": second_job_number,
                        "Note": second_notes_field,
                        "WorkOrderNote": second_notes_field,
                        "PrivateNotes": second_private_notes,
                        "PickingTicketNote": None,
                        "OrderDate": "",
                        "PromiseDate": "",
                        "PONumber": second_job_data.get('po_number', ''),
                        "CustomerType": "INSURANCE",
                        "DateEntered": datetime.now().strftime('%Y-%m-%d'),
                        "DatePaid": None,
                        "DueDate": "",
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
                        "UserOrderType": 12,
                        "ServiceType": 9,
                        "ContractType": 2,
                        "Timeslot": 0,
                        "InstallStore": 49,
                        "AgeFrom": None,
                        "Completed": None,
                        "ReferralAmount": 0.0,
                        "ReferralLocked": False,
                        "PreAuthorization": None,
                        "SalesTax": 0.0,
                        "GrandInvoiceTotal": "",
                        "MaterialOnly": 0.0,
                        "Labor": 0.0,
                        "MiscCharges": second_job_data.get('dollar_value', 0),
                        "InvoiceTotal": second_job_data.get('dollar_value', 0),
                        "MiscTax": 0.0,
                        "RecycleFee": 0.0,
                        "TotalPaid": 0.0,
                        "Balance": second_job_data.get('dollar_value', 0),
                        "DiscountRate": 0.0,
                        "DiscountAmount": 0.0,
                        "ApplyRecycleFee": False,
                        "Attachements": None,
                        "PendingAttachments": None,
                        "Order": None,
                        "LockInfo": None,
                        "Message": None,
                        "Lines": [{
                            'productId': f'PO#$$',
                            'colorId': f'PO#$$',
                            'quantity': second_job_data.get('dollar_value', 0),
                            'priceLevel': 'Price4'
                        }]
                    }
                }
                logger.info(f"Creating second job in RFMS: {second_order_payload['order'].get('PONumber')}")
                second_job_result = rfms_api.create_job(second_order_payload)
                second_job_id = second_job_result.get('id')
                logger.info(f"Second job created in RFMS with ID: {second_job_id}")
                # Add both jobs to a billing group
                billing_group_result = rfms_api.add_to_billing_group([job_id, second_job_id])
                result['second_job'] = second_job_result
                result['billing_group'] = billing_group_result
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error creating job in RFMS: {str(e)}")
            return jsonify({"error": f"Error creating job in RFMS: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error during RFMS export: {str(e)}")
        return jsonify({"error": f"Error during RFMS export: {str(e)}"}), 500

@app.route('/clear_data', methods=['POST'])
def clear_data():
    """Clear current extracted data for next upload."""
    session.pop('extracted_data', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
    
    debug_mode = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 
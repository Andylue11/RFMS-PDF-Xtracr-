import logging
import sys
from logging.handlers import RotatingFileHandler

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console output
        RotatingFileHandler(
            "app_dev.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting RFMS PDF XTRACR in development mode")
logger.debug("Debug logging enabled")

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime, timedelta
import tempfile
from test_rfms_api_connection import get_session_token, search_customers, get_customer_by_id, BASE_URL, STORE, API_KEY

# Import models and database
from models import db, Customer, Quote, Job, PdfData

# Import utility modules
from utils.pdf_extractor import extract_data_from_pdf
from utils.rfms_api import RfmsApi

# Load environment variables
load_dotenv()

# App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///rfms_xtracr_dev.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Development mode settings
app.config['DEBUG'] = True
app.config['TESTING'] = False

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database with app
db.init_app(app)

# Create database and tables if they don't exist
with app.app_context():
    db.create_all()
    logger.info("Development database initialized successfully")

# Initialize RFMS API client
rfms_api = RfmsApi(
    base_url=os.getenv('RFMS_BASE_URL'),
    store_code=os.getenv('RFMS_STORE_CODE'),
    username=os.getenv('RFMS_USERNAME'),
    api_key=os.getenv('RFMS_API_KEY')
)

# Verify RFMS API configuration
if not all([os.getenv('RFMS_BASE_URL'), os.getenv('RFMS_STORE_CODE'), 
           os.getenv('RFMS_USERNAME'), os.getenv('RFMS_API_KEY')]):
    logger.error("Missing required RFMS API configuration. Please check your .env file.")
    raise ValueError("Missing required RFMS API configuration")

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    logger.debug('Response Status: %s', response.status)
    logger.debug('Response Headers: %s', response.headers)
    return response

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
    if 'pdf_file' not in request.files:
        logger.warning("No file part in upload request.")
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['pdf_file']
    
    if file.filename == '':
        logger.warning("No selected file in upload request.")
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # Extract data from PDF
            extracted_data = extract_data_from_pdf(file_path)
            logger.info(f"Successfully extracted data for {filename}")
            
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
            
            # Return the extracted data as JSON
            return jsonify(extracted_data), 200
        
        except Exception as e:
            logger.error(f"Error extracting data from PDF {filename}: {str(e)}")
            # Clean up the file in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
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

@app.route('/api/check_status')
def check_api_status():
    """Check if the RFMS API is available."""
    try:
        session_token = get_session_token(BASE_URL)
        if session_token:
            return jsonify({'status': 'online'})
        return jsonify({'status': 'offline'})
    except Exception as e:
        logger.error(f"Error checking API status: {str(e)}")
        return jsonify({'status': 'offline'})

@app.route('/api/customers/search')
def search_customers_api():
    """Search for customers by name or exact ID."""
    search_term = request.args.get('term', '')
    page = int(request.args.get('page', 0))
    
    if not search_term:
        return jsonify({"results": [], "total": 0})
    
    logger.info(f"Searching for customers with term: {search_term}, page: {page}")
    
    try:
        # If the search term is a digit, treat as exact customer ID
        if search_term.isdigit():
            customer = rfms_api.find_customer_by_id(search_term)
            if customer:
                return jsonify({
                    "results": [customer],
                    "total": 1
                })
            else:
                return jsonify({
                    "results": [],
                    "total": 0
                })
        
        # Otherwise, do a fuzzy search with pagination
        customers = rfms_api.find_customers(search_term, page)
        total = rfms_api.get_customer_count(search_term)
        
        return jsonify({
            "results": customers,
            "total": total
        })
        
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
    try:
        job_data = request.json
        extracted_data = job_data.get('extracted_data', {})

        # Aggregate contacts for notes and ship-to phone
        contacts = []
        for contact in extracted_data.get('alternate_contacts', []):
            if contact.get('type') in ['Best Contact', 'Authorised Contact', 'Real Estate Agent', 'Tenant', 'Site Contact']:
                contacts.append(contact)

        # Build contact string for notes
        contact_lines = []
        for c in contacts:
            line = f"{c.get('type', '')}: {c.get('name', '')} {c.get('phone', '')} {c.get('email', '')}"
            contact_lines.append(line)

        # Work order notes
        work_order_notes = extracted_data.get('scope_of_work', '')
        if extracted_data.get('description_of_works'):
            work_order_notes += "\n" + extracted_data['description_of_works']
        if extracted_data.get('special_instructions'):
            work_order_notes += "\nSpecial Instructions: " + extracted_data['special_instructions']
        if contact_lines:
            work_order_notes += "\nContacts:\n" + "\n".join(contact_lines)

        # Private notes (could be the same or include more internal info)
        private_notes = work_order_notes

        # Public/custom notes (job description)
        public_notes = extracted_data.get('job_description', '') or extracted_data.get('scope_of_work', '')

        # Ship to phone
        ship_to_phone = ""
        if contacts:
            for c in contacts:
                if c.get('phone'):
                    ship_to_phone = c['phone']
                    break

        # Format job data according to RFMS API requirements
        formatted_job_data = {
            "username": job_data.get('username'),
            "order": {
                "poNumber": job_data.get('po_number'),
                "adSource": job_data.get('ad_source', ''),
                "quoteDate": job_data.get('quote_date'),
                "estimatedDeliveryDate": job_data.get('estimated_delivery_date'),
                "jobNumber": f"{job_data.get('supervisor_name', '')}{job_data.get('supervisor_mobile', '')}",
                "storeNumber": job_data.get('store_number', '49'),  # Default to store 49
                "privateNotes": private_notes,
                "publicNotes": public_notes,
                "workOrderNotes": work_order_notes,
                "customerId": job_data.get('sold_to_customer_id'),  # Use the existing customer ID
                "shipToAddress": {
                    "lastName": job_data.get('ship_to_last_name', ''),
                    "firstName": job_data.get('ship_to_first_name', ''),
                    "address1": job_data.get('ship_to_address', ''),
                    "address2": job_data.get('ship_to_address2', ''),
                    "city": job_data.get('ship_to_city', ''),
                    "state": job_data.get('ship_to_state', ''),
                    "postalCode": job_data.get('ship_to_zip_code', ''),
                    "county": job_data.get('ship_to_county', ''),
                    "phone2": ship_to_phone
                },
                "MiscCharges": float(job_data.get('dollar_value', 0)),
                "lines": []
            }
        }
        
        # Create the job
        job_result = rfms_api.create_job(formatted_job_data)
        
        # Handle billing group if needed
        if job_data.get('is_billing_group'):
            # Create second job with modified PO number
            second_job_data = formatted_job_data.copy()
            second_job_data['order']['poNumber'] = f"{job_data.get('po_prefix', '')}{job_data.get('po_suffix', '')}"
            second_value = float(job_data.get('second_value', 0))
            second_job_data['order']['MiscCharges'] = second_value
            # lines remains empty unless there are actual line items
            
            second_job_result = rfms_api.create_job(second_job_data)
            
            # Add both jobs to billing group
            billing_group = {
                "job1": job_result,
                "job2": second_job_result
            }
            
            return jsonify({
                "success": True,
                "message": "Jobs created successfully",
                "jobs": billing_group
            })
        
        return jsonify({
            "success": True,
            "message": "Job created successfully",
            "job": job_result
        })
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to create job: {str(e)}"
        }), 500

@app.route('/api/export-to-rfms', methods=['POST'])
def export_to_rfms():
    """Export customer, job, and order data to RFMS API."""
    try:
        # Get the data from the request
        data = request.json
        
        if not data:
            logger.warning("No data provided for RFMS export")
            return jsonify({"error": "No data provided for export"}), 400
        
        # Validate that we have the necessary data sections
        required_sections = ['sold_to', 'ship_to', 'job_details']
        for section in required_sections:
            if section not in data:
                logger.warning(f"Missing required section: {section}")
                return jsonify({"error": f"Missing required section: {section}"}), 400
        
        logger.info("Starting export to RFMS")
        
        # 1. Create or update the Ship To customer in RFMS
        ship_to_data = data['ship_to']
        logger.info(f"Creating/updating Ship To customer: {ship_to_data.get('name')}")
        
        try:
            ship_to_result = rfms_api.create_customer(ship_to_data)
            ship_to_customer_id = ship_to_result.get('id')
            logger.info(f"Ship To customer created/updated with ID: {ship_to_customer_id}")
        except Exception as e:
            logger.error(f"Error creating Ship To customer: {str(e)}")
            return jsonify({"error": f"Error creating Ship To customer: {str(e)}"}), 500
        
        # 2. Get the Sold To customer ID (assumes it was already obtained via search)
        sold_to_data = data['sold_to']
        sold_to_customer_id = sold_to_data.get('customerSourceId')
        
        if not sold_to_customer_id:
            logger.warning("Missing Sold To customer ID")
            return jsonify({"error": "Missing Sold To customer ID"}), 400
        
        # 3. Create the job in RFMS
        job_data = data['job_details']
        
        # If alternate_contact is present, append to description
        alt_contact = data.get('alternate_contact', {})
        description = job_data.get('description_of_works', '')
        # Add all alternate contacts from the list
        alt_contacts_list = data.get('alternate_contacts', [])
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
        if notes_lines:
            description += '\n' + '\n'.join(notes_lines)
        
        # Prepare the job data for the API
        po_number = job_data.get('po_number', '')
        dollar_value = job_data.get('dollar_value', 0)
        # Build lines array for the PO# line item
        lines = [{
            'productId': f'PO#$$',
            'colorId': f'PO#$$',
            'quantity': dollar_value,
            'priceLevel': 'Price4'
        }]
        
        # Prepare the job data using the new format
        prepared_job_data = {
            'sold_to_customer_id': sold_to_customer_id,
            'ship_to_customer_id': ship_to_customer_id,
            'po_number': po_number,
            'job_number': job_data.get('job_number'),
            'description_of_works': description,
            'dollar_value': dollar_value,
            'salesperson1': 'Zoran Vekic',
            'store_number': 49,  # Set to store 49
            'service_type_id': 1,
            'contract_type_id': 1,
            'user_order_type_id': 3,
            'lines': lines
        }
        
        logger.info(f"Creating job in RFMS: {prepared_job_data.get('po_number')}")
        
        try:
            # Create the main job
            job_result = rfms_api.create_job(prepared_job_data)
            job_id = job_result.get('id')
            logger.info(f"Job created in RFMS with ID: {job_id}")
            
            result = {
                'success': True,
                'message': 'Successfully exported data to RFMS',
                'ship_to_customer': ship_to_result,
                'job': job_result
            }
            
            # 4. Handle billing group/second PO if applicable
            billing_group_data = data.get('billing_group')
            if billing_group_data and billing_group_data.get('is_billing_group'):
                logger.info("Processing second job for billing group")
                
                po_prefix = job_data.get('actual_job_number', '')
                po_suffix = billing_group_data.get('po_suffix', '')
                second_value = billing_group_data.get('second_value', 0)
                
                if not po_suffix or second_value <= 0:
                    logger.warning("Invalid second job data: missing suffix or value ≤ 0")
                    return jsonify({"error": "Invalid second job data"}), 400
                
                # Create a copy of the job data for the second job
                second_job_data = prepared_job_data.copy()
                second_job_data['po_number'] = f"{po_prefix}-{po_suffix}"
                second_job_data['dollar_value'] = second_value
                # Update lines for the second job
                second_job_data['lines'] = [{
                    'productId': f'PO#$$',
                    'colorId': f'PO#$$',
                    'quantity': second_value,
                    'priceLevel': 'Price4'
                }]
                
                logger.info(f"Creating second job in RFMS: {second_job_data.get('po_number')}")
                
                try:
                    # Create the second job
                    second_job_result = rfms_api.create_job(second_job_data)
                    second_job_id = second_job_result.get('id')
                    logger.info(f"Second job created in RFMS with ID: {second_job_id}")
                    
                    # Add both jobs to a billing group
                    logger.info(f"Adding jobs to billing group: {job_id}, {second_job_id}")
                    billing_group_result = rfms_api.add_to_billing_group([job_id, second_job_id])
                    
                    # Add the second job and billing group results to the API response
                    result['second_job'] = second_job_result
                    result['billing_group'] = billing_group_result
                    
                except Exception as e:
                    logger.error(f"Error creating second job or billing group: {str(e)}")
                    # Still return success for the first job, but include the error
                    result['second_job_error'] = str(e)
            
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

@app.route('/api/search', methods=['GET'])
def api_search():
    term = request.args.get('term', '')
    start = int(request.args.get('start', 0))
    customers = search_customers(BASE_URL, term, start)
    return jsonify(customers or [])

@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def api_customer(customer_id):
    customer = get_customer_by_id(BASE_URL, customer_id)
    return jsonify(customer or {})

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
    
    # Run in development mode
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        use_reloader=True
    ) 
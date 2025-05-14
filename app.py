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
def upload_pdf():
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

@app.route('/api/customers/search')
def search_customers():
    """Search for customers in RFMS API."""
    search_term = request.args.get('term', '')
    
    if not search_term:
        logger.warning("Empty search term provided")
        return jsonify({"error": "Search term is required"}), 400
    
    try:
        logger.info(f"Searching for customers with term: {search_term}")
        customers = rfms_api.find_customers(search_term)
        
        if not customers:
            logger.info(f"No customers found for search term: {search_term}")
            return jsonify([])
        
        # Format response for frontend
        formatted_customers = []
        for customer in customers:
            formatted_customer = {
                'id': customer.get('id'),
                'customer_source_id': customer.get('customer_source_id'),
                'name': customer.get('name', ''),
                'first_name': customer.get('first_name', ''),
                'last_name': customer.get('last_name', ''),
                'business_name': customer.get('business_name', ''),
                'address': f"{customer.get('address1', '')}, {customer.get('city', '')}, {customer.get('state', '')} {customer.get('zip_code', '')}",
                'address1': customer.get('address1', ''),
                'address2': customer.get('address2', ''),
                'city': customer.get('city', ''),
                'state': customer.get('state', ''),
                'zip_code': customer.get('zip_code', ''),
                'country': customer.get('country', '')
            }
            formatted_customers.append(formatted_customer)
        
        logger.info(f"Found {len(formatted_customers)} customers for search term: {search_term}")
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
        sold_to_customer_id = sold_to_data.get('id')
        
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
            'store_number': 1,
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

if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
    
    debug_mode = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000))) 
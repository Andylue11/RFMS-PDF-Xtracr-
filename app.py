from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
from datetime import datetime

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

# Initialize database
db = SQLAlchemy(app)

# Initialize RFMS API client
rfms_api = RfmsApi(
    base_url=os.getenv('RFMS_BASE_URL', 'https://api.rfms.online'),
    store_code=os.getenv('RFMS_STORE_CODE'),
    username=os.getenv('RFMS_USERNAME'),
    api_key=os.getenv('RFMS_API_KEY')
)

# Import models after db initialization to avoid circular imports
from models.customer import Customer
from models.quote import Quote
from models.job import Job
from models.pdf_data import PdfData

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

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
    try:
        customers = rfms_api.find_customers(search_term)
        return jsonify(customers)
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
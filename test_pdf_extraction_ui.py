import pytest
from app import app
from utils.pdf_extractor import extract_data_from_pdf
import json
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_pdf_extraction_and_ui_mapping():
    """Test PDF extraction and verify data mapping to UI fields."""
    # Test PDF path - replace with your test PDF path
    pdf_path = "testing pdfs/EXTRACTR REFERENCE Purchase Order.pdf"
    
    # Extract data from PDF
    extracted_data = extract_data_from_pdf(pdf_path)
    
    # Verify essential fields are extracted
    assert 'customer_name' in extracted_data, "Customer name not extracted"
    assert 'po_number' in extracted_data, "PO number not extracted"
    assert 'dollar_value' in extracted_data, "Dollar value not extracted"
    assert 'scope_of_work' in extracted_data, "Scope of work not extracted"
    
    # Verify data types and formats
    assert isinstance(extracted_data['dollar_value'], (int, float)), "Dollar value should be numeric"
    assert isinstance(extracted_data['po_number'], str), "PO number should be string"
    assert isinstance(extracted_data['customer_name'], str), "Customer name should be string"
    
    # Verify address components
    assert 'address1' in extracted_data, "Address line 1 not extracted"
    assert 'city' in extracted_data, "City not extracted"
    assert 'state' in extracted_data, "State not extracted"
    assert 'zip_code' in extracted_data, "ZIP code not extracted"
    
    # Verify contact information
    assert 'phone' in extracted_data, "Phone number not extracted"
    assert 'email' in extracted_data, "Email not extracted"
    
    # Verify job information
    assert 'job_number' in extracted_data, "Job number not extracted"
    assert 'supervisor_name' in extracted_data, "Supervisor name not extracted"
    assert 'supervisor_mobile' in extracted_data, "Supervisor mobile not extracted"
    
    # Verify alternate contacts
    assert 'alternate_contacts' in extracted_data, "Alternate contacts not extracted"
    assert isinstance(extracted_data['alternate_contacts'], list), "Alternate contacts should be a list"
    
    # Print extracted data for manual verification
    print("\n=== EXTRACTED DATA ===")
    print(json.dumps(extracted_data, indent=2, default=str))
    
    # Verify data matches UI field requirements
    verify_ui_field_mapping(extracted_data)

def verify_ui_field_mapping(extracted_data):
    """Verify that extracted data matches UI field requirements."""
    # Builder Information fields
    assert 'first_name' in extracted_data, "First name required for UI"
    assert 'last_name' in extracted_data, "Last name required for UI"
    assert 'business_name' in extracted_data, "Business name required for UI"
    assert 'address' in extracted_data, "Address required for UI"
    assert 'city' in extracted_data, "City required for UI"
    assert 'state' in extracted_data, "State required for UI"
    assert 'zip_code' in extracted_data, "ZIP code required for UI"
    assert 'phone' in extracted_data, "Phone required for UI"
    assert 'email' in extracted_data, "Email required for UI"
    
    # Purchase Order Information fields
    assert 'po_number' in extracted_data, "PO number required for UI"
    assert 'dollar_value' in extracted_data, "Dollar value required for UI"
    assert 'scope_of_work' in extracted_data, "Scope of work required for UI"
    
    # Verify data formats match UI expectations
    if extracted_data['dollar_value']:
        assert isinstance(extracted_data['dollar_value'], (int, float)), "Dollar value must be numeric"
        assert extracted_data['dollar_value'] >= 0, "Dollar value must be non-negative"
    
    if extracted_data['zip_code']:
        assert len(str(extracted_data['zip_code'])) >= 4, "ZIP code must be at least 4 digits"
    
    if extracted_data['email']:
        assert '@' in extracted_data['email'], "Email must contain @ symbol"
    
    if extracted_data['phone']:
        # Remove non-digit characters for phone validation
        phone_digits = ''.join(filter(str.isdigit, str(extracted_data['phone'])))
        assert len(phone_digits) >= 8, "Phone number must have at least 8 digits"

def test_pdf_upload_endpoint(client):
    """Test the PDF upload endpoint and verify response data."""
    # Create a test PDF file
    test_pdf_path = "testing pdfs/test_upload.pdf"
    
    # Ensure the test PDF exists
    if not os.path.exists(test_pdf_path):
        pytest.skip(f"Test PDF not found: {test_pdf_path}")
    
    # Test file upload
    with open(test_pdf_path, 'rb') as pdf_file:
        response = client.post(
            '/upload-pdf',
            data={'pdf_file': (pdf_file, 'test.pdf')},
            content_type='multipart/form-data'
        )
    
    # Verify response
    assert response.status_code == 200, f"Upload failed with status {response.status_code}"
    
    # Parse response data
    response_data = json.loads(response.data)
    
    # Verify response contains required fields
    assert 'customer_name' in response_data, "Response missing customer name"
    assert 'po_number' in response_data, "Response missing PO number"
    assert 'dollar_value' in response_data, "Response missing dollar value"
    assert 'scope_of_work' in response_data, "Response missing scope of work"
    
    # Verify data types in response
    assert isinstance(response_data['dollar_value'], (int, float)), "Dollar value should be numeric"
    assert isinstance(response_data['po_number'], str), "PO number should be string"
    assert isinstance(response_data['customer_name'], str), "Customer name should be string"

if __name__ == '__main__':
    pytest.main(['-v', 'test_pdf_extraction_ui.py']) 
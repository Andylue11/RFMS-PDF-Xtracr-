import pytest
from unittest.mock import patch
import json
from io import BytesIO

from app import app

def test_upload_pdf_endpoint():
    """Tests the PDF upload endpoint."""
    client = app.test_client()
    
    # Mock the extract_data_from_pdf function to control its return value
    mock_extracted_data = {
        'customer_name': 'Test Customer',
        'po_number': 'TEST-123',
        'dollar_value': 100.50,
        'job_number': 'Test Supervisor 0400000000'
        # Add other relevant fields that the endpoint is expected to return
    }
    
    with patch('app.extract_data_from_pdf', return_value=mock_extracted_data) as mock_extractor:
        # Create a dummy file for testing upload
        # In a real test, you might use a small, valid PDF file
        # For this mock, we just need a file-like object
        data = {'pdf_file': (BytesIO(b'fake pdf data'), 'test.pdf')}
        
        # Send a POST request to the hypothetical upload endpoint
        response = client.post('/upload-pdf', data=data, content_type='multipart/form-data')
        
        # Assert the response status code
        assert response.status_code == 200
        
        # Assert that the extractor function was called once with the file path
        # We can't easily check the file path inside the test_client context
        # but we can check if it was called
        mock_extractor.assert_called_once()
        
        # Assert the JSON response contains the extracted data
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data == mock_extracted_data

# You might need to add BytesIO import if not available
# from io import BytesIO 
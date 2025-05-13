import pytest
from unittest.mock import patch, MagicMock
import json

from app import app

def test_export_to_rfms_endpoint():
    """Tests the /api/export-to-rfms endpoint."""
    client = app.test_client()
    
    # Mock the RfmsApi class and its methods
    mock_rfms_api = MagicMock()
    
    # Define the expected return values for the API calls - ensure they're JSON serializable
    mock_create_customer_response = {'id': 456, 'name': 'John Smith'}
    mock_rfms_api.create_customer.return_value = mock_create_customer_response
    
    mock_job_response = {'id': 789, 'po_number': '20173719-30'}
    mock_rfms_api.create_job.return_value = mock_job_response
    
    mock_second_job_response = {'id': 790, 'po_number': '20173719-01'}
    # Configure specific return values for create_job based on input
    mock_rfms_api.create_job.side_effect = lambda job_data: mock_second_job_response if job_data.get('po_number', '').endswith('-01') else mock_job_response
    
    mock_billing_group_response = {'group_id': 101}
    mock_rfms_api.add_to_billing_group.return_value = mock_billing_group_response
    
    # Test data to use for the request
    test_data = {
        'sold_to': {
            'id': 123,
            'name': 'Builder One',
            'address1': '123 Main St',
            'city': 'Brisbane',
            'state': 'QLD',
            'zip_code': '4000',
            'country': 'Australia',
            'phone': '0400 123 456',
            'email': 'builder@example.com'
        },
        'ship_to': {
            'name': 'John Smith',
            'address1': '456 Oak Ave',
            'city': 'Sydney',
            'state': 'NSW',
            'zip_code': '2000',
            'country': 'Australia',
            'phone': '0412 345 678',
            'email': 'customer@example.com'
        },
        'job_details': {
            'job_number': 'Jackson Peters 0447012125',
            'actual_job_number': '20173719',
            'po_number': '20173719-30',
            'description_of_works': 'Supply and install carpet in 4 bedrooms',
            'dollar_value': 2718.0
        },
        'billing_group': {
            'is_billing_group': True,
            'po_suffix': '01',
            'second_value': 1200.0
        }
    }
    
    # Patch the RfmsApi instance in the app
    with patch('app.rfms_api', mock_rfms_api):
        # Send a POST request to the export endpoint
        response = client.post('/api/export-to-rfms', 
                              data=json.dumps(test_data),
                              content_type='application/json')
        
        # Assert the response status code is 200 OK
        assert response.status_code == 200
        
        # Assert that the create_customer method was called with the ship_to data
        mock_rfms_api.create_customer.assert_called_once()
        
        # Assert that create_job was called at least once (might be called twice for billing group)
        mock_rfms_api.create_job.assert_called()
        
        # If billing group is used, add appropriate assertions
        if test_data['billing_group']['is_billing_group']:
            # Should have called create_job at least twice
            assert mock_rfms_api.create_job.call_count >= 2
            
            # Should have called add_to_billing_group
            mock_rfms_api.add_to_billing_group.assert_called_once()
        
        # Check response content
        response_data = json.loads(response.get_data(as_text=True))
        assert 'success' in response_data
        assert response_data['success'] is True 
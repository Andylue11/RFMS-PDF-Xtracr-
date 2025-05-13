import pytest
from unittest.mock import patch, MagicMock
import json

from app import app

def test_search_customers_endpoint():
    """Tests the /api/customers/search endpoint."""
    client = app.test_client()
    
    # Mock the RfmsApi class and its find_customers method
    mock_rfms_api = MagicMock()
    
    # Define the expected return value of find_customers
    mock_search_results = [
        {"id": 1, "name": "Builder One", "address": "123 Main St"},
        {"id": 2, "name": "Builder Two", "address": "456 Oak Ave"}
    ]
    mock_rfms_api.find_customers.return_value = mock_search_results
    
    # Patch the RfmsApi instance in the app
    with patch('app.rfms_api', mock_rfms_api):
        # Send a GET request to the search endpoint with a search term
        search_term = "Test Builder"
        response = client.get(f'/api/customers/search?term={search_term}')
        
        # Assert the response status code is 200 OK
        assert response.status_code == 200
        
        # Assert that the find_customers method was called with the correct search term
        mock_rfms_api.find_customers.assert_called_once_with(search_term)
        
        # Assert the JSON response contains the expected search results
        response_data = json.loads(response.get_data(as_text=True))
        assert response_data == mock_search_results 
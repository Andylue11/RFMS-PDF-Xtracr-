import pytest
import json
from app import app

def test_search_customers_endpoint():
    """Tests the /api/customers/search endpoint with a real request (no mocking)."""
    client = app.test_client()
    search_term = "Test Builder"
    response = client.post('/api/customers/search', json={"term": search_term})
    assert response.status_code == 200
    response_data = json.loads(response.get_data(as_text=True))
    assert isinstance(response_data, list)
    if response_data:
        customer = response_data[0]
        assert 'id' in customer
        assert 'name' in customer
        assert 'address1' in customer 
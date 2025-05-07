"""
Tests for the Paysafe API client.
"""

import pytest
import json
from unittest import mock

import requests

from paysafe import Client
from paysafe.exceptions import (
    AuthenticationError, 
    InvalidRequestError, 
    APIError, 
    NetworkError, 
    RateLimitError
)


class TestClient:
    """Tests for the Client class."""

    def test_init(self, api_key):
        """Test client initialization."""
        client = Client(api_key=api_key)
        assert client.api_key == api_key
        assert client.environment == "production"
        assert client.base_url == Client.DEFAULT_BASE_URL
        
        # Test sandbox environment
        sandbox_client = Client(api_key=api_key, environment="sandbox")
        assert sandbox_client.environment == "sandbox"
        assert sandbox_client.base_url == Client.SANDBOX_BASE_URL
        
        # Test custom base URL
        custom_url = "https://custom.api.com/"
        custom_client = Client(api_key=api_key, base_url=custom_url)
        assert custom_client.base_url == custom_url
    
    def test_default_headers(self, api_key):
        """Test default headers."""
        client = Client(api_key=api_key)
        headers = client._get_default_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Basic {api_key}"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "User-Agent" in headers
    
    @mock.patch('paysafe.api_client.Client._handle_response')
    @mock.patch('paysafe.api_client.Session.request')
    def test_request_success(self, mock_request, mock_handle_response):
        """Test successful API request."""
        # Set up mocks
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "payment123", "status": "COMPLETED"}
        mock_request.return_value = mock_response
        mock_handle_response.return_value = {"id": "payment123", "status": "COMPLETED"}
        
        # Create client
        client = Client(api_key="test_key")
        
        # Make request
        response = client.request("GET", "payments/payment123")
        
        # Verify response
        assert response == {"id": "payment123", "status": "COMPLETED"}
        mock_request.assert_called_once()
        mock_handle_response.assert_called_once_with(mock_response)
    
    def test_request_network_error(self, api_key):
        """Test handling of network errors."""
        # Create a real client with a non-existent host to trigger connection error
        client = Client(api_key=api_key, base_url="https://nonexistent-domain-123456789.com/v1/")
        
        # Test that the error is properly converted
        with pytest.raises(NetworkError) as exc_info:
            client.request("GET", "payments")
            
        assert "Network error" in str(exc_info.value)
    
    def test_handle_error_response(self):
        """Test handling of error responses from the API."""
        client = Client(api_key="test_key")
        
        # Test 400 error
        mock_response = mock.MagicMock()
        mock_response.status_code = 400
        mock_response.text = json.dumps({"error": {"code": "INVALID_REQUEST", "message": "Invalid request"}})
        mock_response.json.return_value = {"error": {"code": "INVALID_REQUEST", "message": "Invalid request"}}
        
        with pytest.raises(InvalidRequestError) as exc_info:
            client._handle_response(mock_response)
        assert "Invalid request" in str(exc_info.value)
        
        # Test 401 error
        mock_response.status_code = 401
        with pytest.raises(AuthenticationError) as exc_info:
            client._handle_response(mock_response)
        assert "Authentication error" in str(exc_info.value)
        
        # Test 429 error
        mock_response.status_code = 429
        with pytest.raises(RateLimitError) as exc_info:
            client._handle_response(mock_response)
        assert "Rate limit exceeded" in str(exc_info.value)
        
        # Test 500 error
        mock_response.status_code = 500
        # For the 500 error test, use an empty error response
        mock_response.json.return_value = {}
        mock_response.text = "{}"
        with pytest.raises(APIError) as exc_info:
            client._handle_response(mock_response)
        assert "Unknown error" in str(exc_info.value)
    
    @mock.patch('paysafe.api_client.Client.request')
    def test_get(self, mock_request):
        """Test GET request method."""
        # Set up mock
        mock_request.return_value = {"id": "customer123", "firstName": "John"}
        
        # Create client and make request
        client = Client(api_key="test_key")
        response = client.get("customers/customer123")
        
        # Verify response
        assert response == {"id": "customer123", "firstName": "John"}
        mock_request.assert_called_once_with(
            "GET", "customers/customer123", params=None, headers=None, retry_config=None
        )
    
    @mock.patch('paysafe.api_client.Client.request')
    def test_post(self, mock_request):
        """Test POST request method."""
        # Set up mock
        mock_request.return_value = {"id": "payment123", "status": "COMPLETED"}
        
        # Create client and make request
        client = Client(api_key="test_key")
        data = {"amount": 1000, "currencyCode": "USD"}
        response = client.post("payments", data=data)
        
        # Verify response
        assert response == {"id": "payment123", "status": "COMPLETED"}
        mock_request.assert_called_once_with(
            "POST", "payments", params=None, data=data, headers=None, retry_config=None
        )
    
    @mock.patch('paysafe.api_client.Client.request')
    def test_put(self, mock_request):
        """Test PUT request method."""
        # Set up mock
        mock_request.return_value = {"id": "customer123", "firstName": "John", "lastName": "Doe"}
        
        # Create client and make request
        client = Client(api_key="test_key")
        data = {"firstName": "John", "lastName": "Doe"}
        response = client.put("customers/customer123", data=data)
        
        # Verify response
        assert response == {"id": "customer123", "firstName": "John", "lastName": "Doe"}
        mock_request.assert_called_once_with(
            "PUT", "customers/customer123", params=None, data=data, headers=None, retry_config=None
        )
    
    @mock.patch('paysafe.api_client.Client.request')
    def test_delete(self, mock_request):
        """Test DELETE request method."""
        # Set up mock
        mock_request.return_value = {"deleted": True}
        
        # Create client and make request
        client = Client(api_key="test_key")
        response = client.delete("customers/customer123")
        
        # Verify response
        assert response == {"deleted": True}
        mock_request.assert_called_once_with(
            "DELETE", "customers/customer123", params=None, headers=None, retry_config=None
        )
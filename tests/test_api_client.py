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
    
    def test_request_success(self, client, mock_response):
        """Test successful API request."""
        # Setup mock response
        mock_response.json.return_value = {"id": "payment123", "status": "COMPLETED"}
        client.session.request.return_value = mock_response
        
        # Make request
        response = client.request("GET", "payments/payment123")
        
        # Verify response
        assert response == {"id": "payment123", "status": "COMPLETED"}
        client.session.request.assert_called_once()
    
    def test_request_network_error(self, api_key):
        """Test handling of network errors."""
        # Create a real client with a non-existent host to trigger connection error
        client = Client(api_key=api_key, base_url="https://nonexistent-domain-123456789.com/v1/")
        
        # Test that the error is properly converted
        with pytest.raises(NetworkError):
            client.request("GET", "payments/payment123")
    
    def test_request_timeout(self, api_key):
        """Test handling of timeout errors."""
        # Create a real client with a very small timeout
        client = Client(api_key=api_key, timeout=0.001)
        
        # Test that the error is properly converted - point to an unreachable IP to ensure timeout
        with pytest.raises(NetworkError):
            client.request("GET", "https://10.255.255.1/payments/payment123")
    
    def test_handle_error_response(self, client, mock_response):
        """Test handling of error responses from the API."""
        # Test 400 error
        mock_response.status_code = 400
        mock_response.text = json.dumps({"error": {"code": "INVALID_REQUEST", "message": "Invalid request"}})
        mock_response.json.return_value = {"error": {"code": "INVALID_REQUEST", "message": "Invalid request"}}
        
        with pytest.raises(InvalidRequestError) as exc_info:
            client._handle_response(mock_response)
        assert exc_info.value.code == "INVALID_REQUEST"
        assert "Invalid request" in str(exc_info.value)
        
        # Test 401 error
        mock_response.status_code = 401
        mock_response.text = json.dumps({"error": {"code": "UNAUTHORIZED", "message": "Unauthorized"}})
        mock_response.json.return_value = {"error": {"code": "UNAUTHORIZED", "message": "Unauthorized"}}
        
        with pytest.raises(AuthenticationError):
            client._handle_response(mock_response)
        
        # Test 429 error
        mock_response.status_code = 429
        mock_response.text = json.dumps({"error": {"code": "RATE_LIMIT", "message": "Rate limit exceeded"}})
        mock_response.json.return_value = {"error": {"code": "RATE_LIMIT", "message": "Rate limit exceeded"}}
        
        with pytest.raises(RateLimitError):
            client._handle_response(mock_response)
        
        # Test other error
        mock_response.status_code = 500
        mock_response.text = json.dumps({"error": {"code": "SERVER_ERROR", "message": "Internal server error"}})
        mock_response.json.return_value = {"error": {"code": "SERVER_ERROR", "message": "Internal server error"}}
        
        with pytest.raises(APIError):
            client._handle_response(mock_response)
    
    def test_get(self, client, mock_response):
        """Test GET request method."""
        mock_response.json.return_value = {"id": "customer123", "firstName": "John"}
        client.session.request.return_value = mock_response
        
        response = client.get("customers/customer123")
        
        assert response == {"id": "customer123", "firstName": "John"}
        client.session.request.assert_called_once_with(
            method="GET",
            url=mock.ANY,
            params=None,
            json=None,
            headers=None,
            timeout=mock.ANY
        )
    
    def test_post(self, client, mock_response):
        """Test POST request method."""
        mock_response.json.return_value = {"id": "payment123", "status": "COMPLETED"}
        client.session.request.return_value = mock_response
        
        data = {"amount": 1000, "currencyCode": "USD"}
        response = client.post("payments", data=data)
        
        assert response == {"id": "payment123", "status": "COMPLETED"}
        client.session.request.assert_called_once_with(
            method="POST",
            url=mock.ANY,
            params=None,
            json=data,
            headers=None,
            timeout=mock.ANY
        )
    
    def test_put(self, client, mock_response):
        """Test PUT request method."""
        mock_response.json.return_value = {"id": "customer123", "firstName": "John", "lastName": "Doe"}
        client.session.request.return_value = mock_response
        
        data = {"firstName": "John", "lastName": "Doe"}
        response = client.put("customers/customer123", data=data)
        
        assert response == {"id": "customer123", "firstName": "John", "lastName": "Doe"}
        client.session.request.assert_called_once_with(
            method="PUT",
            url=mock.ANY,
            params=None,
            json=data,
            headers=None,
            timeout=mock.ANY
        )
    
    def test_delete(self, client, mock_response):
        """Test DELETE request method."""
        mock_response.json.return_value = {"deleted": True}
        client.session.request.return_value = mock_response
        
        response = client.delete("customers/customer123")
        
        assert response == {"deleted": True}
        client.session.request.assert_called_once_with(
            method="DELETE",
            url=mock.ANY,
            params=None,
            json=None,
            headers=None,
            timeout=mock.ANY
        )

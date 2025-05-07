"""
Tests for the payload logging functionality.
"""

import json
import os
import logging
from unittest import mock

import pytest
from requests import Response

from paysafe import Client
from paysafe.models.customer import Customer


def test_payload_logging_enabled(payload_log_file):
    """Test that payload logging is properly set up."""
    # Verify that the log file exists and is empty at the start of the test
    assert os.path.exists(payload_log_file)
    
    # Create a client
    client = Client(api_key="test_api_key", environment="sandbox")
    
    # Mock the session.request method to avoid actual API calls
    client.session.request = mock.MagicMock()
    
    # Create a mock response
    mock_response = mock.MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = {"id": "cust_test123", "first_name": "John", "last_name": "Doe"}
    mock_response.text = json.dumps(mock_response.json.return_value)
    mock_response.content = mock_response.text.encode("utf-8")
    mock_response.headers = {"Content-Type": "application/json"}
    
    # Configure the mock to return our mock response
    client.session.request.return_value = mock_response
    
    # Perform a client request
    result = client.get("customers/cust_test123")
    
    # Verify the result
    assert result == {"id": "cust_test123", "first_name": "John", "last_name": "Doe"}
    
    # Verify the log file has content
    with open(payload_log_file, 'r') as f:
        log_content = f.read()
    
    # Check that our request and response were logged
    assert "REQUEST: GET" in log_content
    assert "customers/cust_test123" in log_content
    assert "RESPONSE STATUS: 200" in log_content
    assert "John" in log_content
    assert "Doe" in log_content
    
    print(f"\n✓ Payload logging test passed! Log file: {payload_log_file}")
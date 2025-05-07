"""
Demo script for the payload logging functionality.

This script shows how to set up and use the payload logging feature
to capture API request and response payloads.
"""

import json
import logging
import os
from unittest import mock
import tempfile

from paysafe import Client
from requests import Response


def setup_payload_logging():
    """Set up payload logging to a file."""
    # Create a temporary log file
    log_dir = tempfile.mkdtemp(prefix="paysafe_logs_")
    log_file = os.path.join(log_dir, "api_payloads.log")
    
    # Set up logging
    payload_logger = logging.getLogger("paysafe.api.payloads")
    payload_logger.setLevel(logging.DEBUG)
    
    # Create console handler for demonstration
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # Create file handler
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    
    # Add handlers to logger
    payload_logger.addHandler(ch)
    payload_logger.addHandler(fh)
    
    # Reset logger to avoid duplicate handlers in repeated runs
    payload_logger.propagate = False
    
    # Log file info
    payload_logger.info(f"API Payload Log File: {log_file}")
    payload_logger.info("="*80)
    
    print(f"\n🔍 API PAYLOAD LOG: {log_file}\n")
    
    return log_file


def simulate_api_request():
    """Simulate an API request with mock responses."""
    # Create a client
    client = Client(api_key="test_api_key", environment="sandbox")
    
    # Mock the session.request method to avoid actual API calls
    client.session.request = mock.MagicMock()
    
    # Create a mock response
    mock_response = mock.MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.ok = True
    mock_response.json.return_value = {
        "id": "cust_test123", 
        "first_name": "John", 
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "1234567890",
        "created_at": "2025-05-07T12:00:00Z"
    }
    mock_response.text = json.dumps(mock_response.json.return_value)
    mock_response.content = mock_response.text.encode("utf-8")
    mock_response.headers = {"Content-Type": "application/json"}
    
    # Configure the mock to return our mock response
    client.session.request.return_value = mock_response
    
    # Perform a client request
    print("\n📡 Making GET request to 'customers/cust_test123'...")
    result = client.get("customers/cust_test123")
    
    print(f"\n✓ Response received: {json.dumps(result, indent=2)}")
    
    # Now, make a POST request with data
    mock_response.json.return_value = {
        "id": "cust_new456", 
        "first_name": "Jane", 
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone": "9876543210",
        "created_at": "2025-05-07T13:00:00Z"
    }
    mock_response.text = json.dumps(mock_response.json.return_value)
    mock_response.content = mock_response.text.encode("utf-8")
    
    # Customer data to create
    customer_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "phone": "9876543210"
    }
    
    print("\n📡 Making POST request to 'customers' with data...")
    result = client.post("customers", data=customer_data)
    
    print(f"\n✓ Response received: {json.dumps(result, indent=2)}")
    
    return result


def main():
    """Run the payload logging demonstration."""
    print("\n🚀 Starting Paysafe SDK Payload Logging Demo")
    print("="*50)
    
    # Set up payload logging
    log_file = setup_payload_logging()
    
    # Simulate API requests
    simulate_api_request()
    
    # Display log file information
    print("\n✨ Demo completed!")
    print(f"📋 API payloads are logged to: {log_file}")
    print(f"📖 View log file contents with: cat {log_file}")
    print("="*50)


if __name__ == "__main__":
    main()
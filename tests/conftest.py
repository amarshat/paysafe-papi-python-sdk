"""
Test fixtures for the Paysafe Python SDK.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from unittest import mock

import pytest
from requests import Response

from paysafe import Client
from paysafe.models.card import Card
from paysafe.models.customer import Customer
from paysafe.models.payment import CardPaymentMethod, Payment


@pytest.fixture
def api_key():
    """Return a test API key."""
    # Use environment variable if available, otherwise use test key
    return os.environ.get("PAYSAFE_TEST_API_KEY", "test_api_key")


@pytest.fixture
def test_id():
    """Generate a unique ID for test resources."""
    return f"test_{uuid.uuid4().hex[:16]}"


@pytest.fixture
def successful_response():
    """Create a mock response setup function for successful API calls."""
    def _create_response(data: Dict[str, Any]) -> mock.Mock:
        response = mock.Mock(spec=Response)
        response.status_code = 200
        response.text = json.dumps(data)
        response.json.return_value = data
        response.headers = {"Content-Type": "application/json"}
        return response
    return _create_response


@pytest.fixture
def error_response():
    """Create a mock response setup function for error API calls."""
    def _create_response(status_code: int, error_msg: str, error_code: Optional[str] = None) -> mock.Mock:
        error_data = {
            "error": {
                "message": error_msg,
                "code": error_code
            }
        }
        response = mock.Mock(spec=Response)
        response.status_code = status_code
        response.text = json.dumps(error_data)
        response.json.return_value = error_data
        response.headers = {"Content-Type": "application/json"}
        return response
    return _create_response


@pytest.fixture
def mock_payment_response(successful_response):
    """Create a mock payment response."""
    payment_data = {
        "id": "pay_123456789",
        "merchantReferenceNumber": "ref_123456",
        "amount": 1000,
        "currencyCode": "USD",
        "status": "COMPLETED",
        "description": "Test payment",
        "gatewayResponse": {
            "transactionId": "tr_987654321"
        },
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    return successful_response(payment_data)


@pytest.fixture
def mock_customer_response(successful_response):
    """Create a mock customer response."""
    customer_data = {
        "id": "cust_123456789",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "phone": "1234567890",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    return successful_response(customer_data)


@pytest.fixture
def mock_card_response(successful_response):
    """Create a mock card response."""
    card_data = {
        "id": "card_123456789",
        "lastDigits": "1111",
        "cardType": "VISA",
        "expiryMonth": 12,
        "expiryYear": 25,
        "holderName": "John Doe",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    return successful_response(card_data)


@pytest.fixture
def mock_session(mock_payment_response, mock_customer_response, mock_card_response):
    """Create a mock session with predefined responses."""
    session = mock.Mock()
    
    # Set default responses
    session.request.return_value = mock_payment_response
    session.get.return_value = mock_payment_response
    session.post.return_value = mock_payment_response
    session.put.return_value = mock_payment_response
    session.delete.return_value = mock_payment_response
    
    return session


@pytest.fixture
def client(api_key, mock_session):
    """Create a test client with mocked session."""
    with mock.patch('paysafe.api_client.Session', return_value=mock_session):
        client = Client(api_key=api_key, environment="sandbox")
        client.session = mock_session
        return client


@pytest.fixture
def sample_customer() -> Customer:
    """Create a sample customer model for testing."""
    return Customer(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890"
    )


@pytest.fixture
def sample_card() -> Card:
    """Create a sample card model for testing."""
    return Card(
        card_number="4111111111111111",
        expiry={"month": 12, "year": 25},
        holder_name="John Doe",
        cvv="123"
    )


@pytest.fixture
def sample_payment() -> Payment:
    """Create a sample payment model for testing."""
    payment_method = CardPaymentMethod(
        card_number="4111111111111111",
        card_expiry={"month": 12, "year": 25},
        card_holder_name="John Doe",
        card_cvv="123"
    )
    
    return Payment(
        amount=1000,
        currency_code="USD",
        payment_method=payment_method,
        description="Test payment"
    )

"""
Fixtures for testing the Paysafe SDK.
"""

import json
from datetime import datetime
from unittest import mock

import pytest
from requests import Response

from paysafe import Client
from paysafe.models.customer import Customer, CustomerBillingDetails


@pytest.fixture
def client():
    """Mock Paysafe API client."""
    client = mock.MagicMock(spec=Client)
    client.session = mock.MagicMock()
    return client


@pytest.fixture
def successful_response():
    """Create a successful API response with provided data."""
    def _create_response(data):
        response = mock.MagicMock(spec=Response)
        response.status_code = 200
        response.ok = True
        response.json.return_value = data
        response.text = json.dumps(data)
        response.content = json.dumps(data).encode("utf-8")
        return response
    return _create_response


@pytest.fixture
def error_response():
    """Create an error API response with provided status code and error message."""
    def _create_response(status_code, error_message, error_code="ERROR"):
        response = mock.MagicMock(spec=Response)
        response.status_code = status_code
        response.ok = False
        error_data = {
            "error": {
                "code": error_code,
                "message": error_message,
                "details": []
            }
        }
        response.json.return_value = error_data
        response.text = json.dumps(error_data)
        response.content = json.dumps(error_data).encode("utf-8")
        return response
    return _create_response


@pytest.fixture
def sample_customer():
    """Sample customer data for testing."""
    return Customer(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
        billing_details=CustomerBillingDetails(
            street="123 Main St",
            city="Anytown",
            state="CA",
            country="US",
            zip="12345"
        )
    )
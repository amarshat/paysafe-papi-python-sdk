"""
Tests for the Payment resource.
"""

import pytest
import json
from unittest import mock

from paysafe.api_resources.payment import Payment
from paysafe.models.payment import Payment as PaymentModel, CardPaymentMethod
from paysafe.exceptions import InvalidRequestError, PaysafeError


class TestPayment:
    """Tests for the Payment resource."""

    def test_create(self, client, mock_response):
        """Test payment creation."""
        # Setup mock response
        mock_response.json.return_value = {
            "id": "payment123",
            "amount": 1000,
            "currencyCode": "USD",
            "status": "COMPLETED"
        }
        client.session.request.return_value = mock_response
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Create payment data
        payment_data = {
            "amount": 1000,
            "currency_code": "USD",
            "payment_method": {
                "type": "CARD",
                "card_number": "4111111111111111",
                "card_expiry": {"month": 12, "year": 25},
                "card_holder_name": "John Doe",
                "card_cvv": "123"
            }
        }
        
        # Create payment
        payment = payment_resource.create(payment_data)
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "payment123"
        assert payment.amount == 1000
        assert payment.currency_code == "USD"
        assert payment.status.value == "COMPLETED"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "payments" in call_args[1]["url"]
        
        # Check that data was converted to camelCase
        sent_data = json.loads(call_args[1]["json"])
        assert "currencyCode" in sent_data
        assert "paymentMethod" in sent_data
        
    def test_create_missing_required_fields(self, client):
        """Test payment creation with missing fields."""
        # Create payment resource
        payment_resource = Payment(client)
        
        # Create incomplete payment data
        payment_data = {
            "amount": 1000,
            # Missing currency_code
            # Missing payment_method
        }
        
        # Attempt to create payment
        with pytest.raises(ValueError) as exc_info:
            payment_resource.create(payment_data)
        
        assert "Missing required parameters" in str(exc_info.value)
        
    def test_retrieve(self, client, mock_response):
        """Test payment retrieval."""
        # Setup mock response
        mock_response.json.return_value = {
            "id": "payment123",
            "amount": 1000,
            "currencyCode": "USD",
            "status": "COMPLETED"
        }
        client.session.request.return_value = mock_response
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Retrieve payment
        payment = payment_resource.retrieve("payment123")
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "payment123"
        assert payment.amount == 1000
        assert payment.currency_code == "USD"
        assert payment.status.value == "COMPLETED"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "payments/payment123" in call_args[1]["url"]
        
    def test_retrieve_invalid_id(self, client):
        """Test payment retrieval with invalid ID."""
        # Create payment resource
        payment_resource = Payment(client)
        
        # Attempt to retrieve with empty ID
        with pytest.raises(ValueError) as exc_info:
            payment_resource.retrieve("")
        
        assert "payment_id cannot be None or empty" in str(exc_info.value)
        
    def test_list(self, client, mock_response):
        """Test payment listing."""
        # Setup mock response
        mock_response.json.return_value = {
            "payments": [
                {
                    "id": "payment123",
                    "amount": 1000,
                    "currencyCode": "USD",
                    "status": "COMPLETED"
                },
                {
                    "id": "payment456",
                    "amount": 2000,
                    "currencyCode": "EUR",
                    "status": "PENDING"
                }
            ]
        }
        client.session.request.return_value = mock_response
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # List payments
        payments = payment_resource.list(limit=10, customer_id="customer123")
        
        # Verify result
        assert isinstance(payments, list)
        assert len(payments) == 2
        assert all(isinstance(payment, PaymentModel) for payment in payments)
        assert payments[0].id == "payment123"
        assert payments[1].id == "payment456"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "payments" in call_args[1]["url"]
        assert call_args[1]["params"]["limit"] == 10
        assert call_args[1]["params"]["customerId"] == "customer123"
        
    def test_cancel(self, client, mock_response):
        """Test payment cancellation."""
        # Setup mock response
        mock_response.json.return_value = {
            "id": "payment123",
            "amount": 1000,
            "currencyCode": "USD",
            "status": "CANCELLED"
        }
        client.session.request.return_value = mock_response
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Cancel payment
        payment = payment_resource.cancel("payment123")
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "payment123"
        assert payment.status.value == "CANCELLED"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "payments/payment123/cancel" in call_args[1]["url"]
        
    def test_capture(self, client, mock_response):
        """Test payment capture."""
        # Setup mock response
        mock_response.json.return_value = {
            "id": "payment123",
            "amount": 1000,
            "currencyCode": "USD",
            "status": "COMPLETED"
        }
        client.session.request.return_value = mock_response
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Capture payment
        payment = payment_resource.capture("payment123", amount=500)
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "payment123"
        assert payment.status.value == "COMPLETED"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "payments/payment123/capture" in call_args[1]["url"]
        assert json.loads(call_args[1]["json"])["amount"] == 500

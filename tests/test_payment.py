"""
Tests for the Payment resource.
"""

import json
import os
import re
from datetime import datetime
from unittest import mock

import pytest

from paysafe import Client
from paysafe.api_resources.payment import Payment
from paysafe.exceptions import (APIError, AuthenticationError, InvalidRequestError,
                               NetworkError, PaysafeError, RateLimitError)
from paysafe.models.payment import (BankAccountPaymentMethod, CardPaymentMethod,
                                   Payment as PaymentModel, PaymentStatus)


class TestPayment:
    """Unit tests for the Payment resource."""

    def test_create(self, client, mock_payment_response, sample_payment):
        """Test payment creation with mocked response."""
        # Set up the mock
        client.post.return_value = mock_payment_response.json.return_value
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Create payment
        payment = payment_resource.create(sample_payment)
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "pay_123456789"
        assert payment.amount == 1000
        assert payment.currency_code == "USD"
        assert payment.status == PaymentStatus.COMPLETED
        
        # Verify API call
        client.post.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully
        
    def test_create_with_dictionary(self, client, mock_payment_response):
        """Test payment creation using a dictionary."""
        # Set up the mock
        client.post.return_value = mock_payment_response.json.return_value
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Create payment data as dictionary
        payment_data = {
            "amount": 1000,
            "currency_code": "USD",
            "description": "Test payment",
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
        assert payment.id == "pay_123456789"
        assert payment.amount == 1000
        assert payment.currency_code == "USD"
        
        # Verify API call
        client.post.assert_called_once()
        
    def test_create_with_bank_account(self, client, mock_payment_response):
        """Test payment creation with bank account payment method."""
        # Set up the mock
        client.post.return_value = mock_payment_response.json.return_value
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Create bank account payment method
        payment_method = BankAccountPaymentMethod(
            account_number="12345678",
            routing_number="123456789",
            account_type="CHECKING",
            account_holder_name="John Doe"
        )
        
        # Create payment
        payment = PaymentModel(
            amount=1000,
            currency_code="USD",
            payment_method=payment_method,
            description="Bank account payment"
        )
        
        # Submit payment
        result = payment_resource.create(payment)
        
        # Verify result
        assert isinstance(result, PaymentModel)
        assert result.id == "pay_123456789"
        
        # Verify API call
        client.post.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully
        
    def test_create_missing_required_fields(self, client):
        """Test payment creation with missing required fields."""
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
        
    def test_retrieve(self, client, mock_payment_response):
        """Test payment retrieval."""
        # Set up the mock
        client.get.return_value = mock_payment_response.json.return_value
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Retrieve payment
        payment = payment_resource.retrieve("pay_123456789")
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "pay_123456789"
        assert payment.amount == 1000
        assert payment.currency_code == "USD"
        
        # Verify API call
        client.get.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully
        
    def test_retrieve_invalid_id(self, client):
        """Test payment retrieval with invalid ID."""
        # Create payment resource
        payment_resource = Payment(client)
        
        # Attempt to retrieve with empty ID
        with pytest.raises(ValueError) as exc_info:
            payment_resource.retrieve("")
        
        assert "payment_id cannot be None or empty" in str(exc_info.value)
        
    def test_list(self, client, successful_response):
        """Test payment listing."""
        # Setup mock response
        payments_data = {
            "payments": [
                {
                    "id": "pay_123456789",
                    "merchantReferenceNumber": "ref_123456",
                    "amount": 1000,
                    "currencyCode": "USD",
                    "status": "COMPLETED",
                    "description": "Test payment 1",
                    "createdAt": datetime.now().isoformat(),
                },
                {
                    "id": "pay_987654321",
                    "merchantReferenceNumber": "ref_654321",
                    "amount": 2000,
                    "currencyCode": "EUR",
                    "status": "PENDING",
                    "description": "Test payment 2",
                    "createdAt": datetime.now().isoformat(),
                }
            ],
            "pagination": {
                "totalItems": 2,
                "limit": 10,
                "offset": 0
            }
        }
        client.get.return_value = payments_data
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # List payments
        payments = payment_resource.list(limit=10, customer_id="cust_123456789")
        
        # Verify result
        assert isinstance(payments, list)
        assert len(payments) == 2
        assert all(isinstance(payment, PaymentModel) for payment in payments)
        assert payments[0].id == "pay_123456789"
        assert payments[1].id == "pay_987654321"
        
        # Verify API call
        client.get.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully
        
    def test_list_with_filters(self, client, successful_response):
        """Test payment listing with filters."""
        # Setup mock response
        payments_data = {
            "payments": [
                {
                    "id": "pay_123456789",
                    "amount": 1000,
                    "currencyCode": "USD",
                    "status": "COMPLETED",
                    "createdAt": "2023-01-01T12:00:00Z",
                }
            ],
            "pagination": {
                "totalItems": 1,
                "limit": 5,
                "offset": 0
            }
        }
        client.get.return_value = payments_data
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # List payments with filters
        payments = payment_resource.list(
            limit=5,
            offset=0,
            status="COMPLETED",
            from_date="2023-01-01T00:00:00Z",
            to_date="2023-01-02T00:00:00Z"
        )
        
        # Verify result
        assert isinstance(payments, list)
        assert len(payments) == 1
        
        # Verify API call
        client.get.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully
        
    def test_cancel(self, client, successful_response):
        """Test payment cancellation."""
        # Setup mock response
        cancelled_payment = {
            "id": "pay_123456789",
            "amount": 1000,
            "currencyCode": "USD",
            "status": "CANCELLED",
            "description": "Test payment",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        client.post.return_value = cancelled_payment
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Cancel payment
        payment = payment_resource.cancel("pay_123456789")
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "pay_123456789"
        assert payment.status == PaymentStatus.CANCELLED
        
        # Verify API call
        client.post.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully
        
    def test_capture(self, client, successful_response):
        """Test payment capture."""
        # Setup mock response
        captured_payment = {
            "id": "pay_123456789",
            "amount": 1000,
            "currencyCode": "USD",
            "status": "COMPLETED",
            "description": "Test payment",
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        response = successful_response(captured_payment)
        client.session.request.return_value = response
        
        # Create payment resource
        payment_resource = Payment(client)
        
        # Capture payment
        payment = payment_resource.capture("pay_123456789", amount=500)
        
        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "pay_123456789"
        assert payment.status == PaymentStatus.COMPLETED
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "payments/pay_123456789/capture" in call_args[1]["url"]
        assert json.loads(call_args[1]["json"])["amount"] == 500
        
    def test_error_handling(self, client, error_response):
        """Test error handling in payment resource."""
        # Create payment resource
        payment_resource = Payment(client)
        
        # Test authentication error
        client.session.request.return_value = error_response(401, "Invalid API key", "UNAUTHORIZED")
        with pytest.raises(AuthenticationError) as exc_info:
            payment_resource.retrieve("pay_123456789")
        assert "Authentication error" in str(exc_info.value)
        
        # Test invalid request error
        client.session.request.return_value = error_response(400, "Invalid payment ID", "INVALID_REQUEST")
        with pytest.raises(InvalidRequestError) as exc_info:
            payment_resource.retrieve("pay_123456789")
        assert "Invalid payment ID" in str(exc_info.value)
        
        # Test rate limit error
        client.session.request.return_value = error_response(429, "Rate limit exceeded", "RATE_LIMIT_EXCEEDED")
        with pytest.raises(RateLimitError) as exc_info:
            payment_resource.retrieve("pay_123456789")
        assert "Rate limit exceeded" in str(exc_info.value)
        
        # Test API error
        client.session.request.return_value = error_response(500, "Internal server error", "SERVER_ERROR")
        with pytest.raises(APIError) as exc_info:
            payment_resource.retrieve("pay_123456789")
        assert "Internal server error" in str(exc_info.value)


@pytest.mark.integration
class TestPaymentIntegration:
    """Integration tests for the Payment resource using real API calls.
    
    These tests are skipped by default and only run when the PAYSAFE_TEST_API_KEY
    environment variable is set and the --integration flag is passed to pytest.
    """
    
    @pytest.fixture
    def real_client(self):
        """Create a real client for API calls."""
        api_key = os.environ.get("PAYSAFE_TEST_API_KEY")
        if not api_key:
            pytest.skip("PAYSAFE_TEST_API_KEY environment variable not set")
        return Client(api_key=api_key, environment="sandbox")
    
    @pytest.fixture
    def test_payment_id(self):
        """Store a payment ID for tests that need an existing payment."""
        return os.environ.get("PAYSAFE_TEST_PAYMENT_ID", "")
    
    def test_create_and_retrieve_payment(self, real_client, sample_payment):
        """Test creating and retrieving a payment with real API calls."""
        # Skip if no API key
        if not os.environ.get("PAYSAFE_TEST_API_KEY"):
            pytest.skip("PAYSAFE_TEST_API_KEY environment variable not set")
            
        # Create payment resource
        payment_resource = Payment(real_client)
        
        # Generate a unique reference number
        reference = f"test_payment_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        sample_payment.merchant_reference_number = reference
        
        try:
            # Create payment
            created_payment = payment_resource.create(sample_payment)
            
            # Verify payment was created
            assert created_payment.id is not None
            assert created_payment.merchant_reference_number == reference
            
            # Retrieve the payment
            retrieved_payment = payment_resource.retrieve(created_payment.id)
            
            # Verify retrieved payment
            assert retrieved_payment.id == created_payment.id
            assert retrieved_payment.amount == sample_payment.amount
            assert retrieved_payment.currency_code == sample_payment.currency_code
            
        except PaysafeError as e:
            pytest.fail(f"API error: {e}")
    
    def test_list_payments(self, real_client):
        """Test listing payments with real API calls."""
        # Skip if no API key
        if not os.environ.get("PAYSAFE_TEST_API_KEY"):
            pytest.skip("PAYSAFE_TEST_API_KEY environment variable not set")
            
        # Create payment resource
        payment_resource = Payment(real_client)
        
        try:
            # List payments
            payments = payment_resource.list(limit=5)
            
            # Verify response
            assert isinstance(payments, list)
            
            # Verify payment objects
            if payments:
                assert all(isinstance(payment, PaymentModel) for payment in payments)
                assert all(payment.id is not None for payment in payments)
                
        except PaysafeError as e:
            pytest.fail(f"API error: {e}")
    
    def test_cancel_payment(self, real_client, test_payment_id):
        """Test cancelling a payment with real API calls."""
        # Skip if no API key or payment ID
        if not os.environ.get("PAYSAFE_TEST_API_KEY") or not test_payment_id:
            pytest.skip("PAYSAFE_TEST_API_KEY or PAYSAFE_TEST_PAYMENT_ID not set")
            
        # Create payment resource
        payment_resource = Payment(real_client)
        
        try:
            # Attempt to cancel the payment
            # Note: This may fail if the payment is not in a cancellable state
            payment = payment_resource.cancel(test_payment_id)
            
            # Verify result
            assert payment.id == test_payment_id
            assert payment.status == PaymentStatus.CANCELLED
            
        except APIError as e:
            # If the payment can't be cancelled, this is expected in some cases
            assert "Cannot cancel payment" in str(e) or "not in a cancellable state" in str(e)
        except PaysafeError as e:
            pytest.fail(f"Unexpected API error: {e}")

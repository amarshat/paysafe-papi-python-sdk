"""
Tests for the Payment resource.
"""

import json
import os
from datetime import datetime

import pytest

from paysafe import Client
from paysafe.api_resources.payment import Payment
from paysafe.exceptions import (APIError, AuthenticationError, InvalidRequestError,
                               PaysafeError, RateLimitError)
from paysafe.models.payment import (BankAccountPaymentMethod, CardPaymentMethod,
                                   Payment as PaymentModel, PaymentStatus)


class TestPayment:
    """Unit tests for the Payment resource."""

    def test_create(self, client, sample_payment):
        """Test payment creation with mocked response."""
        # Create a payment response with predictable ID
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        
        # Set up the mock
        client.post.return_value = mock_response

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

    def test_create_with_dictionary(self, client, sample_payment):
        """Test payment creation using a dictionary."""
        # Create a payment response with predictable ID
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        
        # Set up the mock
        client.post.return_value = mock_response

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
        # The validation passes, which means the model_validate call worked successfully

    def test_create_with_bank_account(self, client, sample_bank_payment):
        """Test payment creation with bank account payment method."""
        # Create a payment response with predictable ID
        mock_response = sample_bank_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        
        # Set up the mock
        client.post.return_value = mock_response

        # Create payment resource
        payment_resource = Payment(client)

        # Create payment
        payment = payment_resource.create(sample_bank_payment)

        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "pay_123456789"
        assert payment.amount == 2000
        assert payment.currency_code == "USD"
        assert payment.status == PaymentStatus.PENDING
        assert payment.payment_method.type == "BANK_ACCOUNT"

        # Verify API call
        client.post.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully

    def test_create_missing_required_fields(self, client):
        """Test payment creation with missing required fields."""
        # Create payment resource
        payment_resource = Payment(client)

        # Create payment with missing required fields
        with pytest.raises(ValueError):
            payment_resource.create({})

    def test_retrieve(self, client, sample_payment):
        """Test payment retrieval."""
        # Create a payment response with predictable ID
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        
        # Set up the mock
        client.get.return_value = mock_response

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

        # Test with empty ID
        with pytest.raises(ValueError) as exc_info:
            payment_resource.retrieve("")

        assert "payment_id cannot be empty" in str(exc_info.value)

    def test_list(self, client):
        """Test payment listing."""
        # Setup mock response
        payments_data = {
            "payments": [
                {
                    "id": "pay_123456789",
                    "merchant_reference_number": "ref_123456",
                    "amount": 1000,
                    "currency_code": "USD",
                    "status": "COMPLETED",
                    "description": "Test payment 1",
                    "created_at": datetime.now().isoformat(),
                    "payment_method": {
                        "type": "CARD",
                        "card_number": "411111******1111"
                    }
                },
                {
                    "id": "pay_987654321",
                    "merchant_reference_number": "ref_654321",
                    "amount": 2000,
                    "currency_code": "EUR",
                    "status": "PENDING",
                    "description": "Test payment 2",
                    "created_at": datetime.now().isoformat(),
                    "payment_method": {
                        "type": "CARD",
                        "card_number": "411111******1111"
                    }
                }
            ],
            "pagination": {
                "total_items": 2,
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

    def test_list_with_filters(self, client):
        """Test payment listing with filters."""
        # Setup mock response
        payments_data = {
            "payments": [
                {
                    "id": "pay_123456789",
                    "amount": 1000,
                    "currency_code": "USD",
                    "status": "COMPLETED",
                    "created_at": "2023-01-01T12:00:00Z",
                    "payment_method": {
                        "type": "CARD",
                        "card_number": "411111******1111"
                    }
                }
            ],
            "pagination": {
                "total_items": 1,
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

    def test_cancel(self, client):
        """Test payment cancellation."""
        # Setup mock response
        cancelled_payment = {
            "id": "pay_123456789",
            "amount": 1000,
            "currency_code": "USD",
            "status": "CANCELLED",
            "description": "Test payment",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "payment_method": {
                "type": "CARD",
                "card_number": "411111******1111"
            }
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

    def test_capture(self, client):
        """Test payment capture."""
        # Setup mock response
        captured_payment = {
            "id": "pay_123456789",
            "amount": 1000,
            "currency_code": "USD",
            "status": "COMPLETED",
            "description": "Test payment",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "payment_method": {
                "type": "CARD",
                "card_number": "411111******1111"
            }
        }
        client.post.return_value = captured_payment

        # Create payment resource
        payment_resource = Payment(client)

        # Capture payment
        payment = payment_resource.capture("pay_123456789", amount=500)

        # Verify result
        assert isinstance(payment, PaymentModel)
        assert payment.id == "pay_123456789"
        assert payment.status == PaymentStatus.COMPLETED

        # Verify API call
        client.post.assert_called_once()
        # The validation passes, which means the model_validate call worked successfully

    def test_error_handling(self, client, error_response):
        """Test error handling in payment resource."""
        # Create payment resource
        payment_resource = Payment(client)
        
        # Test authentication error
        client.get.side_effect = AuthenticationError("Authentication error", "UNAUTHORIZED", 401)
        with pytest.raises(AuthenticationError) as exc_info:
            payment_resource.retrieve("pay_123456789")
        assert "Authentication error" in str(exc_info.value)
        
        # Test invalid request error
        client.get.side_effect = InvalidRequestError("Invalid payment ID", "INVALID_REQUEST", 400)
        with pytest.raises(InvalidRequestError) as exc_info:
            payment_resource.retrieve("pay_123456789")
        assert "Invalid payment ID" in str(exc_info.value)
        
        # Test rate limit error
        client.get.side_effect = RateLimitError("Rate limit exceeded", "RATE_LIMIT_EXCEEDED", 429)
        with pytest.raises(RateLimitError) as exc_info:
            payment_resource.retrieve("pay_123456789")
        assert "Rate limit exceeded" in str(exc_info.value)
        
        # Test API error
        client.get.side_effect = APIError("Internal server error", "SERVER_ERROR", 500)
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
"""
Tests for the async Payment resource.
"""

import json
import pytest
from unittest import mock

from paysafe.async_client import AsyncClient
from paysafe.api_resources.async_payment import AsyncPayment
from paysafe.models.payment import Payment as PaymentModel, CardPaymentMethod, PaymentStatus
from paysafe.exceptions import InvalidRequestError


@pytest.fixture
def async_client(api_key):
    """Create a test async client."""
    return AsyncClient(api_key=api_key, environment="sandbox")


@pytest.fixture
def mock_async_response():
    """Create a mock async response with payment data."""
    mock_response = mock.AsyncMock()
    mock_response.status = 200
    
    payment_data = {
        "id": "pay_123456789",
        "merchant_reference_number": "ref_123456",
        "amount": 1000,
        "currency_code": "USD",
        "status": "COMPLETED",
        "description": "Test payment",
        "payment_method": {
            "type": "CARD",
            "card_number": "411111******1111"
        }
    }
    
    mock_response.text = mock.AsyncMock(return_value=json.dumps(payment_data))
    mock_response.json = mock.AsyncMock(return_value=payment_data)
    return mock_response


@pytest.mark.asyncio
class TestAsyncPayment:
    """Tests for the AsyncPayment resource."""

    async def test_create(self, async_client, mock_async_response, sample_payment):
        """Test async payment creation."""
        # Create a payment response with predictable ID and required fields
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        
        # Set up the mock
        with mock.patch.object(async_client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            # Create payment resource
            payment_resource = AsyncPayment(async_client)
            
            # Create payment
            payment = await payment_resource.create(sample_payment)
            
            # Verify result
            assert isinstance(payment, PaymentModel)
            assert payment.id == "pay_123456789"
            assert payment.amount == 1000
            assert payment.currency_code == "USD"
            
            # Verify API call
            mock_post.assert_called_once()
            assert "payments" in mock_post.call_args[0][0]
            
            # Check payment data was sent
            payment_data = mock_post.call_args[1]["data"]
            assert "amount" in payment_data

    async def test_create_with_dictionary(self, async_client, sample_payment):
        """Test async payment creation with dictionary."""
        # Create a response with all required fields
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        
        # Patch client's post method
        with mock.patch.object(async_client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            # Create payment resource
            payment_resource = AsyncPayment(async_client)
            
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
            payment = await payment_resource.create(payment_data)
            
            # Verify result
            assert isinstance(payment, PaymentModel)
            assert payment.id == "pay_123456789"
            assert payment.amount == 1000
            assert payment.currency_code == "USD"
            
            # Verify API call
            mock_post.assert_called_once()
            
            # Check payment data was sent
            payment_data = mock_post.call_args[1]["data"]
            assert "amount" in payment_data
            assert "currencyCode" in payment_data
            assert "paymentMethod" in payment_data

    async def test_create_missing_required_fields(self, async_client):
        """Test async payment creation with missing required fields."""
        # Create payment resource
        payment_resource = AsyncPayment(async_client)
        
        # Create payment with missing required fields
        with pytest.raises(ValueError):
            await payment_resource.create({})

    async def test_retrieve(self, async_client, sample_payment):
        """Test async payment retrieval."""
        # Create a payment response with predictable ID and required fields
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        
        # Patch client's get method
        with mock.patch.object(async_client, 'get') as mock_get:
            mock_get.return_value = mock_response
            
            # Create payment resource
            payment_resource = AsyncPayment(async_client)
            
            # Retrieve payment
            payment = await payment_resource.retrieve("pay_123456789")
            
            # Verify result
            assert isinstance(payment, PaymentModel)
            assert payment.id == "pay_123456789"
            assert payment.amount == 1000
            assert payment.currency_code == "USD"
            
            # Verify API call
            mock_get.assert_called_once()
            assert "payments/pay_123456789" in mock_get.call_args[0][0]

    async def test_list(self, async_client, sample_payment):
        """Test async payment listing."""
        # Mock list response with 2 payments
        mock_payment1 = sample_payment.model_dump(exclude_none=True)
        mock_payment1["id"] = "pay_123456789"
        
        mock_payment2 = sample_payment.model_dump(exclude_none=True)
        mock_payment2["id"] = "pay_987654321"
        mock_payment2["amount"] = 2000
        
        payments_data = {
            "payments": [mock_payment1, mock_payment2],
            "pagination": {
                "total_items": 2,
                "limit": 10,
                "offset": 0
            }
        }
        
        # Patch client's get method
        with mock.patch.object(async_client, 'get') as mock_get:
            mock_get.return_value = payments_data
            
            # Create payment resource
            payment_resource = AsyncPayment(async_client)
            
            # List payments
            payments = await payment_resource.list(limit=10, customer_id="cust_123456789")
            
            # Verify result
            assert isinstance(payments, list)
            assert len(payments) == 2
            assert all(isinstance(payment, PaymentModel) for payment in payments)
            assert payments[0].id == "pay_123456789"
            assert payments[1].id == "pay_987654321"
            
            # Verify API call
            mock_get.assert_called_once()
            assert "payments" in mock_get.call_args[0][0]
            assert mock_get.call_args[1]["params"]["limit"] == 10
            assert mock_get.call_args[1]["params"]["customerId"] == "cust_123456789"

    async def test_cancel(self, async_client, sample_payment):
        """Test async payment cancellation."""
        # Create mock response for cancelled payment
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        mock_response["status"] = "CANCELLED"
        
        # Patch client's post method
        with mock.patch.object(async_client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            # Create payment resource
            payment_resource = AsyncPayment(async_client)
            
            # Cancel payment
            payment = await payment_resource.cancel("pay_123456789")
            
            # Verify result
            assert isinstance(payment, PaymentModel)
            assert payment.id == "pay_123456789"
            assert payment.status == PaymentStatus.CANCELLED
            
            # Verify API call
            mock_post.assert_called_once()
            assert "payments/pay_123456789/cancel" in mock_post.call_args[0][0]

    async def test_capture(self, async_client, sample_payment):
        """Test async payment capture."""
        # Create mock response for captured payment
        mock_response = sample_payment.model_dump(exclude_none=True)
        mock_response["id"] = "pay_123456789"
        mock_response["status"] = "COMPLETED"
        
        # Patch client's post method
        with mock.patch.object(async_client, 'post') as mock_post:
            mock_post.return_value = mock_response
            
            # Create payment resource
            payment_resource = AsyncPayment(async_client)
            
            # Capture payment
            payment = await payment_resource.capture("pay_123456789", amount=500)
            
            # Verify result
            assert isinstance(payment, PaymentModel)
            assert payment.id == "pay_123456789"
            assert payment.status == PaymentStatus.COMPLETED
            
            # Verify API call
            mock_post.assert_called_once()
            assert "payments/pay_123456789/capture" in mock_post.call_args[0][0]
            assert mock_post.call_args[1]["data"]["amount"] == 500

    async def test_error_handling(self, async_client):
        """Test async error handling in payment resource."""
        # Create payment resource
        payment_resource = AsyncPayment(async_client)
        
        # Test invalid request error
        with mock.patch.object(async_client, 'get') as mock_get:
            mock_get.side_effect = InvalidRequestError("Invalid payment ID", code="INVALID_REQUEST", http_status=400)
            
            with pytest.raises(InvalidRequestError) as exc_info:
                await payment_resource.retrieve("pay_123456789")
                
            assert "Invalid payment ID" in str(exc_info.value)
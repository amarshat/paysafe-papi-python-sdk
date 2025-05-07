"""
Async Payment resource for the Paysafe Python SDK.
"""

from typing import Any, Dict, List, Optional, Union, cast

from paysafe.async_client import AsyncClient
from paysafe.models.payment import Payment as PaymentModel
from paysafe.utils import transform_keys_to_camel_case, transform_keys_to_snake_case, validate_id, validate_parameters


class AsyncPayment:
    """
    Async Payment operations for the Paysafe API.
    
    This class provides asynchronous methods to create, retrieve, and manage payments.
    """
    
    RESOURCE_PATH = "payments"
    
    def __init__(self, client: AsyncClient):
        """
        Initialize the AsyncPayment resource.
        
        Args:
            client: The Paysafe async API client.
        """
        self.client = client
    
    async def create(self, payment: Union[PaymentModel, Dict[str, Any]]) -> PaymentModel:
        """
        Create a new payment asynchronously.
        
        Args:
            payment: Payment data, either as a PaymentModel or dictionary.
            
        Returns:
            A PaymentModel instance with the created payment data.
            
        Raises:
            ValueError: If required parameters are missing.
            PaysafeError: If the API returns an error.
        """
        if isinstance(payment, PaymentModel):
            payment_data = payment.model_dump(exclude_none=True, by_alias=True)
        else:
            payment_data = payment
        
        validate_parameters(payment_data, ["amount", "currency_code", "payment_method"])
        
        # Convert snake_case to camelCase for the API
        payment_data = transform_keys_to_camel_case(payment_data)
        
        response = await self.client.post(self.RESOURCE_PATH, data=payment_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return PaymentModel.model_validate(response_data)
    
    async def retrieve(self, payment_id: str) -> PaymentModel:
        """
        Retrieve a payment by ID asynchronously.
        
        Args:
            payment_id: The ID of the payment to retrieve.
            
        Returns:
            A PaymentModel instance with the payment data.
            
        Raises:
            ValueError: If payment_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(payment_id, "payment_id")
        
        response = await self.client.get(f"{self.RESOURCE_PATH}/{payment_id}")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return PaymentModel.model_validate(response_data)
    
    async def list(
        self,
        limit: int = 10,
        offset: int = 0,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[PaymentModel]:
        """
        List payments with optional filtering asynchronously.
        
        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip for pagination.
            customer_id: Filter by customer ID.
            status: Filter by payment status.
            from_date: Filter by created date (ISO format).
            to_date: Filter by created date (ISO format).
            
        Returns:
            A list of PaymentModel instances.
            
        Raises:
            PaysafeError: If the API returns an error.
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        if customer_id:
            params["customerId"] = customer_id
        
        if status:
            params["status"] = status
        
        if from_date:
            params["fromDate"] = from_date
        
        if to_date:
            params["toDate"] = to_date
        
        response = await self.client.get(self.RESOURCE_PATH, params=params)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        payments_data = response_data.get("payments", [])
        return [PaymentModel.model_validate(payment) for payment in payments_data]
    
    async def cancel(self, payment_id: str) -> PaymentModel:
        """
        Cancel a payment asynchronously.
        
        Args:
            payment_id: The ID of the payment to cancel.
            
        Returns:
            A PaymentModel instance with the updated payment data.
            
        Raises:
            ValueError: If payment_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(payment_id, "payment_id")
        
        response = await self.client.post(f"{self.RESOURCE_PATH}/{payment_id}/cancel")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return PaymentModel.model_validate(response_data)
    
    async def capture(self, payment_id: str, amount: Optional[int] = None) -> PaymentModel:
        """
        Capture an authorized payment asynchronously.
        
        Args:
            payment_id: The ID of the payment to capture.
            amount: Optional amount to capture (defaults to full amount).
            
        Returns:
            A PaymentModel instance with the updated payment data.
            
        Raises:
            ValueError: If payment_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(payment_id, "payment_id")
        
        data = {}
        if amount is not None:
            data["amount"] = amount
        
        # Convert snake_case to camelCase for the API
        data = transform_keys_to_camel_case(data)
        
        response = await self.client.post(f"{self.RESOURCE_PATH}/{payment_id}/capture", data=data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return PaymentModel.model_validate(response_data)
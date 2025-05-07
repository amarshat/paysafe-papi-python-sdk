"""
Refund resource for the Paysafe Python SDK.
"""

from typing import Any, Dict, List, Optional, Union, cast

from paysafe.api_client import Client
from paysafe.models.refund import Refund as RefundModel
from paysafe.utils import transform_keys_to_camel_case, transform_keys_to_snake_case, validate_id, validate_parameters


class Refund:
    """
    Refund operations for the Paysafe API.
    
    This class provides methods to create, retrieve, and manage refunds.
    """
    
    def __init__(self, client: Client):
        """
        Initialize the Refund resource.
        
        Args:
            client: The Paysafe API client.
        """
        self.client = client
    
    def create(self, refund: Union[RefundModel, Dict[str, Any]]) -> RefundModel:
        """
        Create a new refund.
        
        Args:
            refund: Refund data, either as a RefundModel or dictionary.
            
        Returns:
            A RefundModel instance with the created refund data.
            
        Raises:
            ValueError: If required parameters are missing.
            PaysafeError: If the API returns an error.
        """
        if isinstance(refund, RefundModel):
            refund_data = refund.dict(exclude_none=True, by_alias=True)
        else:
            refund_data = refund
        
        validate_parameters(refund_data, ["payment_id", "amount", "currency_code"])
        
        # Convert snake_case to camelCase for the API
        refund_data = transform_keys_to_camel_case(refund_data)
        
        payment_id = refund_data.pop("paymentId")
        
        response = self.client.post(f"payments/{payment_id}/refunds", data=refund_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return RefundModel.parse_obj(response_data)
    
    def retrieve(self, payment_id: str, refund_id: str) -> RefundModel:
        """
        Retrieve a refund by ID.
        
        Args:
            payment_id: The ID of the payment that was refunded.
            refund_id: The ID of the refund to retrieve.
            
        Returns:
            A RefundModel instance with the refund data.
            
        Raises:
            ValueError: If payment_id or refund_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(payment_id, "payment_id")
        validate_id(refund_id, "refund_id")
        
        response = self.client.get(f"payments/{payment_id}/refunds/{refund_id}")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return RefundModel.parse_obj(response_data)
    
    def list(
        self,
        payment_id: str,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[RefundModel]:
        """
        List refunds for a payment with optional filtering.
        
        Args:
            payment_id: The ID of the payment whose refunds to list.
            limit: Maximum number of results to return.
            offset: Number of results to skip for pagination.
            status: Filter by refund status.
            
        Returns:
            A list of RefundModel instances.
            
        Raises:
            ValueError: If payment_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(payment_id, "payment_id")
        
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        if status:
            params["status"] = status
        
        response = self.client.get(f"payments/{payment_id}/refunds", params=params)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        refunds_data = response_data.get("refunds", [])
        return [RefundModel.parse_obj(refund) for refund in refunds_data]
    
    def cancel(self, payment_id: str, refund_id: str) -> RefundModel:
        """
        Cancel a pending refund.
        
        Args:
            payment_id: The ID of the payment that was refunded.
            refund_id: The ID of the refund to cancel.
            
        Returns:
            A RefundModel instance with the updated refund data.
            
        Raises:
            ValueError: If payment_id or refund_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(payment_id, "payment_id")
        validate_id(refund_id, "refund_id")
        
        response = self.client.post(f"payments/{payment_id}/refunds/{refund_id}/cancel")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return RefundModel.parse_obj(response_data)

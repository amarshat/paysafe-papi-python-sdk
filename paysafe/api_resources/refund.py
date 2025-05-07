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
            refund_data = refund.model_dump(exclude_none=True, by_alias=True)
        else:
            refund_data = refund
        
        validate_parameters(refund_data, ["payment_id", "amount", "currency_code"])
        
        # Convert snake_case to camelCase for the API
        refund_data = transform_keys_to_camel_case(refund_data)
        
        response = self.client.post("refunds", data=refund_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return RefundModel.model_validate(response_data)
    
    def retrieve(self, refund_id: str) -> RefundModel:
        """
        Retrieve a refund by ID.
        
        Args:
            refund_id: The ID of the refund to retrieve.
            
        Returns:
            A RefundModel instance with the refund data.
            
        Raises:
            ValueError: If refund_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(refund_id, "refund_id")
        
        response = self.client.get(f"refunds/{refund_id}")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return RefundModel.model_validate(response_data)
    
    def list(
        self,
        limit: int = 10,
        offset: int = 0,
        payment_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[RefundModel]:
        """
        List refunds with optional filtering.
        
        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip for pagination.
            payment_id: Filter by payment ID.
            status: Filter by refund status.
            
        Returns:
            A list of RefundModel instances.
            
        Raises:
            PaysafeError: If the API returns an error.
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        if payment_id:
            params["paymentId"] = payment_id
        
        if status:
            params["status"] = status
        
        response = self.client.get("refunds", params=params)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        refunds_data = response_data.get("refunds", [])
        return [RefundModel.model_validate(refund) for refund in refunds_data]
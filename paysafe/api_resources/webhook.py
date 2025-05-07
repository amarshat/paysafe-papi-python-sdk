"""
Webhook resource for the Paysafe Python SDK.
"""

from typing import Any, Dict, List, Optional, Union, cast

from paysafe.api_client import Client
from paysafe.models.webhook import Webhook as WebhookModel, WebhookPayload
from paysafe.utils import transform_keys_to_camel_case, transform_keys_to_snake_case, validate_id, validate_parameters


class Webhook:
    """
    Webhook operations for the Paysafe API.
    
    This class provides methods to create, retrieve, and manage webhooks.
    """
    
    RESOURCE_PATH = "webhooks"
    
    def __init__(self, client: Client):
        """
        Initialize the Webhook resource.
        
        Args:
            client: The Paysafe API client.
        """
        self.client = client
    
    def create(self, webhook: Union[WebhookModel, Dict[str, Any]]) -> WebhookModel:
        """
        Create a new webhook subscription.
        
        Args:
            webhook: Webhook data, either as a WebhookModel or dictionary.
            
        Returns:
            A WebhookModel instance with the created webhook data.
            
        Raises:
            ValueError: If required parameters are missing.
            PaysafeError: If the API returns an error.
        """
        if isinstance(webhook, WebhookModel):
            webhook_data = webhook.model_dump(exclude_none=True, by_alias=True)
        else:
            webhook_data = webhook
        
        validate_parameters(webhook_data, ["url", "events"])
        
        # Convert snake_case to camelCase for the API
        webhook_data = transform_keys_to_camel_case(webhook_data)
        
        response = self.client.post(self.RESOURCE_PATH, data=webhook_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return WebhookModel.model_validate(response_data)
    
    def retrieve(self, webhook_id: str) -> WebhookModel:
        """
        Retrieve a webhook by ID.
        
        Args:
            webhook_id: The ID of the webhook to retrieve.
            
        Returns:
            A WebhookModel instance with the webhook data.
            
        Raises:
            ValueError: If webhook_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(webhook_id, "webhook_id")
        
        response = self.client.get(f"{self.RESOURCE_PATH}/{webhook_id}")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return WebhookModel.model_validate(response_data)
    
    def update(
        self, webhook_id: str, webhook: Union[WebhookModel, Dict[str, Any]]
    ) -> WebhookModel:
        """
        Update a webhook.
        
        Args:
            webhook_id: The ID of the webhook to update.
            webhook: Updated webhook data, either as a WebhookModel or dictionary.
            
        Returns:
            A WebhookModel instance with the updated webhook data.
            
        Raises:
            ValueError: If webhook_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(webhook_id, "webhook_id")
        
        if isinstance(webhook, WebhookModel):
            webhook_data = webhook.model_dump(exclude_none=True, by_alias=True)
        else:
            webhook_data = webhook
        
        # Convert snake_case to camelCase for the API
        webhook_data = transform_keys_to_camel_case(webhook_data)
        
        response = self.client.put(f"{self.RESOURCE_PATH}/{webhook_id}", data=webhook_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return WebhookModel.model_validate(response_data)
    
    def delete(self, webhook_id: str) -> Dict[str, Any]:
        """
        Delete a webhook.
        
        Args:
            webhook_id: The ID of the webhook to delete.
            
        Returns:
            The API response.
            
        Raises:
            ValueError: If webhook_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(webhook_id, "webhook_id")
        
        response = self.client.delete(f"{self.RESOURCE_PATH}/{webhook_id}")
        
        return response
    
    def list(
        self,
        limit: int = 10,
        offset: int = 0,
        active: Optional[bool] = None,
    ) -> List[WebhookModel]:
        """
        List webhooks with optional filtering.
        
        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip for pagination.
            active: Filter by active status.
            
        Returns:
            A list of WebhookModel instances.
            
        Raises:
            PaysafeError: If the API returns an error.
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        if active is not None:
            params["active"] = active
        
        response = self.client.get(self.RESOURCE_PATH, params=params)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        webhooks_data = response_data.get("webhooks", [])
        return [WebhookModel.model_validate(webhook) for webhook in webhooks_data]
    
    @staticmethod
    def parse_webhook_payload(payload: Dict[str, Any]) -> WebhookPayload:
        """
        Parse a webhook event payload.
        
        Args:
            payload: The raw webhook payload as received from Paysafe.
            
        Returns:
            A WebhookPayload instance.
            
        Raises:
            ValueError: If the payload is invalid.
        """
        # Convert camelCase to snake_case for our models
        payload_data = transform_keys_to_snake_case(payload)
        
        return WebhookPayload.model_validate(payload_data)
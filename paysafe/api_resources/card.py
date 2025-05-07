"""
Card resource for the Paysafe Python SDK.
"""

from typing import Any, Dict, List, Optional, Union, cast

from paysafe.api_client import Client
from paysafe.models.card import Card as CardModel
from paysafe.utils import transform_keys_to_camel_case, transform_keys_to_snake_case, validate_id, validate_parameters


class Card:
    """
    Card operations for the Paysafe API.
    
    This class provides methods to create, retrieve, and manage cards.
    """
    
    def __init__(self, client: Client):
        """
        Initialize the Card resource.
        
        Args:
            client: The Paysafe API client.
        """
        self.client = client
    
    def create(self, customer_id: str, card: Union[CardModel, Dict[str, Any]]) -> CardModel:
        """
        Create a new card for a customer.
        
        Args:
            customer_id: The ID of the customer to associate the card with.
            card: Card data, either as a CardModel or dictionary.
            
        Returns:
            A CardModel instance with the created card data.
            
        Raises:
            ValueError: If customer_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        
        if isinstance(card, CardModel):
            card_data = card.dict(exclude_none=True, by_alias=True)
        else:
            card_data = card
        
        # Convert snake_case to camelCase for the API
        card_data = transform_keys_to_camel_case(card_data)
        
        response = self.client.post(f"customers/{customer_id}/cards", data=card_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return CardModel.parse_obj(response_data)
    
    def retrieve(self, customer_id: str, card_id: str) -> CardModel:
        """
        Retrieve a card by ID.
        
        Args:
            customer_id: The ID of the customer who owns the card.
            card_id: The ID of the card to retrieve.
            
        Returns:
            A CardModel instance with the card data.
            
        Raises:
            ValueError: If customer_id or card_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        validate_id(card_id, "card_id")
        
        response = self.client.get(f"customers/{customer_id}/cards/{card_id}")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return CardModel.parse_obj(response_data)
    
    def update(
        self, customer_id: str, card_id: str, card: Union[CardModel, Dict[str, Any]]
    ) -> CardModel:
        """
        Update a card.
        
        Args:
            customer_id: The ID of the customer who owns the card.
            card_id: The ID of the card to update.
            card: Updated card data, either as a CardModel or dictionary.
            
        Returns:
            A CardModel instance with the updated card data.
            
        Raises:
            ValueError: If customer_id or card_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        validate_id(card_id, "card_id")
        
        if isinstance(card, CardModel):
            card_data = card.dict(exclude_none=True, by_alias=True)
        else:
            card_data = card
        
        # Convert snake_case to camelCase for the API
        card_data = transform_keys_to_camel_case(card_data)
        
        response = self.client.put(f"customers/{customer_id}/cards/{card_id}", data=card_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return CardModel.parse_obj(response_data)
    
    def delete(self, customer_id: str, card_id: str) -> Dict[str, Any]:
        """
        Delete a card.
        
        Args:
            customer_id: The ID of the customer who owns the card.
            card_id: The ID of the card to delete.
            
        Returns:
            The API response.
            
        Raises:
            ValueError: If customer_id or card_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        validate_id(card_id, "card_id")
        
        response = self.client.delete(f"customers/{customer_id}/cards/{card_id}")
        
        return response
    
    def list(
        self,
        customer_id: str,
        limit: int = 10,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[CardModel]:
        """
        List cards for a customer with optional filtering.
        
        Args:
            customer_id: The ID of the customer whose cards to list.
            limit: Maximum number of results to return.
            offset: Number of results to skip for pagination.
            status: Filter by card status.
            
        Returns:
            A list of CardModel instances.
            
        Raises:
            ValueError: If customer_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        if status:
            params["status"] = status
        
        response = self.client.get(f"customers/{customer_id}/cards", params=params)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        cards_data = response_data.get("cards", [])
        return [CardModel.parse_obj(card) for card in cards_data]

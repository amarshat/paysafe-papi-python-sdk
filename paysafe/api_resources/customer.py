"""
Customer resource for the Paysafe Python SDK.
"""

from typing import Any, Dict, List, Optional, Union, cast

from paysafe.api_client import Client
from paysafe.models.customer import Customer as CustomerModel
from paysafe.utils import transform_keys_to_camel_case, transform_keys_to_snake_case, validate_id


class Customer:
    """
    Customer operations for the Paysafe API.
    
    This class provides methods to create, retrieve, and manage customers.
    """
    
    RESOURCE_PATH = "customers"
    
    def __init__(self, client: Client):
        """
        Initialize the Customer resource.
        
        Args:
            client: The Paysafe API client.
        """
        self.client = client
    
    def create(self, customer: Union[CustomerModel, Dict[str, Any]]) -> CustomerModel:
        """
        Create a new customer.
        
        Args:
            customer: Customer data, either as a CustomerModel or dictionary.
            
        Returns:
            A CustomerModel instance with the created customer data.
            
        Raises:
            PaysafeError: If the API returns an error.
        """
        if isinstance(customer, CustomerModel):
            customer_data = customer.dict(exclude_none=True, by_alias=True)
        else:
            customer_data = customer
        
        # Convert snake_case to camelCase for the API
        customer_data = transform_keys_to_camel_case(customer_data)
        
        response = self.client.post(self.RESOURCE_PATH, data=customer_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return CustomerModel.parse_obj(response_data)
    
    def retrieve(self, customer_id: str) -> CustomerModel:
        """
        Retrieve a customer by ID.
        
        Args:
            customer_id: The ID of the customer to retrieve.
            
        Returns:
            A CustomerModel instance with the customer data.
            
        Raises:
            ValueError: If customer_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        
        response = self.client.get(f"{self.RESOURCE_PATH}/{customer_id}")
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return CustomerModel.parse_obj(response_data)
    
    def update(
        self, customer_id: str, customer: Union[CustomerModel, Dict[str, Any]]
    ) -> CustomerModel:
        """
        Update a customer.
        
        Args:
            customer_id: The ID of the customer to update.
            customer: Updated customer data, either as a CustomerModel or dictionary.
            
        Returns:
            A CustomerModel instance with the updated customer data.
            
        Raises:
            ValueError: If customer_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        
        if isinstance(customer, CustomerModel):
            customer_data = customer.dict(exclude_none=True, by_alias=True)
        else:
            customer_data = customer
        
        # Convert snake_case to camelCase for the API
        customer_data = transform_keys_to_camel_case(customer_data)
        
        response = self.client.put(f"{self.RESOURCE_PATH}/{customer_id}", data=customer_data)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        return CustomerModel.parse_obj(response_data)
    
    def delete(self, customer_id: str) -> Dict[str, Any]:
        """
        Delete a customer.
        
        Args:
            customer_id: The ID of the customer to delete.
            
        Returns:
            The API response.
            
        Raises:
            ValueError: If customer_id is None or empty.
            PaysafeError: If the API returns an error.
        """
        validate_id(customer_id, "customer_id")
        
        response = self.client.delete(f"{self.RESOURCE_PATH}/{customer_id}")
        
        return response
    
    def list(
        self,
        limit: int = 10,
        offset: int = 0,
        email: Optional[str] = None,
        merchant_customer_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[CustomerModel]:
        """
        List customers with optional filtering.
        
        Args:
            limit: Maximum number of results to return.
            offset: Number of results to skip for pagination.
            email: Filter by customer email.
            merchant_customer_id: Filter by merchant's customer ID.
            status: Filter by customer status.
            
        Returns:
            A list of CustomerModel instances.
            
        Raises:
            PaysafeError: If the API returns an error.
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        
        if email:
            params["email"] = email
        
        if merchant_customer_id:
            params["merchantCustomerId"] = merchant_customer_id
        
        if status:
            params["status"] = status
        
        response = self.client.get(self.RESOURCE_PATH, params=params)
        
        # Convert camelCase to snake_case for our models
        response_data = transform_keys_to_snake_case(response)
        
        customers_data = response_data.get("customers", [])
        return [CustomerModel.parse_obj(customer) for customer in customers_data]

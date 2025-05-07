"""
Tests for the Customer resource.
"""

import pytest
import json
from unittest import mock

from paysafe.api_resources.customer import Customer
from paysafe.models.customer import Customer as CustomerModel
from paysafe.exceptions import InvalidRequestError, PaysafeError


class TestCustomer:
    """Tests for the Customer resource."""

    def test_create(self, client, mock_response):
        """Test customer creation."""
        # Setup mock response
        mock_response.json.return_value = {
            "id": "customer123",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "status": "ACTIVE"
        }
        client.session.request.return_value = mock_response
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Create customer data
        customer_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        # Create customer
        customer = customer_resource.create(customer_data)
        
        # Verify result
        assert isinstance(customer, CustomerModel)
        assert customer.id == "customer123"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.email == "john.doe@example.com"
        assert customer.status.value == "ACTIVE"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "customers" in call_args[1]["url"]
        
        # Check that data was converted to camelCase
        sent_data = json.loads(call_args[1]["json"])
        assert "firstName" in sent_data
        assert "lastName" in sent_data
        
    def test_retrieve(self, client, mock_response):
        """Test customer retrieval."""
        # Setup mock response
        mock_response.json.return_value = {
            "id": "customer123",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "status": "ACTIVE"
        }
        client.session.request.return_value = mock_response
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Retrieve customer
        customer = customer_resource.retrieve("customer123")
        
        # Verify result
        assert isinstance(customer, CustomerModel)
        assert customer.id == "customer123"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.email == "john.doe@example.com"
        assert customer.status.value == "ACTIVE"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "customers/customer123" in call_args[1]["url"]
        
    def test_retrieve_invalid_id(self, client):
        """Test customer retrieval with invalid ID."""
        # Create customer resource
        customer_resource = Customer(client)
        
        # Attempt to retrieve with empty ID
        with pytest.raises(ValueError) as exc_info:
            customer_resource.retrieve("")
        
        assert "customer_id cannot be None or empty" in str(exc_info.value)
        
    def test_update(self, client, mock_response):
        """Test customer update."""
        # Setup mock response
        mock_response.json.return_value = {
            "id": "customer123",
            "firstName": "John",
            "lastName": "Smith",  # Updated
            "email": "john.doe@example.com",
            "status": "ACTIVE"
        }
        client.session.request.return_value = mock_response
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Update data
        update_data = {
            "last_name": "Smith"
        }
        
        # Update customer
        customer = customer_resource.update("customer123", update_data)
        
        # Verify result
        assert isinstance(customer, CustomerModel)
        assert customer.id == "customer123"
        assert customer.last_name == "Smith"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "PUT"
        assert "customers/customer123" in call_args[1]["url"]
        
        # Check that data was converted to camelCase
        sent_data = json.loads(call_args[1]["json"])
        assert "lastName" in sent_data
        assert sent_data["lastName"] == "Smith"
        
    def test_delete(self, client, mock_response):
        """Test customer deletion."""
        # Setup mock response
        mock_response.json.return_value = {"deleted": True}
        client.session.request.return_value = mock_response
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Delete customer
        response = customer_resource.delete("customer123")
        
        # Verify result
        assert response == {"deleted": True}
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "DELETE"
        assert "customers/customer123" in call_args[1]["url"]
        
    def test_list(self, client, mock_response):
        """Test customer listing."""
        # Setup mock response
        mock_response.json.return_value = {
            "customers": [
                {
                    "id": "customer123",
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john.doe@example.com",
                    "status": "ACTIVE"
                },
                {
                    "id": "customer456",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "email": "jane.smith@example.com",
                    "status": "ACTIVE"
                }
            ]
        }
        client.session.request.return_value = mock_response
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # List customers
        customers = customer_resource.list(limit=10, email="example.com")
        
        # Verify result
        assert isinstance(customers, list)
        assert len(customers) == 2
        assert all(isinstance(customer, CustomerModel) for customer in customers)
        assert customers[0].id == "customer123"
        assert customers[1].id == "customer456"
        
        # Verify API call
        client.session.request.assert_called_once()
        call_args = client.session.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "customers" in call_args[1]["url"]
        assert call_args[1]["params"]["limit"] == 10
        assert call_args[1]["params"]["email"] == "example.com"

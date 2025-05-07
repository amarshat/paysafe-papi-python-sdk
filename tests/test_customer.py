"""
Tests for the Customer resource.
"""

import json
import os
import re
from datetime import datetime
from unittest import mock

import pytest

from paysafe import Client
from paysafe.api_resources.customer import Customer
from paysafe.exceptions import (APIError, AuthenticationError, InvalidRequestError,
                               NetworkError, PaysafeError, RateLimitError)
from paysafe.models.customer import Customer as CustomerModel, CustomerStatus, CustomerBillingDetails


class TestCustomer:
    """Unit tests for the Customer resource."""

    def test_create(self, client, mock_customer_response, sample_customer):
        """Test customer creation with mocked response."""
        # Setup mock response
        client.post.return_value = {
            "id": "cust_123456789",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "status": "ACTIVE",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Create customer
        customer = customer_resource.create(sample_customer)
        
        # Verify result
        assert isinstance(customer, CustomerModel)
        assert customer.id == "cust_123456789"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.email == "john.doe@example.com"
        assert customer.status == CustomerStatus.ACTIVE
        
        # Verify API call
        client.post.assert_called_once()
        
        # Verify that post was called with the correct resource path
        client.post.assert_called_with(
            "customers", 
            data=mock.ANY  # We don't need to check the exact data here
        )
        
    def test_create_with_dictionary(self, client, mock_customer_response):
        """Test customer creation using a dictionary."""
        # Setup mock response with transformed data (snake_case)
        client.post.return_value = {
            "id": "cust_123456789",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "status": "ACTIVE"
        }
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Create customer data as dictionary
        customer_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890"
        }
        
        # Create customer
        customer = customer_resource.create(customer_data)
        
        # Verify result
        assert isinstance(customer, CustomerModel)
        assert customer.id == "cust_123456789"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.email == "john.doe@example.com"
        
        # Verify API call
        client.post.assert_called_once()
        
        # Verify that post was called with the correct path and transformed data (snake_case to camelCase)
        client.post.assert_called_with(
            "customers", 
            data={
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@example.com",
                "phone": "1234567890"
            }
        )
        
    def test_create_with_billing_details(self, client, mock_customer_response):
        """Test customer creation with billing details."""
        # Setup mock response with transformed data (snake_case)
        client.post.return_value = {
            "id": "cust_123456789",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "billing_details": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "country": "US",
                "zip": "12345"
            },
            "status": "ACTIVE"
        }
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Create billing details
        billing_details = CustomerBillingDetails(
            street="123 Main St",
            city="Anytown",
            state="CA",
            country="US",
            zip="12345"
        )
        
        # Create customer
        customer = CustomerModel(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            billing_details=billing_details
        )
        
        # Submit customer
        result = customer_resource.create(customer)
        
        # Verify result
        assert isinstance(result, CustomerModel)
        assert result.id == "cust_123456789"
        assert result.billing_details is not None
        assert result.billing_details.street == "123 Main St"
        assert result.billing_details.city == "Anytown"
        assert result.billing_details.country == "US"
        
        # Verify API call
        client.post.assert_called_once()
        
        # Verify that post was called with the correct path
        client.post.assert_called_with("customers", data=mock.ANY)
        
    def test_retrieve(self, client, mock_customer_response):
        """Test customer retrieval."""
        # Setup mock response
        client.get.return_value = {
            "id": "cust_123456789",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "status": "ACTIVE"
        }
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Retrieve customer
        customer = customer_resource.retrieve("cust_123456789")
        
        # Verify result
        assert isinstance(customer, CustomerModel)
        assert customer.id == "cust_123456789"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.email == "john.doe@example.com"
        
        # Verify API call
        client.get.assert_called_once()
        
        # Verify that get was called with the correct resource path and ID
        client.get.assert_called_with(
            "customers/cust_123456789"
        )
        
    def test_retrieve_invalid_id(self, client):
        """Test customer retrieval with invalid ID."""
        # Create customer resource
        customer_resource = Customer(client)
        
        # Attempt to retrieve with empty ID
        with pytest.raises(ValueError) as exc_info:
            customer_resource.retrieve("")
        
        assert "customer_id cannot be None or empty" in str(exc_info.value)
        
    def test_update(self, client, mock_customer_response):
        """Test customer update."""
        # Setup mock response
        client.put.return_value = {
            "id": "cust_123456789",
            "first_name": "Jane",  # Changed from John to Jane
            "last_name": "Doe",
            "email": "jane.doe@example.com",  # Updated email
            "status": "ACTIVE"
        }
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Update customer data
        customer_update = {
            "first_name": "Jane",
            "email": "jane.doe@example.com"
        }
        
        # Update customer
        customer = customer_resource.update("cust_123456789", customer_update)
        
        # Verify result
        assert isinstance(customer, CustomerModel)
        assert customer.id == "cust_123456789"
        assert customer.first_name == "Jane"  # Verify name changed
        assert customer.email == "jane.doe@example.com"  # Verify email updated
        
        # Verify API call
        client.put.assert_called_once()
        
        # Verify that put was called with the correct resource path and ID
        client.put.assert_called_with(
            "customers/cust_123456789", 
            data=mock.ANY  # We don't need to check the exact data format, but path should be correct
        )
        
    def test_delete(self, client, mock_customer_response):
        """Test customer deletion."""
        # Setup mock response
        client.delete.return_value = {"deleted": True}
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # Delete customer
        result = customer_resource.delete("cust_123456789")
        
        # Verify result
        assert "deleted" in result
        assert result["deleted"] is True
        
        # Verify API call
        client.delete.assert_called_once()
        
        # Verify that delete was called with the correct resource path and ID
        client.delete.assert_called_with(
            "customers/cust_123456789"
        )
        
    def test_list(self, client, mock_customer_response):
        """Test customer listing."""
        # Setup mock response with transformed data (snake_case)
        client.get.return_value = {
            "customers": [
                {
                    "id": "cust_123456789",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "status": "ACTIVE"
                },
                {
                    "id": "cust_987654321",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "email": "jane.smith@example.com",
                    "status": "ACTIVE"
                }
            ],
            "pagination": {
                "total_items": 2,
                "limit": 10,
                "offset": 0
            }
        }
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # List customers
        customers = customer_resource.list(limit=10, email="example.com")
        
        # Verify result
        assert isinstance(customers, list)
        assert len(customers) == 2
        assert all(isinstance(customer, CustomerModel) for customer in customers)
        assert customers[0].id == "cust_123456789"
        assert customers[1].id == "cust_987654321"
        
        # Verify API call
        client.get.assert_called_once()
        
        # Verify that get was called with the correct parameters
        client.get.assert_called_with(
            "customers", 
            params={"limit": 10, "offset": 0, "email": "example.com"}
        )
        
    def test_list_with_filters(self, client, mock_customer_response):
        """Test customer listing with multiple filters."""
        # Setup mock response with transformed data (snake_case)
        client.get.return_value = {
            "customers": [
                {
                    "id": "cust_123456789",
                    "first_name": "John",
                    "last_name": "Doe",
                    "merchant_customer_id": "merch123",
                    "status": "ACTIVE"
                }
            ],
            "pagination": {
                "total_items": 1,
                "limit": 5,
                "offset": 0
            }
        }
        
        # Create customer resource
        customer_resource = Customer(client)
        
        # List customers with filters
        customers = customer_resource.list(
            limit=5,
            offset=0,
            merchant_customer_id="merch123",
            status="ACTIVE"
        )
        
        # Verify result
        assert isinstance(customers, list)
        assert len(customers) == 1
        
        # Verify API call
        client.get.assert_called_once()
        
        # Verify that get was called with the correct parameters
        client.get.assert_called_with(
            "customers", 
            params={
                "limit": 5, 
                "offset": 0, 
                "merchantCustomerId": "merch123", 
                "status": "ACTIVE"
            }
        )
        
    def test_utility_methods(self, client):
        """Test utility methods on the Customer model."""
        # Test get_full_name method
        customer = CustomerModel(
            first_name="John",
            last_name="Doe"
        )
        assert customer.get_full_name() == "John Doe"
        
        # Test with only first name
        customer = CustomerModel(
            first_name="John"
        )
        assert customer.get_full_name() == "John"
        
        # Test with only last name
        customer = CustomerModel(
            last_name="Doe"
        )
        assert customer.get_full_name() == "Doe"
        
        # Test with no name
        customer = CustomerModel()
        assert customer.get_full_name() == ""
        
    def test_error_handling(self, client, error_response):
        """Test error handling in customer resource."""
        # Create customer resource
        customer_resource = Customer(client)
        
        # Since we're using the high-level client methods (get, post, etc.)
        # we need to mock the client.request method which is called by those methods
        
        # Test authentication error
        client.request.side_effect = AuthenticationError(
            message="Authentication error: Invalid API key", 
            code="UNAUTHORIZED", 
            http_status=401
        )
        with pytest.raises(AuthenticationError) as exc_info:
            customer_resource.retrieve("cust_123456789")
        assert "Authentication error" in str(exc_info.value)
        
        # Test invalid request error
        client.request.side_effect = InvalidRequestError(
            message="Invalid customer ID", 
            code="INVALID_REQUEST", 
            http_status=400
        )
        with pytest.raises(InvalidRequestError) as exc_info:
            customer_resource.retrieve("cust_123456789")
        assert "Invalid customer ID" in str(exc_info.value)
        
        # Test rate limit error
        client.request.side_effect = RateLimitError(
            message="Rate limit exceeded", 
            code="RATE_LIMIT_EXCEEDED", 
            http_status=429
        )
        with pytest.raises(RateLimitError) as exc_info:
            customer_resource.retrieve("cust_123456789")
        assert "Rate limit exceeded" in str(exc_info.value)
        
        # Test API error
        client.request.side_effect = APIError(
            message="Internal server error", 
            code="SERVER_ERROR", 
            http_status=500
        )
        with pytest.raises(APIError) as exc_info:
            customer_resource.retrieve("cust_123456789")
        assert "Internal server error" in str(exc_info.value)


@pytest.mark.integration
class TestCustomerIntegration:
    """Integration tests for the Customer resource using real API calls.
    
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
    def test_customer_id(self):
        """Store a customer ID for tests that need an existing customer."""
        return os.environ.get("PAYSAFE_TEST_CUSTOMER_ID", "")
    
    def test_create_and_retrieve_customer(self, real_client, sample_customer):
        """Test creating and retrieving a customer with real API calls."""
        # Skip if no API key
        if not os.environ.get("PAYSAFE_TEST_API_KEY"):
            pytest.skip("PAYSAFE_TEST_API_KEY environment variable not set")
            
        # Create customer resource
        customer_resource = Customer(real_client)
        
        # Generate a unique email to avoid conflicts
        unique_id = datetime.now().strftime("%Y%m%d%H%M%S")
        sample_customer.email = f"test.user+{unique_id}@example.com"
        
        try:
            # Create customer
            created_customer = customer_resource.create(sample_customer)
            
            # Verify customer was created
            assert created_customer.id is not None
            assert created_customer.email == sample_customer.email
            
            # Retrieve the customer
            retrieved_customer = customer_resource.retrieve(created_customer.id)
            
            # Verify retrieved customer
            assert retrieved_customer.id == created_customer.id
            assert retrieved_customer.first_name == sample_customer.first_name
            assert retrieved_customer.last_name == sample_customer.last_name
            
            # Clean up - delete the test customer
            customer_resource.delete(created_customer.id)
            
        except PaysafeError as e:
            pytest.fail(f"API error: {e}")
    
    def test_update_customer(self, real_client, test_customer_id):
        """Test updating a customer with real API calls."""
        # Skip if no API key or customer ID
        if not os.environ.get("PAYSAFE_TEST_API_KEY") or not test_customer_id:
            pytest.skip("PAYSAFE_TEST_API_KEY or PAYSAFE_TEST_CUSTOMER_ID not set")
            
        # Create customer resource
        customer_resource = Customer(real_client)
        
        try:
            # Retrieve the customer first
            customer = customer_resource.retrieve(test_customer_id)
            
            # Generate new values
            new_phone = f"555{datetime.now().strftime('%M%S')}"
            
            # Update the customer
            update_data = {
                "phone": new_phone,
                "locale": "en_US"
            }
            
            updated_customer = customer_resource.update(test_customer_id, update_data)
            
            # Verify update
            assert updated_customer.id == test_customer_id
            assert updated_customer.phone == new_phone
            assert updated_customer.locale == "en_US"
            
        except PaysafeError as e:
            pytest.fail(f"API error: {e}")
    
    def test_list_customers(self, real_client):
        """Test listing customers with real API calls."""
        # Skip if no API key
        if not os.environ.get("PAYSAFE_TEST_API_KEY"):
            pytest.skip("PAYSAFE_TEST_API_KEY environment variable not set")
            
        # Create customer resource
        customer_resource = Customer(real_client)
        
        try:
            # List customers
            customers = customer_resource.list(limit=5)
            
            # Verify response
            assert isinstance(customers, list)
            
            # Verify customer objects
            if customers:
                assert all(isinstance(customer, CustomerModel) for customer in customers)
                assert all(customer.id is not None for customer in customers)
                
        except PaysafeError as e:
            pytest.fail(f"API error: {e}")
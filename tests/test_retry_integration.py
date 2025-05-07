"""
Integration tests for the retry functionality with real API calls to Paysafe.

These tests require a real Paysafe API key and will make actual API calls.
Run with: pytest tests/test_retry_integration.py --integration
"""

import os
import time
import uuid
import pytest
import requests
from unittest import mock

from paysafe import Client
from paysafe.exceptions import NetworkError, RateLimitError
from paysafe.retry import RetryConfig, RetryStrategy, RetryCondition


# Skip all tests in this module unless the --integration flag is passed
pytestmark = pytest.mark.integration


@pytest.fixture
def real_client():
    """Create a client with real API credentials for integration testing."""
    api_key = os.environ.get("PAYSAFE_API_KEY")
    credentials_file = os.environ.get("PAYSAFE_CREDENTIALS_FILE")
    
    if not api_key and not credentials_file:
        pytest.skip("No Paysafe API credentials available for integration tests")
    
    return Client(
        api_key=api_key,
        credentials_file=credentials_file,
        environment="sandbox",
    )


@pytest.fixture
def dummy_api_key():
    """Create a dummy API key that will cause authentication errors."""
    return "invalid_api_key_" + str(uuid.uuid4()).replace("-", "")


class TestRetryIntegration:
    """Integration tests for retry functionality with real API calls."""

    def test_successful_request(self, real_client):
        """Test a successful API request that doesn't need retrying."""
        retry_config = RetryConfig(
            max_retries=2,
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=0.5,
        )
        
        # Use a simple endpoint that should succeed
        result = real_client.get("merchantaccountref", retry_config=retry_config)
        
        # If we get here without exceptions, the test passes
        assert isinstance(result, dict)
    
    def test_invalid_auth_not_retried(self):
        """Test that authentication errors are not retried."""
        # Create client with invalid API key
        client = Client(
            api_key="invalid_api_key", 
            environment="sandbox",
            retry_config=RetryConfig(
                max_retries=3,
                retry_strategy=RetryStrategy.FIXED,
                initial_delay=0.5,
            )
        )
        
        # Mock the request method to track calls
        with mock.patch.object(client.session, 'request', wraps=client.session.request) as mock_request:
            # This should fail with AuthenticationError and not retry
            with pytest.raises(Exception) as excinfo:
                client.get("merchantaccountref")
            
            # Verify we only tried once
            assert mock_request.call_count == 1
            assert "Authentication" in str(excinfo.value)
    
    def test_network_error_retry(self, real_client):
        """Test retrying on network errors."""
        # Create a retry config with network error retries
        retry_config = RetryConfig(
            max_retries=2,
            retry_conditions=[RetryCondition.NETWORK_ERROR],
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=0.5,
        )
        
        # Mock the requests.Session.request method to fail with network error then succeed
        original_request = real_client.session.request
        
        def side_effect(*args, **kwargs):
            # Restore the original method to ensure the second attempt succeeds
            real_client.session.request = original_request
            # First call will fail with a connection error
            raise requests.exceptions.ConnectionError("Simulated network error")
        
        with mock.patch.object(real_client.session, 'request', side_effect=side_effect):
            # This should retry after the network error and then succeed with the real API call
            result = real_client.get("merchantaccountref", retry_config=retry_config)
            
            # If we get here, the retry succeeded
            assert isinstance(result, dict)
    
    def test_request_with_invalid_endpoint(self, real_client):
        """Test request to an invalid endpoint (404 error)."""
        retry_config = RetryConfig(
            max_retries=2,
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=0.5,
            # Don't retry 404s by default, as that's an InvalidRequestError
            retry_conditions=[RetryCondition.NETWORK_ERROR, RetryCondition.SERVER_ERROR],
        )
        
        # Mock the request method to track calls
        with mock.patch.object(real_client.session, 'request', wraps=real_client.session.request) as mock_request:
            # This should fail with InvalidRequestError and not retry
            with pytest.raises(Exception) as excinfo:
                real_client.get("nonexistent_endpoint", retry_config=retry_config)
            
            # Verify we only tried once
            assert mock_request.call_count == 1
    
    def test_retry_any_error(self, real_client):
        """Test retrying on any error."""
        retry_config = RetryConfig(
            max_retries=1,
            retry_conditions=[RetryCondition.ANY_ERROR],
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=0.5,
        )
        
        # Mock the request method to track calls
        with mock.patch.object(real_client.session, 'request', wraps=real_client.session.request) as mock_request:
            # This should fail with InvalidRequestError but still retry once
            with pytest.raises(Exception):
                real_client.get("nonexistent_endpoint", retry_config=retry_config)
            
            # Verify we tried twice (initial + 1 retry)
            assert mock_request.call_count == 2
"""
Tests for the retry functionality of the Paysafe SDK.
"""

import time
from unittest import mock
import pytest
import requests

from paysafe import Client
from paysafe.exceptions import (
    NetworkError,
    APIError,
    RateLimitError,
    InvalidRequestError,
)
from paysafe.retry import (
    RetryConfig,
    RetryStrategy,
    RetryCondition,
    create_retry_handler,
)


class TestRetryConfig:
    """Tests for the RetryConfig class."""

    def test_init_default_values(self):
        """Test RetryConfig initialization with default values."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.retry_strategy == RetryStrategy.EXPONENTIAL_JITTER
        assert RetryCondition.NETWORK_ERROR in config.retry_conditions
        assert RetryCondition.RATE_LIMIT in config.retry_conditions
        assert RetryCondition.SERVER_ERROR in config.retry_conditions
        assert 429 in config.retry_codes
        assert 500 in config.retry_codes
        assert "GET" in config.retry_methods
        assert "POST" in config.retry_methods
        assert len(config.excluded_endpoints) == 0

    def test_init_custom_values(self):
        """Test RetryConfig initialization with custom values."""
        config = RetryConfig(
            max_retries=5,
            retry_strategy=RetryStrategy.FIXED,
            retry_conditions=[RetryCondition.NETWORK_ERROR],
            initial_delay=1.0,
            max_delay=10.0,
            jitter_factor=0.5,
            retry_codes={500, 502, 503},
            backoff_factor=3.0,
            retry_methods={"GET"},
            excluded_endpoints={"/payments"},
        )
        
        assert config.max_retries == 5
        assert config.retry_strategy == RetryStrategy.FIXED
        assert len(config.retry_conditions) == 1
        assert RetryCondition.NETWORK_ERROR in config.retry_conditions
        assert config.initial_delay == 1.0
        assert config.max_delay == 10.0
        assert config.jitter_factor == 0.5
        assert config.retry_codes == {500, 502, 503}
        assert config.backoff_factor == 3.0
        assert config.retry_methods == {"GET"}
        assert config.excluded_endpoints == {"/payments"}

    def test_should_retry_max_retries(self):
        """Test retry decision based on max retries."""
        config = RetryConfig(max_retries=2)
        
        # Attempt 0 (first try) should be retriable
        assert config.should_retry("GET", "/test", 0, NetworkError(message="Test"))
        
        # Attempt 1 (first retry) should be retriable
        assert config.should_retry("GET", "/test", 1, NetworkError(message="Test"))
        
        # Attempt 2 (second retry) should not be retriable (max_retries=2)
        assert not config.should_retry("GET", "/test", 2, NetworkError(message="Test"))

    def test_should_retry_methods(self):
        """Test retry decision based on HTTP methods."""
        config = RetryConfig(retry_methods={"GET", "POST"})
        
        # GET should be retriable
        assert config.should_retry("GET", "/test", 0, NetworkError(message="Test"))
        
        # POST should be retriable
        assert config.should_retry("POST", "/test", 0, NetworkError(message="Test"))
        
        # DELETE should not be retriable
        assert not config.should_retry("DELETE", "/test", 0, NetworkError(message="Test"))

    def test_should_retry_excluded_endpoints(self):
        """Test retry decision based on excluded endpoints."""
        config = RetryConfig(excluded_endpoints={"/payments"})
        
        # Non-excluded endpoint should be retriable
        assert config.should_retry("GET", "/customers", 0, NetworkError(message="Test"))
        
        # Excluded endpoint should not be retriable
        assert not config.should_retry("GET", "/payments", 0, NetworkError(message="Test"))
        
        # Endpoint containing excluded path should not be retriable
        assert not config.should_retry("GET", "/payments/123", 0, NetworkError(message="Test"))

    def test_should_retry_error_types(self):
        """Test retry decision based on error types."""
        # Only retry network errors
        config = RetryConfig(retry_conditions=[RetryCondition.NETWORK_ERROR])
        
        assert config.should_retry("GET", "/test", 0, NetworkError(message="Test"))
        assert not config.should_retry("GET", "/test", 0, APIError(message="Test"))
        
        # Only retry rate limit errors
        config = RetryConfig(retry_conditions=[RetryCondition.RATE_LIMIT])
        
        assert config.should_retry("GET", "/test", 0, RateLimitError(message="Test"))
        assert not config.should_retry("GET", "/test", 0, NetworkError(message="Test"))
        
        # Retry any error
        config = RetryConfig(retry_conditions=[RetryCondition.ANY_ERROR])
        
        assert config.should_retry("GET", "/test", 0, NetworkError(message="Test"))
        assert config.should_retry("GET", "/test", 0, APIError(message="Test"))
        assert config.should_retry("GET", "/test", 0, InvalidRequestError(message="Test"))

    def test_should_retry_status_codes(self):
        """Test retry decision based on status codes."""
        config = RetryConfig(retry_codes={500, 502, 503})
        
        # Status code in retry_codes should be retriable
        assert config.should_retry("GET", "/test", 0, None, 500)
        assert config.should_retry("GET", "/test", 0, None, 502)
        
        # Status code not in retry_codes should not be retriable
        assert not config.should_retry("GET", "/test", 0, None, 400)
        assert not config.should_retry("GET", "/test", 0, None, 404)

    def test_get_retry_delay_none(self):
        """Test delay calculation for NONE strategy."""
        config = RetryConfig(retry_strategy=RetryStrategy.NONE)
        
        assert config.get_retry_delay(0) == 0
        assert config.get_retry_delay(1) == 0
        assert config.get_retry_delay(2) == 0

    def test_get_retry_delay_fixed(self):
        """Test delay calculation for FIXED strategy."""
        config = RetryConfig(
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=1.5,
        )
        
        assert config.get_retry_delay(0) == 1.5
        assert config.get_retry_delay(1) == 1.5
        assert config.get_retry_delay(2) == 1.5

    def test_get_retry_delay_exponential(self):
        """Test delay calculation for EXPONENTIAL strategy."""
        config = RetryConfig(
            retry_strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
        )
        
        # 1.0 * (2.0 ^ 0)
        assert config.get_retry_delay(0) == 1.0
        
        # 1.0 * (2.0 ^ 1)
        assert config.get_retry_delay(1) == 2.0
        
        # 1.0 * (2.0 ^ 2)
        assert config.get_retry_delay(2) == 4.0
        
        # 1.0 * (2.0 ^ 3) = 8.0
        assert config.get_retry_delay(3) == 8.0
        
        # 1.0 * (2.0 ^ 4) = 16.0, but capped at max_delay=10.0
        assert config.get_retry_delay(4) == 10.0

    def test_get_retry_delay_exponential_jitter(self):
        """Test delay calculation for EXPONENTIAL_JITTER strategy."""
        # Mock random.uniform to return a consistent value for testing
        with mock.patch("random.uniform", return_value=0.1):
            config = RetryConfig(
                retry_strategy=RetryStrategy.EXPONENTIAL_JITTER,
                initial_delay=1.0,
                jitter_factor=0.25,
                backoff_factor=2.0,
            )
            
            # 1.0 * (2.0 ^ 0) * (1 + 0.1) = 1.0 * 1.1 = 1.1
            assert config.get_retry_delay(0) == 1.1
            
            # 1.0 * (2.0 ^ 1) * (1 + 0.1) = 2.0 * 1.1 = 2.2
            assert config.get_retry_delay(1) == 2.2
            
            # 1.0 * (2.0 ^ 2) * (1 + 0.1) = 4.0 * 1.1 = 4.4
            assert config.get_retry_delay(2) == 4.4


class TestRetryHandler:
    """Tests for the retry handler."""

    def test_retry_handler_success_first_try(self):
        """Test retry handler when first try succeeds."""
        config = RetryConfig(max_retries=3)
        request_func = mock.MagicMock(return_value="Success")
        
        handler = create_retry_handler(config)
        result = handler(request_func, "GET", "/test")
        
        assert result == "Success"
        request_func.assert_called_once()

    def test_retry_handler_success_after_retry(self):
        """Test retry handler when success occurs after retry."""
        config = RetryConfig(
            max_retries=3,
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=0.01,  # Small delay to make test fast
        )
        
        # Fail twice, then succeed on 3rd attempt
        side_effects = [
            NetworkError(message="Error 1"),
            NetworkError(message="Error 2"),
            "Success",
        ]
        request_func = mock.MagicMock(side_effect=side_effects)
        
        handler = create_retry_handler(config)
        result = handler(request_func, "GET", "/test")
        
        assert result == "Success"
        assert request_func.call_count == 3

    def test_retry_handler_max_retries_exceeded(self):
        """Test retry handler when max retries is exceeded."""
        config = RetryConfig(
            max_retries=2,
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=0.01,  # Small delay to make test fast
        )
        
        # Always fail with NetworkError
        request_func = mock.MagicMock(side_effect=NetworkError(message="Persistent error"))
        
        handler = create_retry_handler(config)
        
        with pytest.raises(NetworkError, match="Persistent error"):
            handler(request_func, "GET", "/test")
        
        # Original attempt plus 2 retries = 3 total calls
        assert request_func.call_count == 3

    def test_retry_handler_non_retriable_error(self):
        """Test retry handler with a non-retriable error."""
        config = RetryConfig(
            max_retries=3,
            retry_conditions=[RetryCondition.NETWORK_ERROR],  # Only retry network errors
        )
        
        # Fail with an API error which shouldn't be retried
        request_func = mock.MagicMock(side_effect=APIError(message="API error"))
        
        handler = create_retry_handler(config)
        
        with pytest.raises(APIError, match="API error"):
            handler(request_func, "GET", "/test")
        
        # Should only try once and not retry
        request_func.assert_called_once()


class TestClientRetry:
    """Integration tests for client with retry functionality."""

    def test_client_init_with_retry_config(self, api_key):
        """Test client initialization with retry configuration."""
        retry_config = RetryConfig(
            max_retries=5,
            retry_strategy=RetryStrategy.FIXED,
        )
        
        client = Client(api_key=api_key, retry_config=retry_config)
        
        assert client.retry_config is retry_config
        assert client.retry_config.max_retries == 5
        assert client.retry_config.retry_strategy == RetryStrategy.FIXED

    def test_client_default_retry_config(self, api_key):
        """Test client with default retry configuration."""
        client = Client(api_key=api_key)
        
        assert client.retry_config is not None
        assert client.retry_config.max_retries == client.max_retries
        assert client.retry_config.retry_strategy == RetryStrategy.EXPONENTIAL_JITTER

    @mock.patch("requests.Session.request")
    def test_client_retry_network_error(self, mock_request, api_key):
        """Test client retry behavior with network errors."""
        client = Client(
            api_key=api_key, 
            retry_config=RetryConfig(
                max_retries=2,
                retry_strategy=RetryStrategy.FIXED,
                initial_delay=0.01,  # Small delay to make test fast
            )
        )
        
        # Simulate a network error on first request, then success
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.text = '{"result": "success"}'
        
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            mock_response,
        ]
        
        result = client.get("test")
        
        assert result == {"result": "success"}
        assert mock_request.call_count == 2  # Initial request plus one retry

    @mock.patch("requests.Session.request")
    def test_client_retry_rate_limit(self, mock_request, api_key):
        """Test client retry behavior with rate limit errors."""
        client = Client(
            api_key=api_key, 
            retry_config=RetryConfig(
                max_retries=2,
                retry_strategy=RetryStrategy.FIXED,
                initial_delay=0.01,  # Small delay to make test fast
            )
        )
        
        # Simulate rate limit on first request, then success
        rate_limit_response = mock.MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        rate_limit_response.text = '{"error": {"message": "Rate limit exceeded"}}'
        
        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"result": "success"}
        success_response.text = '{"result": "success"}'
        
        mock_request.side_effect = [rate_limit_response, success_response]
        
        # This should trigger _handle_error_response, which raises a RateLimitError
        # The retry handler should catch this and retry
        with mock.patch.object(client, '_handle_error_response') as mock_handle_error:
            mock_handle_error.side_effect = [
                RateLimitError(message="Rate limit exceeded", http_status=429),
                None,
            ]
            
            result = client.get("test")
            
            assert result == {"result": "success"}
            assert mock_request.call_count == 2  # Initial request plus one retry

    @mock.patch("requests.Session.request")
    def test_client_per_request_retry_config(self, mock_request, api_key):
        """Test client with per-request retry configuration."""
        # Create client with default retry config (3 retries)
        client = Client(api_key=api_key)
        
        # Create custom retry config for specific request (1 retry)
        custom_retry_config = RetryConfig(
            max_retries=1,
            retry_strategy=RetryStrategy.FIXED,
            initial_delay=0.01,  # Small delay to make test fast
        )
        
        # Simulate network errors
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Network error 1"),
            requests.exceptions.ConnectionError("Network error 2"),
            requests.exceptions.ConnectionError("Network error 3"),
        ]
        
        # Should only retry once due to custom config (2 total attempts)
        with pytest.raises(NetworkError):
            client.get("test", retry_config=custom_retry_config)
        
        assert mock_request.call_count == 2  # Initial request plus one retry
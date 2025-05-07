"""
Mock client for the Paysafe Python SDK.

This module provides mock client implementations for testing applications
that use the Paysafe SDK without requiring actual API credentials.
"""

import base64
import functools
import json
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from paysafe.api_client import Client
from paysafe.async_client import AsyncClient
from paysafe.exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    NetworkError,
    PaysafeError,
    RateLimitError,
)
from paysafe.retry import RetryConfig
from paysafe.testing.mock_server import MockPaysafeServer, MockResponse

T = TypeVar("T", bound=Callable[..., Any])


def mock_api_call(func: T) -> T:
    """
    Decorator to mock API calls for testing.

    This decorator replaces the actual API call with a mock response from
    the mock server. It can be used to test API resource methods without
    making actual network requests.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from paysafe.api_resources.base import Resource

        # Get the resource instance (self)
        resource = args[0]
        if not isinstance(resource, Resource):
            raise ValueError("Decorator can only be used on Resource methods")

        # Get the client from the resource
        client = resource.client
        if not hasattr(client, "mock_server"):
            raise ValueError("Client does not have a mock server")

        # Extract the original function name and path
        method_name = func.__name__
        http_method = ""
        if method_name.startswith("get_"):
            http_method = "GET"
        elif method_name.startswith("create_"):
            http_method = "POST"
        elif method_name.startswith("update_"):
            http_method = "PUT"
        elif method_name.startswith("delete_"):
            http_method = "DELETE"
        else:
            http_method = "GET"  # Default to GET for unknown methods

        # Get the path from the resource class
        path = resource.RESOURCE_PATH
        if len(args) > 1:
            # Append ID to the path if there is an ID argument
            path = f"{path}/{args[1]}"

        # Get headers and data from function arguments
        headers = kwargs.get("headers", {})
        data = kwargs.get("data", {})
        params = kwargs.get("params", {})

        # Call the mock server
        mock_server = client.mock_server
        response = mock_server.handle_request(
            method=http_method, path=path, headers=headers, params=params, data=data
        )

        # Process the response
        if response.status_code >= 400:
            error_data = response.json()
            error = error_data.get("error", {})
            message = error.get("message", "Unknown error")
            code = error.get("code", "ERROR")

            if response.status_code == 401:
                raise AuthenticationError(message, code=code)
            elif response.status_code == 400:
                raise InvalidRequestError(message, code=code)
            elif response.status_code == 429:
                raise RateLimitError(message, code=code)
            elif response.status_code >= 500:
                raise APIError(message, code=code)
            else:
                raise PaysafeError(message, code=code)

        return response.json()

    return cast(T, wrapper)


class MockClient(Client):
    """
    Mock client for the Paysafe API.

    This class simulates the Paysafe API client for local testing.
    It intercepts all API requests and routes them to the mock server.
    """

    def __init__(
        self,
        api_key: str = "mock_api_key",
        environment: str = "sandbox",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        fail_rate: float = 0.0,
        latency: tuple = (0.0, 0.0),
    ):
        """
        Initialize the mock client.

        Args:
            api_key: API key to use for authentication
            environment: API environment ('sandbox' or 'production')
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of request retries
            fail_rate: Probability of random failure (0.0 to 1.0)
            latency: Range of random latency in seconds (min, max)
        """
        super().__init__(
            api_key=api_key,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.mock_server = MockPaysafeServer(
            api_key=api_key, fail_rate=fail_rate, latency=latency
        )

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the mock Paysafe API.

        Args:
            method: HTTP method to use ('GET', 'POST', etc.)
            path: API endpoint path
            params: URL parameters to include in the request
            data: JSON data to include in the request body
            headers: Additional HTTP headers to include in the request

        Returns:
            The parsed JSON response

        Raises:
            AuthenticationError: If authentication fails
            InvalidRequestError: If the request is invalid
            APIError: If the API returns an error
            NetworkError: If there's a network-related error
            RateLimitError: If the API rate limit is exceeded
            PaysafeError: For any other Paysafe-related error
        """
        # Set default headers if none provided
        if headers is None:
            headers = {}

        # Add authorization header
        auth_string = f"{self.api_key}:"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Basic {encoded_auth}"

        # Call the mock server
        response = self.mock_server.handle_request(
            method=method, path=path, headers=headers, params=params, data=data
        )

        # Process the response
        if not response.ok:
            self._handle_error_response(response, response.text, response.json())

        return response.json()

    def reset_mock_server(self) -> None:
        """Reset the mock server data."""
        self.mock_server.reset()


class MockAsyncClient(AsyncClient):
    """
    Mock async client for the Paysafe API.

    This class simulates the async Paysafe API client for local testing.
    It intercepts all API requests and routes them to the mock server.
    """

    def __init__(
        self,
        api_key: str = "mock_api_key",
        environment: str = "sandbox",
        base_url: Optional[str] = None,
        timeout: int = 60,
        fail_rate: float = 0.0,
        latency: tuple = (0.0, 0.0),
    ):
        """
        Initialize the mock async client.

        Args:
            api_key: API key to use for authentication
            environment: API environment ('sandbox' or 'production')
            base_url: API base URL
            timeout: Request timeout in seconds
            fail_rate: Probability of random failure (0.0 to 1.0)
            latency: Range of random latency in seconds (min, max)
        """
        super().__init__(
            api_key=api_key, environment=environment, base_url=base_url, timeout=timeout
        )
        self.mock_server = MockPaysafeServer(
            api_key=api_key, fail_rate=fail_rate, latency=latency
        )

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async request to the mock Paysafe API.

        Args:
            method: HTTP method to use ('GET', 'POST', etc.)
            path: API endpoint path
            params: URL parameters to include in the request
            data: JSON data to include in the request body
            headers: Additional HTTP headers to include in the request

        Returns:
            The parsed JSON response

        Raises:
            AuthenticationError: If authentication fails
            InvalidRequestError: If the request is invalid
            APIError: If the API returns an error
            NetworkError: If there's a network-related error
            RateLimitError: If the API rate limit is exceeded
            PaysafeError: For any other Paysafe-related error
        """
        # Set default headers if none provided
        if headers is None:
            headers = {}

        # Add authorization header
        auth_string = f"{self.api_key}:"
        encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Basic {encoded_auth}"

        # Call the mock server (async functions can still call sync code)
        response = self.mock_server.handle_request(
            method=method, path=path, headers=headers, params=params, data=data
        )

        # Process the response
        if not response.ok:
            await self._handle_error_response(response, response.text, response.json())

        return response.json()

    def reset_mock_server(self) -> None:
        """Reset the mock server data."""
        self.mock_server.reset()
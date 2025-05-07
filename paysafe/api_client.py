"""
API client for the Paysafe Python SDK.

This module provides the core functionality for making requests to the Paysafe API.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urljoin

import requests
from requests import Response, Session

from paysafe.exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    NetworkError,
    PaysafeError,
    RateLimitError,
)
from paysafe.retry import RetryConfig, RetryStrategy, RetryCondition, create_retry_handler
from paysafe.utils import load_credentials_from_file, get_api_key_from_credentials
from paysafe.version import VERSION

logger = logging.getLogger("paysafe")
payload_logger = logging.getLogger("paysafe.api.payloads")


class Client:
    """
    Client for the Paysafe API.

    This class handles authentication and request signing, and provides
    methods for making HTTP requests to the Paysafe API.
    """

    DEFAULT_BASE_URL = "https://api.paysafe.com/v1/"
    SANDBOX_BASE_URL = "https://api.test.paysafe.com/v1/"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: str = "production",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
        credentials_file: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        """
        Initialize a new Paysafe API client.

        Args:
            api_key: Your Paysafe API key. If not provided, will look for credentials_file or environment variable.
            environment: The API environment to use ('production' or 'sandbox').
            base_url: Override the default API base URL.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of request retries.
            credentials_file: Path to a JSON file containing Paysafe credentials (Postman format).
                              If not provided, will check PAYSAFE_CREDENTIALS_FILE environment variable.
            retry_config: Custom retry configuration. If not provided, default configuration will be used
                          with max_retries from the parameter above.
        """
        # Get API key from credentials file if not directly provided
        if api_key is None:
            try:
                credentials = load_credentials_from_file(credentials_file)
                api_key = get_api_key_from_credentials(credentials)
            except (ValueError, FileNotFoundError) as e:
                # Check for PAYSAFE_API_KEY environment variable as a fallback
                api_key = os.environ.get("PAYSAFE_API_KEY")
                if not api_key:
                    raise ValueError("API key not provided, not found in credentials file, "
                                    "and PAYSAFE_API_KEY environment variable not set.") from e
        
        self.api_key = api_key
        self.environment = environment
        
        if base_url is not None:
            self.base_url = base_url
        elif environment == "sandbox":
            self.base_url = self.SANDBOX_BASE_URL
        else:
            self.base_url = self.DEFAULT_BASE_URL
            
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Set up retry configuration
        self.retry_config = retry_config or RetryConfig(max_retries=max_retries)
        
        # Initialize requests session
        self.session = Session()
        self.session.headers.update(self._get_default_headers())

    def _get_default_headers(self) -> Dict[str, str]:
        """
        Get the default HTTP headers for API requests.

        Returns:
            A dictionary of default HTTP headers.
        """
        return {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": f"Paysafe/Python/{VERSION}",
        }

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the Paysafe API.

        Args:
            method: HTTP method to use ('GET', 'POST', etc.).
            path: API endpoint path.
            params: URL parameters to include in the request.
            data: JSON data to include in the request body.
            headers: Additional HTTP headers to include in the request.
            retry_config: Custom retry configuration to use for this specific request.
                          If not provided, the client's default configuration is used.

        Returns:
            The parsed JSON response.

        Raises:
            AuthenticationError: If authentication fails.
            InvalidRequestError: If the request is invalid.
            APIError: If the API returns an error.
            NetworkError: If there's a network-related error.
            RateLimitError: If the API rate limit is exceeded.
            PaysafeError: For any other Paysafe-related error.
        """
        url = urljoin(self.base_url, path)
        request_headers = headers.copy() if headers else {}
        
        json_data = None
        if data is not None:
            json_data = data
        
        # Use the provided retry config or the client's default
        active_retry_config = retry_config or self.retry_config
        
        # Create a function to execute a single request attempt
        def _execute_request():
            try:
                # Log the request payload
                payload_logger.debug(f"REQUEST: {method} {url}")
                payload_logger.debug(f"PARAMS: {json.dumps(params, indent=2) if params else None}")
                payload_logger.debug(f"HEADERS: {json.dumps({k: v for k, v in request_headers.items() if k != 'Authorization'}, indent=2) if request_headers else None}")
                payload_logger.debug(f"DATA: {json.dumps(json_data, indent=2) if json_data else None}")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                
                # Log the response payload
                payload_logger.debug(f"RESPONSE STATUS: {response.status_code}")
                payload_logger.debug(f"RESPONSE HEADERS: {json.dumps(dict(response.headers), indent=2)}")
                try:
                    payload_logger.debug(f"RESPONSE BODY: {json.dumps(response.json(), indent=2) if response.text else 'No body'}")
                except ValueError:
                    payload_logger.debug(f"RESPONSE BODY (non-JSON): {response.text[:1000]}")
                
                return self._handle_response(response)
                
            except requests.exceptions.Timeout as e:
                msg = f"Request timed out after {self.timeout} seconds"
                logger.error(msg)
                raise NetworkError(message=msg) from e
                
            except requests.exceptions.RequestException as e:
                msg = f"Network error: {str(e)}"
                logger.error(msg)
                raise NetworkError(message=msg) from e
        
        # Create a retry handler with the active configuration
        retry_handler = create_retry_handler(active_retry_config)
        
        try:
            # Execute the request with retry logic
            return retry_handler(_execute_request, method, path)
        except Exception as e:
            # This will only be reached if the retry handler fails to handle the exception
            # or if max retries are exceeded
            if not isinstance(e, PaysafeError):
                msg = f"Error during request: {str(e)}"
                logger.error(msg)
                raise PaysafeError(message=msg) from e
            raise

    def _handle_response(self, response: Response) -> Dict[str, Any]:
        """
        Handle the API response.

        Args:
            response: The HTTP response from the API.

        Returns:
            The parsed JSON response.

        Raises:
            AuthenticationError: If authentication fails.
            InvalidRequestError: If the request is invalid.
            APIError: If the API returns an error.
            RateLimitError: If the API rate limit is exceeded.
            PaysafeError: For any other Paysafe-related error.
        """
        try:
            http_body = response.text
            json_body = response.json() if http_body else {}
        except ValueError:
            json_body = {}
        
        if not 200 <= response.status_code < 300:
            self._handle_error_response(response, http_body, json_body)
        
        return json_body
    
    def _handle_error_response(
        self,
        response: Response,
        http_body: str,
        json_body: Dict[str, Any],
    ) -> None:
        """
        Handle an error response from the API.

        Args:
            response: The HTTP response from the API.
            http_body: The response body.
            json_body: The parsed JSON response body.

        Raises:
            AuthenticationError: If authentication fails.
            InvalidRequestError: If the request is invalid.
            APIError: If the API returns an error.
            RateLimitError: If the API rate limit is exceeded.
            PaysafeError: For any other Paysafe-related error.
        """
        error_message = json_body.get("error", {}).get("message", "Unknown error")
        error_code = json_body.get("error", {}).get("code")
        
        # Handle different HTTP status codes
        if response.status_code == 400:
            raise InvalidRequestError(
                message=error_message,
                code=error_code,
                http_status=response.status_code,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
            )
        elif response.status_code == 401:
            raise AuthenticationError(
                message="Authentication error: Invalid API key provided",
                code=error_code,
                http_status=response.status_code,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
            )
        elif response.status_code == 429:
            raise RateLimitError(
                message="Rate limit exceeded",
                code=error_code,
                http_status=response.status_code,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
            )
        else:
            raise APIError(
                message=error_message,
                code=error_code,
                http_status=response.status_code,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
            )

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request to the Paysafe API.

        Args:
            path: API endpoint path.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.
            retry_config: Custom retry configuration to use for this specific request.
                          If not provided, the client's default configuration is used.

        Returns:
            The parsed JSON response.
        """
        return self.request("GET", path, params=params, headers=headers, retry_config=retry_config)

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request to the Paysafe API.

        Args:
            path: API endpoint path.
            data: JSON data to include in the request body.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.
            retry_config: Custom retry configuration to use for this specific request.
                          If not provided, the client's default configuration is used.

        Returns:
            The parsed JSON response.
        """
        return self.request("POST", path, params=params, data=data, headers=headers, retry_config=retry_config)

    def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request to the Paysafe API.

        Args:
            path: API endpoint path.
            data: JSON data to include in the request body.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.
            retry_config: Custom retry configuration to use for this specific request.
                          If not provided, the client's default configuration is used.

        Returns:
            The parsed JSON response.
        """
        return self.request("PUT", path, params=params, data=data, headers=headers, retry_config=retry_config)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> Dict[str, Any]:
        """
        Make a DELETE request to the Paysafe API.

        Args:
            path: API endpoint path.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.
            retry_config: Custom retry configuration to use for this specific request.
                          If not provided, the client's default configuration is used.

        Returns:
            The parsed JSON response.
        """
        return self.request("DELETE", path, params=params, headers=headers, retry_config=retry_config)
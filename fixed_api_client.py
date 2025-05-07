"""
API client for the Paysafe Python SDK.

This module provides the core functionality for making requests to the Paysafe API.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union, cast
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
from paysafe.version import VERSION

logger = logging.getLogger("paysafe")


class Client:
    """
    Client for the Paysafe API.

    This class handles authentication and request signing, and provides
    methods for making HTTP requests to the Paysafe API.
    """

    DEFAULT_BASE_URL = "https://api.paysafe.com/v1/"
    SANDBOX_BASE_URL = "https://api.sandbox.paysafe.com/v1/"
    
    def __init__(
        self,
        api_key: str,
        environment: str = "production",
        base_url: Optional[str] = None,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        """
        Initialize a new Paysafe API client.

        Args:
            api_key: Your Paysafe API key.
            environment: The API environment to use ('production' or 'sandbox').
            base_url: Override the default API base URL.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of request retries.
        """
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
    ) -> Dict[str, Any]:
        """
        Make a request to the Paysafe API.

        Args:
            method: HTTP method to use ('GET', 'POST', etc.).
            path: API endpoint path.
            params: URL parameters to include in the request.
            data: JSON data to include in the request body.
            headers: Additional HTTP headers to include in the request.

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
            
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=request_headers,
                timeout=self.timeout,
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout as e:
            msg = f"Request timed out after {self.timeout} seconds"
            logger.error(msg)
            raise NetworkError(message=msg) from e
            
        except requests.exceptions.RequestException as e:
            msg = f"Network error: {str(e)}"
            logger.error(msg)
            raise NetworkError(message=msg) from e
            
        except Exception as e:
            msg = f"Error during request: {str(e)}"
            logger.error(msg)
            raise PaysafeError(message=msg) from e

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
    ) -> Dict[str, Any]:
        """
        Make a GET request to the Paysafe API.

        Args:
            path: API endpoint path.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request to the Paysafe API.

        Args:
            path: API endpoint path.
            data: JSON data to include in the request body.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return self.request("POST", path, params=params, data=data, headers=headers)

    def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request to the Paysafe API.

        Args:
            path: API endpoint path.
            data: JSON data to include in the request body.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return self.request("PUT", path, params=params, data=data, headers=headers)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a DELETE request to the Paysafe API.

        Args:
            path: API endpoint path.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return self.request("DELETE", path, params=params, headers=headers)
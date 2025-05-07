"""
Async API client for the Paysafe Python SDK.

This module provides asynchronous functionality for making requests to the Paysafe API.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp

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


class AsyncClient:
    """
    Async client for the Paysafe API.

    This class handles authentication and request signing, and provides
    asynchronous methods for making HTTP requests to the Paysafe API.
    """

    DEFAULT_BASE_URL = "https://api.paysafe.com/v1/"
    SANDBOX_BASE_URL = "https://api.sandbox.paysafe.com/v1/"
    
    def __init__(
        self,
        api_key: str,
        environment: str = "production",
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize a new async Paysafe API client.

        Args:
            api_key: Your Paysafe API key.
            environment: The API environment to use ('production' or 'sandbox').
            base_url: Override the default API base URL.
            timeout: Request timeout in seconds.
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

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async request to the Paysafe API.

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
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        
        json_data = None
        if data is not None:
            json_data = data
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                    timeout=self.timeout,
                ) as response:
                    http_body = await response.text()
                    try:
                        json_body = await response.json() if http_body else {}
                    except ValueError:
                        json_body = {}
                    
                    if response.status < 200 or response.status >= 300:
                        await self._handle_error_response(response, http_body, json_body)
                    
                    return json_body
                
        except aiohttp.ClientError as e:
            msg = f"Network error: {str(e)}"
            logger.error(msg)
            raise NetworkError(message=msg) from e
            
        except asyncio.TimeoutError as e:
            msg = f"Request timed out after {self.timeout} seconds"
            logger.error(msg)
            raise NetworkError(message=msg) from e
            
        except Exception as e:
            msg = f"Error during request: {str(e)}"
            logger.error(msg)
            raise PaysafeError(message=msg) from e

    async def _handle_error_response(
        self,
        response: aiohttp.ClientResponse,
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
        if response.status == 400:
            raise InvalidRequestError(
                message=error_message,
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )
        elif response.status == 401:
            raise AuthenticationError(
                message="Authentication error: Invalid API key provided",
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )
        elif response.status == 429:
            raise RateLimitError(
                message="Rate limit exceeded",
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )
        else:
            raise APIError(
                message=error_message,
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
                code=error_code,
            )

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async GET request to the Paysafe API.

        Args:
            path: API endpoint path.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return await self.request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async POST request to the Paysafe API.

        Args:
            path: API endpoint path.
            data: JSON data to include in the request body.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return await self.request("POST", path, params=params, data=data, headers=headers)

    async def put(
        self,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async PUT request to the Paysafe API.

        Args:
            path: API endpoint path.
            data: JSON data to include in the request body.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return await self.request("PUT", path, params=params, data=data, headers=headers)

    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an async DELETE request to the Paysafe API.

        Args:
            path: API endpoint path.
            params: URL parameters to include in the request.
            headers: Additional HTTP headers to include in the request.

        Returns:
            The parsed JSON response.
        """
        return await self.request("DELETE", path, params=params, headers=headers)
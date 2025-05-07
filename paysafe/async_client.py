"""
Async API client for the Paysafe Python SDK.

This module provides asynchronous functionality for making requests to the Paysafe API.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import aiohttp

from paysafe.utils import load_credentials_from_file, get_api_key_from_credentials

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
payload_logger = logging.getLogger("paysafe.api.payloads")


class AsyncClient:
    """
    Async client for the Paysafe API.

    This class handles authentication and request signing, and provides
    asynchronous methods for making HTTP requests to the Paysafe API.
    """

    DEFAULT_BASE_URL = "https://api.paysafe.com/v1/"
    SANDBOX_BASE_URL = "https://api.test.paysafe.com/v1/"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        environment: str = "production",
        base_url: Optional[str] = None,
        timeout: int = 60,
        credentials_file: Optional[str] = None,
    ):
        """
        Initialize a new async Paysafe API client.

        Args:
            api_key: Your Paysafe API key. If not provided, will look for credentials_file or environment variable.
            environment: The API environment to use ('production' or 'sandbox').
            base_url: Override the default API base URL.
            timeout: Request timeout in seconds.
            credentials_file: Path to a JSON file containing Paysafe credentials (Postman format).
                              If not provided, will check PAYSAFE_CREDENTIALS_FILE environment variable.
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
            # Log the request payload
            payload_logger.debug(f"[ASYNC] REQUEST: {method} {url}")
            payload_logger.debug(f"[ASYNC] PARAMS: {json.dumps(params, indent=2) if params else None}")
            payload_logger.debug(f"[ASYNC] HEADERS: {json.dumps({k: v for k, v in request_headers.items() if k != 'Authorization'}, indent=2) if request_headers else None}")
            payload_logger.debug(f"[ASYNC] DATA: {json.dumps(json_data, indent=2) if json_data else None}")
            
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
                    
                    # Log the response payload
                    payload_logger.debug(f"[ASYNC] RESPONSE STATUS: {response.status}")
                    payload_logger.debug(f"[ASYNC] RESPONSE HEADERS: {json.dumps(dict(response.headers), indent=2)}")
                    
                    try:
                        json_body = await response.json() if http_body else {}
                        payload_logger.debug(f"[ASYNC] RESPONSE BODY: {json.dumps(json_body, indent=2) if http_body else 'No body'}")
                    except ValueError:
                        json_body = {}
                        payload_logger.debug(f"[ASYNC] RESPONSE BODY (non-JSON): {http_body[:1000]}")
                    
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
                code=error_code,
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
            )
        elif response.status == 401:
            raise AuthenticationError(
                message="Authentication error: Invalid API key provided",
                code=error_code,
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
            )
        elif response.status == 429:
            raise RateLimitError(
                message="Rate limit exceeded",
                code=error_code,
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
            )
        else:
            raise APIError(
                message=error_message,
                code=error_code,
                http_status=response.status,
                http_body=http_body,
                json_body=json_body,
                headers=dict(response.headers),
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
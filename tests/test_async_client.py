"""
Tests for the Paysafe async API client.
"""

import json
import pytest
from unittest import mock

from paysafe.async_client import AsyncClient


class TestAsyncClient:
    """Tests for the AsyncClient class."""

    def test_init(self, api_key):
        """Test client initialization."""
        client = AsyncClient(api_key=api_key, environment="sandbox")
        assert client.api_key == api_key
        assert client.environment == "sandbox"
        assert client.base_url == AsyncClient.SANDBOX_BASE_URL

        client = AsyncClient(api_key=api_key, environment="production")
        assert client.environment == "production"
        assert client.base_url == AsyncClient.DEFAULT_BASE_URL

        custom_url = "https://custom.api.paysafe.com/v1/"
        client = AsyncClient(api_key=api_key, base_url=custom_url)
        assert client.base_url == custom_url

    def test_default_headers(self, api_key):
        """Test default headers."""
        client = AsyncClient(api_key=api_key)
        headers = client._get_default_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Basic {api_key}"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "User-Agent" in headers


@pytest.mark.asyncio
class TestAsyncClientRequests:
    """Tests for the AsyncClient request methods."""

    async def test_request_success(self, api_key):
        """Test successful async API request."""
        # Instead of mocking the whole client session, let's mock the request method
        with mock.patch.object(AsyncClient, 'request', 
                              new=mock.AsyncMock(return_value={"key": "value"})) as mock_request:
            
            client = AsyncClient(api_key=api_key)
            result = await client.get("test_path")
            
            # Verify response
            assert result == {"key": "value"}
            
            # Verify method was called
            mock_request.assert_called_once()

    async def test_get(self, api_key):
        """Test GET request method."""
        with mock.patch.object(AsyncClient, 'request') as mock_request:
            mock_request.return_value = {"key": "value"}
            
            client = AsyncClient(api_key=api_key)
            result = await client.get("test_path", params={"param": "value"})
            
            mock_request.assert_called_once_with(
                "GET", "test_path", params={"param": "value"}, headers=None, retry_config=None
            )
            assert result == {"key": "value"}

    async def test_post(self, api_key):
        """Test POST request method."""
        with mock.patch.object(AsyncClient, 'request') as mock_request:
            mock_request.return_value = {"key": "value"}
            
            client = AsyncClient(api_key=api_key)
            result = await client.post(
                "test_path", 
                data={"data": "value"}, 
                params={"param": "value"}
            )
            
            mock_request.assert_called_once_with(
                "POST", 
                "test_path", 
                params={"param": "value"}, 
                data={"data": "value"}, 
                headers=None,
                retry_config=None
            )
            assert result == {"key": "value"}

    async def test_put(self, api_key):
        """Test PUT request method."""
        with mock.patch.object(AsyncClient, 'request') as mock_request:
            mock_request.return_value = {"key": "value"}
            
            client = AsyncClient(api_key=api_key)
            result = await client.put(
                "test_path", 
                data={"data": "value"}, 
                params={"param": "value"}
            )
            
            mock_request.assert_called_once_with(
                "PUT", 
                "test_path", 
                params={"param": "value"}, 
                data={"data": "value"}, 
                headers=None,
                retry_config=None
            )
            assert result == {"key": "value"}

    async def test_delete(self, api_key):
        """Test DELETE request method."""
        with mock.patch.object(AsyncClient, 'request') as mock_request:
            mock_request.return_value = {"key": "value"}
            
            client = AsyncClient(api_key=api_key)
            result = await client.delete("test_path", params={"param": "value"})
            
            mock_request.assert_called_once_with(
                "DELETE", "test_path", params={"param": "value"}, headers=None, retry_config=None
            )
            assert result == {"key": "value"}
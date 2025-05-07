"""
Test fixtures for the Paysafe Python SDK.
"""

import os
import pytest
from unittest import mock

from paysafe import Client


@pytest.fixture
def api_key():
    """Return a test API key."""
    return "test_api_key"


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = mock.Mock()
    response.status_code = 200
    response.text = "{}"
    response.json.return_value = {}
    return response


@pytest.fixture
def mock_session(mock_response):
    """Create a mock session with predefined response."""
    session = mock.Mock()
    session.request.return_value = mock_response
    session.get.return_value = mock_response
    session.post.return_value = mock_response
    session.put.return_value = mock_response
    session.delete.return_value = mock_response
    return session


@pytest.fixture
def client(api_key, mock_session):
    """Create a test client with mocked session."""
    with mock.patch('paysafe.api_client.Session', return_value=mock_session):
        client = Client(api_key=api_key, environment="sandbox")
        client.session = mock_session
        return client

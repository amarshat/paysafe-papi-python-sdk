"""
Paysafe Python SDK.

This module provides a Python SDK for the Paysafe API, allowing
easy integration with Paysafe's payment processing services.
"""

__title__ = "paysafe"
__author__ = "Amar Akshat <amar.akshat@paysafe.com>"

# Import version
from paysafe.version import VERSION

__version__ = VERSION

# Import core classes
from paysafe.api_client import Client
from paysafe.exceptions import (
    PaysafeError,
    AuthenticationError,
    InvalidRequestError,
    APIError,
    NetworkError,
    RateLimitError,
)

# Import synchronous resources
from paysafe.api_resources.payment import Payment
from paysafe.api_resources.customer import Customer
from paysafe.api_resources.card import Card
from paysafe.api_resources.refund import Refund
from paysafe.api_resources.webhook import Webhook

# Import async client and resources
try:
    import aiohttp
    import asyncio
    has_async_deps = True
    from paysafe.async_client import AsyncClient
    from paysafe.api_resources.async_payment import AsyncPayment
except ImportError:
    has_async_deps = False

# Set default logging handler to avoid "No handler found" warnings
import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())

# For backward compatibility
# Functions to expose as part of the SDK
def create_client(api_key: str, environment: str = "production") -> Client:
    """
    Create a new Paysafe API client.

    Args:
        api_key: Your Paysafe API key.
        environment: The API environment to use ('production' or 'sandbox').

    Returns:
        A new instance of the Paysafe Client class.
    """
    return Client(api_key=api_key, environment=environment)

def create_async_client(api_key: str, environment: str = "production"):
    """
    Create a new async Paysafe API client.

    Args:
        api_key: Your Paysafe API key.
        environment: The API environment to use ('production' or 'sandbox').

    Returns:
        A new instance of the AsyncClient class.

    Raises:
        ImportError: If the required async dependencies (aiohttp) are not installed.
    """
    if not has_async_deps:
        raise ImportError(
            "Async client requires additional dependencies. "
            "Please install with `pip install paysafe[async]`"
        )
    return AsyncClient(api_key=api_key, environment=environment)

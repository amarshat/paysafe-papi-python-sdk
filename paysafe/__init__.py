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

# Import resources
from paysafe.api_resources.payment import Payment
from paysafe.api_resources.customer import Customer
from paysafe.api_resources.card import Card
from paysafe.api_resources.refund import Refund
from paysafe.api_resources.webhook import Webhook

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

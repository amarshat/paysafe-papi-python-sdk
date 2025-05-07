"""
Demonstrates how to use the retry functionality in the Paysafe SDK.

This example shows different ways to configure retry behavior at both the client
and per-request levels.
"""

import os
import logging
from paysafe import Client
from paysafe.retry import RetryConfig, RetryStrategy, RetryCondition

# Set up logging to see retry attempts
logging.basicConfig(level=logging.INFO)


def main():
    # Load API key from environment variable or credentials file
    api_key = os.environ.get("PAYSAFE_API_KEY")
    credentials_file = os.environ.get("PAYSAFE_CREDENTIALS_FILE")
    
    if not api_key and not credentials_file:
        print("Please provide credentials by setting either PAYSAFE_API_KEY or "
              "PAYSAFE_CREDENTIALS_FILE environment variable.")
        return
    
    # Example 1: Default retry behavior
    print("\n=== Example 1: Default Retry Behavior ===")
    default_client = Client(
        api_key=api_key,
        credentials_file=credentials_file,
        environment="sandbox",
    )
    print(f"Default retry config: max_retries={default_client.retry_config.max_retries}, "
          f"strategy={default_client.retry_config.retry_strategy.value}")
    
    try:
        # Make a request with default retry behavior
        result = default_client.get("merchantaccountref")
        print(f"Request succeeded with result: {result}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Example 2: Custom client-level retry configuration
    print("\n=== Example 2: Custom Client-Level Retry Configuration ===")
    custom_retry_config = RetryConfig(
        max_retries=5,
        retry_strategy=RetryStrategy.EXPONENTIAL_JITTER,
        initial_delay=1.0,
        max_delay=30.0,
        jitter_factor=0.3,
        retry_conditions=[
            RetryCondition.NETWORK_ERROR,
            RetryCondition.RATE_LIMIT,
            RetryCondition.SERVER_ERROR,
        ],
        # Only retry these status codes
        retry_codes={429, 500, 502, 503, 504},
        # Only retry these methods
        retry_methods={"GET", "POST", "PUT"},
        # Don't retry these sensitive endpoints
        excluded_endpoints={"/payments/settlements"},
    )
    
    custom_client = Client(
        api_key=api_key,
        credentials_file=credentials_file,
        environment="sandbox",
        retry_config=custom_retry_config,
    )
    
    print(f"Custom retry config: max_retries={custom_client.retry_config.max_retries}, "
          f"strategy={custom_client.retry_config.retry_strategy.value}")
    
    try:
        # Make a request with custom client-level retry config
        result = custom_client.get("merchantaccountref")
        print(f"Request succeeded with result: {result}")
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Example 3: Per-request retry configuration
    print("\n=== Example 3: Per-Request Retry Configuration ===")
    # Create a special retry config for a specific request
    payment_retry_config = RetryConfig(
        max_retries=2,  # Fewer retries for payment operations
        retry_strategy=RetryStrategy.FIXED,
        initial_delay=2.0,
        # Only retry network errors for payments, not server errors
        retry_conditions=[RetryCondition.NETWORK_ERROR],
    )
    
    try:
        # Use the default client but override its retry config for this request
        result = default_client.get(
            "merchantaccountref",
            retry_config=payment_retry_config
        )
        print(f"Request succeeded with result: {result}")
    except Exception as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    main()
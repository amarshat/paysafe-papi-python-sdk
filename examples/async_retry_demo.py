"""
Example demonstrating the retry functionality in async mode.

This example shows how to configure and use retry handling in the AsyncClient.
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Any, Callable, Awaitable

# Add the parent directory to the Python path to allow importing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from paysafe import AsyncClient
from paysafe.retry import RetryConfig, RetryStrategy, RetryCondition
from paysafe.exceptions import NetworkError


# Set up logging to see retry process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define attempt counter as a global variable
attempt_counter = 0


async def test_retry_handler():
    """Test the retry handler directly with simulated failures."""
    
    logger.info("\n===== Testing retry handler directly =====")
    
    # Create a retry configuration
    retry_config = RetryConfig(
        max_retries=3,
        retry_strategy=RetryStrategy.FIXED,
        initial_delay=0.1,  # Short delay for demo
        retry_conditions={RetryCondition.ANY_ERROR},
    )
    
    # Create a failing function that will succeed after some attempts
    global attempt_counter
    attempt_counter = 0
    max_failures = 2
    
    async def failing_function(*args, **kwargs):
        global attempt_counter
        attempt_counter += 1
        
        logger.info(f"Attempt {attempt_counter} of function call")
        
        if attempt_counter <= max_failures:
            logger.info(f"Simulating failure on attempt {attempt_counter}")
            raise NetworkError(f"Simulated network error on attempt {attempt_counter}")
        
        logger.info(f"Simulating success on attempt {attempt_counter}")
        return {"status": "success", "attempt": attempt_counter}
    
    # Create the retry handler
    from paysafe.retry import create_async_retry_handler
    retry_handler = create_async_retry_handler(retry_config)
    
    try:
        # Use the retry handler to execute the function with retries
        result = await retry_handler(failing_function, "GET", "test/endpoint")
        logger.info(f"Function succeeded with result: {result}")
    except Exception as e:
        logger.error(f"Function failed after retries: {e}")


async def test_client_retry():
    """Test the retry functionality through the AsyncClient."""
    logger.info("\n===== Testing client retry mechanism =====")
    
    # Create a client with custom retry configuration
    retry_config = RetryConfig(
        max_retries=3,
        retry_strategy=RetryStrategy.EXPONENTIAL,
        initial_delay=0.1,  # Short delay for demo
        backoff_factor=2.0,
        retry_conditions={RetryCondition.NETWORK_ERROR},
    )
    
    api_key = os.environ.get("PAYSAFE_API_KEY", "test_api_key")
    client = AsyncClient(api_key=api_key, environment="sandbox", retry_config=retry_config)
    
    # We'll mock the aiohttp ClientSession to simulate network failures
    import aiohttp
    from unittest import mock
    
    # Reset the attempt counter
    global attempt_counter
    attempt_counter = 0
    max_failures = 2
    
    # Mock session.request to simulate failures
    original_request = aiohttp.ClientSession.request
    
    @classmethod
    async def mock_request(cls, *args, **kwargs):
        global attempt_counter
        attempt_counter += 1
        
        logger.info(f"Network request attempt {attempt_counter}")
        
        if attempt_counter <= max_failures:
            logger.info(f"Simulating network failure on attempt {attempt_counter}")
            raise aiohttp.ClientError(f"Simulated network error on attempt {attempt_counter}")
        
        # Create a mock response for successful attempts
        mock_response = mock.MagicMock()
        mock_response.status = 200
        mock_response.text = mock.AsyncMock(return_value='{"status": "success", "attempt": ' + str(attempt_counter) + '}')
        mock_response.json = mock.AsyncMock(return_value={"status": "success", "attempt": attempt_counter})
        mock_response.__aenter__ = mock.AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = mock.AsyncMock(return_value=None)
        
        logger.info(f"Simulating network success on attempt {attempt_counter}")
        return mock_response
    
    # Apply the mock
    with mock.patch.object(aiohttp.ClientSession, 'request', mock_request):
        try:
            result = await client.get("test-endpoint")
            logger.info(f"Request succeeded with result: {result}")
        except Exception as e:
            logger.error(f"Request failed: {e}")


async def run_demos():
    """Run all retry demonstrations."""
    await test_retry_handler()
    await test_client_retry()


if __name__ == "__main__":
    asyncio.run(run_demos())
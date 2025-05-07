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
        handler_func = retry_handler(failing_function, "GET", "test/endpoint")
        result = await handler_func
        logger.info(f"Function succeeded with result: {result}")
    except Exception as e:
        logger.error(f"Function failed after retries: {e}")


async def test_client_retry():
    """Test the retry functionality through the AsyncClient."""
    logger.info("\n===== Testing client retry mechanism =====")
    
    # Create a client with custom retry configuration
    retry_config = RetryConfig(
        max_retries=3,
        retry_strategy=RetryStrategy.FIXED,
        initial_delay=0.1,  # Short delay for demo
        retry_conditions={RetryCondition.NETWORK_ERROR},
    )
    
    api_key = os.environ.get("PAYSAFE_API_KEY", "test_api_key")
    client = AsyncClient(api_key=api_key, environment="sandbox", retry_config=retry_config)
    
    # We'll create a test class that mimics the structure of AsyncClient but with simulated failures
    class SimulatedClient:
        def __init__(self, max_failures):
            self.attempt_counter = 0
            self.max_failures = max_failures
            
        async def make_request(self, **kwargs):
            """Simulate a request that fails initially but succeeds after retries."""
            self.attempt_counter += 1
            
            logger.info(f"Client request attempt {self.attempt_counter}")
            
            if self.attempt_counter <= self.max_failures:
                logger.info(f"Simulating network failure on attempt {self.attempt_counter}")
                raise NetworkError(f"Simulated network error on attempt {self.attempt_counter}")
            
            logger.info(f"Simulating success on attempt {self.attempt_counter}")
            return {"status": "success", "attempt": self.attempt_counter}
    
    # Create our test client
    test_client = SimulatedClient(max_failures=2)
    
    # Create a retry handler directly for our test function
    from paysafe.retry import create_async_retry_handler
    retry_handler = create_async_retry_handler(retry_config)
    
    try:
        # The retry handler should properly handle the failing function with retries
        handler_func = retry_handler(test_client.make_request, "GET", "test-endpoint")
        result = await handler_func
        logger.info(f"Request succeeded with result: {result}")
    except Exception as e:
        logger.error(f"Request failed: {e}")


async def run_demos():
    """Run all retry demonstrations."""
    await test_retry_handler()
    await test_client_retry()


if __name__ == "__main__":
    asyncio.run(run_demos())
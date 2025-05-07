"""
Retry configuration and logic for the Paysafe Python SDK.

This module provides configurable retry behavior for API requests,
with support for customizing retry conditions, backoff strategies, and more.
"""

import logging
import random
import time
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from paysafe.exceptions import PaysafeError, NetworkError, RateLimitError

logger = logging.getLogger("paysafe")


class RetryStrategy(Enum):
    """Enum defining different backoff strategies for retries."""
    
    # No retry
    NONE = "none"
    
    # Retry with a fixed delay between attempts
    FIXED = "fixed"
    
    # Retry with exponentially increasing delays between attempts
    EXPONENTIAL = "exponential"
    
    # Retry with exponential backoff plus random jitter
    EXPONENTIAL_JITTER = "exponential_jitter"


class RetryCondition(Enum):
    """Enum defining conditions under which to retry a request."""
    
    # Retry on network-related errors (connection issues, timeouts)
    NETWORK_ERROR = "network_error"
    
    # Retry on rate limit errors (HTTP 429)
    RATE_LIMIT = "rate_limit"
    
    # Retry on server errors (HTTP 5xx)
    SERVER_ERROR = "server_error"
    
    # Retry on any error
    ANY_ERROR = "any_error"


class RetryConfig:
    """
    Configuration for retry behavior.
    
    This class allows specifying how and when requests should be retried.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER,
        retry_conditions: Optional[List[RetryCondition]] = None,
        initial_delay: float = 0.5,  # in seconds
        max_delay: float = 8.0,  # in seconds
        jitter_factor: float = 0.25,
        retry_codes: Optional[Set[int]] = None,
        backoff_factor: float = 2.0,
        retry_methods: Optional[Set[str]] = None,
        excluded_endpoints: Optional[Set[str]] = None,
    ):
        """
        Initialize a new retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts.
            retry_strategy: Strategy to use for retry timing.
            retry_conditions: List of conditions under which to retry.
            initial_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
            jitter_factor: Amount of randomness to add to delay (0.0-1.0).
            retry_codes: Set of HTTP status codes to retry on.
            backoff_factor: Multiplier for exponential backoff.
            retry_methods: Set of HTTP methods to retry (e.g., {"GET", "POST"}).
            excluded_endpoints: Set of API endpoints to exclude from retries.
        """
        self.max_retries = max_retries
        self.retry_strategy = retry_strategy
        
        # Default retry conditions if not specified
        self.retry_conditions = retry_conditions or [
            RetryCondition.NETWORK_ERROR,
            RetryCondition.RATE_LIMIT,
            RetryCondition.SERVER_ERROR,
        ]
        
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        
        # Default retry status codes if not specified
        self.retry_codes = retry_codes or {
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }
        
        self.backoff_factor = backoff_factor
        
        # Default to retrying all HTTP methods except DELETE
        self.retry_methods = retry_methods or {
            "GET", "POST", "PUT", "PATCH", "HEAD", "OPTIONS"
        }
        
        # No excluded endpoints by default
        self.excluded_endpoints = excluded_endpoints or set()
    
    def should_retry(
        self,
        method: str,
        path: str,
        attempt: int,
        error: Optional[Exception] = None,
        status_code: Optional[int] = None,
    ) -> bool:
        """
        Determine if a request should be retried.
        
        Args:
            method: The HTTP method of the request.
            path: The path/endpoint of the request.
            attempt: The current attempt number (0-based).
            error: The exception that occurred, if any.
            status_code: The HTTP status code received, if any.
            
        Returns:
            True if the request should be retried, False otherwise.
        """
        # Check if we've exceeded the maximum retry count
        if attempt >= self.max_retries:
            return False
        
        # Check if the HTTP method should be retried
        if method.upper() not in self.retry_methods:
            return False
        
        # Check if the endpoint is excluded from retries
        for excluded in self.excluded_endpoints:
            if excluded in path:
                return False
        
        # Check based on error type
        if error is not None:
            if RetryCondition.ANY_ERROR in self.retry_conditions:
                return True
                
            if (RetryCondition.NETWORK_ERROR in self.retry_conditions and 
                isinstance(error, NetworkError)):
                return True
                
            if (RetryCondition.RATE_LIMIT in self.retry_conditions and 
                isinstance(error, RateLimitError)):
                return True
        
        # Check based on status code
        if status_code is not None:
            if status_code in self.retry_codes:
                if (RetryCondition.RATE_LIMIT in self.retry_conditions and 
                    status_code == 429):
                    return True
                    
                if (RetryCondition.SERVER_ERROR in self.retry_conditions and 
                    500 <= status_code < 600):
                    return True
        
        return False
    
    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate the delay before the next retry attempt.
        
        Args:
            attempt: The current attempt number (0-based).
            
        Returns:
            The delay in seconds before the next retry attempt.
        """
        if self.retry_strategy == RetryStrategy.NONE:
            return 0
        
        if self.retry_strategy == RetryStrategy.FIXED:
            return self.initial_delay
        
        # For exponential strategies, calculate base delay
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if needed
        if self.retry_strategy == RetryStrategy.EXPONENTIAL_JITTER:
            jitter = random.uniform(-self.jitter_factor, self.jitter_factor)
            delay = delay * (1 + jitter)
        
        return max(0, delay)  # Ensure non-negative delay


def create_retry_handler(config: RetryConfig) -> Callable:
    """
    Create a retry handler function using the given configuration.
    
    Args:
        config: The retry configuration to use.
        
    Returns:
        A function that handles retrying requests.
    """
    def retry_handler(
        request_func: Callable,
        method: str,
        path: str,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Execute a request with retry logic.
        
        Args:
            request_func: The function to call to execute the request.
            method: The HTTP method of the request.
            path: The path/endpoint of the request.
            *args: Positional arguments to pass to the request function.
            **kwargs: Keyword arguments to pass to the request function.
            
        Returns:
            The response from the request function.
            
        Raises:
            The last exception encountered if all retries fail.
        """
        attempt = 0
        last_error = None
        
        while True:
            try:
                return request_func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                # Extract status code from error if available
                status_code = getattr(e, "http_status", None)
                
                # Check if we should retry
                if not config.should_retry(method, path, attempt, e, status_code):
                    raise
                
                # Calculate delay
                delay = config.get_retry_delay(attempt)
                
                # Log retry attempt
                logger.warning(
                    f"Request failed (attempt {attempt+1}/{config.max_retries+1}). "
                    f"Retrying in {delay:.2f} seconds. Error: {str(e)}"
                )
                
                # Wait before retrying
                time.sleep(delay)
                
                # Increment attempt counter
                attempt += 1
    
    return retry_handler
"""
Retry functionality for the Paysafe SDK.

This module provides classes and functions to handle retrying failed API requests
with configurable retry strategies, delays, and conditions.
"""

import enum
import logging
import random
import time
from typing import Any, Callable, Dict, Optional, Set, TypeVar, Union, cast

from paysafe.exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    NetworkError,
    PaysafeError,
    RateLimitError,
)

T = TypeVar("T")
logger = logging.getLogger("paysafe")


class RetryStrategy(enum.Enum):
    """Enum for different retry delay strategies."""

    NONE = "none"  # No delay between retries
    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff between retries
    EXPONENTIAL_JITTER = "exponential_jitter"  # Exponential backoff with jitter


class RetryCondition(enum.Enum):
    """Enum for different retry conditions."""

    NETWORK_ERROR = "network_error"  # Retry on network errors
    RATE_LIMIT = "rate_limit"  # Retry on rate limit errors
    SERVER_ERROR = "server_error"  # Retry on server errors (5xx)
    ANY_ERROR = "any_error"  # Retry on any error (except authentication errors)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER,
        retry_conditions: Optional[Set[RetryCondition]] = None,
        initial_delay: float = 0.5,
        max_delay: float = 30.0,
        jitter_factor: float = 0.25,
        retry_codes: Optional[Set[int]] = None,
        backoff_factor: float = 2.0,
        retry_methods: Optional[Set[str]] = None,
        excluded_endpoints: Optional[Set[str]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts.
            retry_strategy: Strategy for calculating delay between retries.
            retry_conditions: Set of conditions that trigger retries.
            initial_delay: Initial delay in seconds.
            max_delay: Maximum delay in seconds.
            jitter_factor: Random jitter factor (0.0 to 1.0) to add to delay.
            retry_codes: Set of HTTP status codes to retry on.
            backoff_factor: Exponential backoff multiplier.
            retry_methods: Set of HTTP methods to retry.
            excluded_endpoints: Set of API endpoints to exclude from retries.
        """
        self.max_retries = max_retries
        self.retry_strategy = retry_strategy
        
        # Set default retry conditions if none provided
        if retry_conditions is None:
            self.retry_conditions = {
                RetryCondition.NETWORK_ERROR,
                RetryCondition.RATE_LIMIT,
                RetryCondition.SERVER_ERROR,
            }
        else:
            self.retry_conditions = retry_conditions
        
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter_factor = jitter_factor
        
        # Set default retry codes if none provided
        if retry_codes is None:
            self.retry_codes = {429, 500, 502, 503, 504}
        else:
            self.retry_codes = retry_codes
        
        self.backoff_factor = backoff_factor
        
        # Set default retry methods if none provided
        if retry_methods is None:
            self.retry_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
        else:
            self.retry_methods = retry_methods
        
        # Initialize excluded endpoints
        self.excluded_endpoints = excluded_endpoints or set()

    def should_retry(
        self,
        method: str,
        path: str,
        attempt: int,
        error: Optional[PaysafeError] = None,
        status_code: Optional[int] = None,
    ) -> bool:
        """
        Determine if a request should be retried.

        Args:
            method: HTTP method of the request.
            path: API endpoint path.
            attempt: Current attempt number (0-based).
            error: The error that occurred, if any.
            status_code: HTTP status code received, if any.

        Returns:
            True if the request should be retried, False otherwise.
        """
        # Check if we've exceeded the maximum retry attempts
        if attempt >= self.max_retries:
            logger.debug("Max retry attempts (%d) reached", self.max_retries)
            return False
        
        # Check if the HTTP method is allowed for retries
        if method not in self.retry_methods:
            logger.debug("HTTP method %s not configured for retries", method)
            return False
        
        # Check if the endpoint is excluded from retries
        for excluded in self.excluded_endpoints:
            if path.startswith(excluded):
                logger.debug("Endpoint %s is excluded from retries", path)
                return False
        
        # Check for authentication errors, which should never be retried
        if isinstance(error, AuthenticationError):
            logger.debug("Authentication errors are never retried")
            return False
        
        # Check if we should retry based on the error type
        if error is not None:
            if RetryCondition.ANY_ERROR in self.retry_conditions:
                return True
            
            if (
                isinstance(error, NetworkError)
                and RetryCondition.NETWORK_ERROR in self.retry_conditions
            ):
                logger.debug("Retrying due to network error: %s", str(error))
                return True
            
            if (
                isinstance(error, RateLimitError)
                and RetryCondition.RATE_LIMIT in self.retry_conditions
            ):
                logger.debug("Retrying due to rate limit error: %s", str(error))
                return True
            
            if (
                isinstance(error, APIError)
                and RetryCondition.SERVER_ERROR in self.retry_conditions
            ):
                logger.debug("Retrying due to server error: %s", str(error))
                return True
        
        # Check if we should retry based on the status code
        if status_code is not None and status_code in self.retry_codes:
            logger.debug("Retrying due to status code: %d", status_code)
            return True
        
        # If we get here, we shouldn't retry
        return False

    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate the delay before the next retry attempt.

        Args:
            attempt: Current attempt number (0-based).

        Returns:
            The delay in seconds before the next retry.
        """
        if self.retry_strategy == RetryStrategy.NONE:
            return 0
        
        if self.retry_strategy == RetryStrategy.FIXED:
            return self.initial_delay
        
        # Calculate exponential backoff
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        
        # Apply maximum delay cap
        delay = min(delay, self.max_delay)
        
        # Add jitter if configured
        if self.retry_strategy == RetryStrategy.EXPONENTIAL_JITTER and self.jitter_factor > 0:
            jitter = random.uniform(0, self.jitter_factor)
            delay = delay * (1 + jitter)
        
        return delay


def create_retry_handler(
    config: RetryConfig,
) -> Callable[[Callable[..., T], str, str, Dict[str, Any]], T]:
    """
    Create a retry handler function.

    Args:
        config: Retry configuration to use.

    Returns:
        A function that will handle retrying a request function.
    """

    def retry_handler(
        request_func: Callable[..., T], method: str, path: str, **kwargs: Any
    ) -> T:
        """
        Handle retrying a request.

        Args:
            request_func: The function to call to make the request.
            method: The HTTP method of the request.
            path: The API endpoint path.
            **kwargs: Additional arguments to pass to the request function.

        Returns:
            The result of the request.

        Raises:
            The last error that occurred if all retries fail.
        """
        attempt = 0
        last_error = None
        
        while True:
            try:
                # Attempt the request
                return request_func(**kwargs)
            
            except PaysafeError as error:
                last_error = error
                
                # Check if we should retry
                if not config.should_retry(method, path, attempt, error):
                    raise
                
                # Calculate delay before next retry
                delay = config.get_retry_delay(attempt)
                
                # Log the retry attempt
                logger.info(
                    "Request failed with %s. Retrying in %.2f seconds "
                    "(attempt %d/%d)",
                    error.__class__.__name__,
                    delay,
                    attempt + 1,
                    config.max_retries,
                )
                
                # Wait before retrying
                if delay > 0:
                    time.sleep(delay)
                
                # Increment attempt counter
                attempt += 1
        
        # This should never be reached due to the while True loop
        # and the explicit raise in the exception handler
        assert last_error is not None  # For type checking
        raise last_error

    return retry_handler
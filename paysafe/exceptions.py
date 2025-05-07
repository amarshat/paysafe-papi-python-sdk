"""
Exception classes for the Paysafe Python SDK.

This module defines the exception hierarchy used throughout the SDK.
"""

from typing import Dict, Any, Optional, List


class PaysafeError(Exception):
    """Base exception for all Paysafe-related errors."""

    def __init__(
        self,
        message: Optional[str] = None,
        http_status: Optional[int] = None,
        http_body: Optional[str] = None,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
    ):
        """
        Initialize a new PaysafeError.

        Args:
            message: A human-readable message describing the error.
            http_status: The HTTP status code from the API response.
            http_body: The raw HTTP body from the API response.
            json_body: The parsed JSON body from the API response.
            headers: The HTTP headers from the API response.
            code: The Paysafe error code.
        """
        super().__init__(message)
        self.message = message
        self.http_status = http_status
        self.http_body = http_body
        self.json_body = json_body
        self.headers = headers or {}
        self.code = code
        self._error_details: List[Dict[str, Any]] = []

        # Try to parse more error details if possible
        if self.json_body and "errors" in self.json_body:
            self._error_details = self.json_body["errors"]

    def __str__(self) -> str:
        """Return a string representation of the error."""
        status_string = f", status={self.http_status}" if self.http_status else ""
        code_string = f", code={self.code}" if self.code else ""
        return f"{self.message}{status_string}{code_string}"

    @property
    def error_details(self) -> List[Dict[str, Any]]:
        """Get detailed error information if available."""
        return self._error_details


class AuthenticationError(PaysafeError):
    """Raised when authentication with the API fails."""
    pass


class InvalidRequestError(PaysafeError):
    """Raised when the request parameters are invalid."""
    pass


class APIError(PaysafeError):
    """Raised when the Paysafe API returns an error."""
    pass


class NetworkError(PaysafeError):
    """Raised when there are issues connecting to the Paysafe API."""
    pass


class RateLimitError(PaysafeError):
    """Raised when the API rate limit is exceeded."""
    pass


class MissingDependencyError(PaysafeError):
    """Raised when a required dependency is missing."""
    pass


class ValidationError(PaysafeError):
    """Raised when data validation fails."""
    pass

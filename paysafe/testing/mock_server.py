"""
Mock Paysafe API server for testing.

This module provides a mock server implementation of the Paysafe API
for local testing without requiring actual API credentials.
"""

import copy
import json
import random
import re
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

from paysafe.exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    NetworkError,
    PaysafeError,
    RateLimitError,
)


class MockResponse:
    """Mock HTTP response object."""

    def __init__(
        self,
        status_code: int,
        content: Union[Dict[str, Any], List[Any], str],
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize a mock response.

        Args:
            status_code: HTTP status code
            content: Response content
            headers: HTTP headers
        """
        self.status_code = status_code
        self._content = content
        self.headers = headers or {}
        self.ok = 200 <= status_code < 300

    def json(self) -> Union[Dict[str, Any], List[Any]]:
        """Return the response content as JSON."""
        if isinstance(self._content, (dict, list)):
            return self._content
        return json.loads(self._content)

    @property
    def text(self) -> str:
        """Return the response content as text."""
        if isinstance(self._content, str):
            return self._content
        return json.dumps(self._content)

    @property
    def content(self) -> bytes:
        """Return the response content as bytes."""
        return self.text.encode("utf-8")


class Route:
    """Route definition for the mock server."""

    def __init__(
        self,
        method: str,
        path_pattern: str,
        handler: Callable[..., MockResponse],
        required_params: Optional[List[str]] = None,
    ):
        """
        Initialize a route.

        Args:
            method: HTTP method (GET, POST, etc.)
            path_pattern: URL path pattern (can contain regex patterns)
            handler: Function to handle the request
            required_params: List of required params that must be present
        """
        self.method = method.upper()
        self.path_pattern = re.compile(f"^{path_pattern}$")
        self.handler = handler
        self.required_params = required_params or []

    def matches(self, method: str, path: str) -> bool:
        """
        Check if the route matches the given method and path.

        Args:
            method: HTTP method
            path: URL path

        Returns:
            True if the route matches
        """
        return self.method == method.upper() and bool(self.path_pattern.match(path))

    def extract_path_params(self, path: str) -> Dict[str, str]:
        """
        Extract path parameters from the URL.

        Args:
            path: URL path

        Returns:
            Dictionary of path parameters
        """
        match = self.path_pattern.match(path)
        if not match:
            return {}
        return match.groupdict()


class MockPaysafeServer:
    """
    Mock Paysafe API server.

    This class simulates the Paysafe API server for local testing.
    """

    def __init__(
        self,
        api_key: str = "mock_api_key",
        fail_rate: float = 0.0,
        latency: Tuple[float, float] = (0.0, 0.0),
    ):
        """
        Initialize the mock server.

        Args:
            api_key: API key to use for authentication
            fail_rate: Probability of random failure (0.0 to 1.0)
            latency: Range of random latency in seconds (min, max)
        """
        self.api_key = api_key
        self.fail_rate = fail_rate
        self.latency_range = latency
        self.routes: List[Route] = []
        self.data: Dict[str, Dict[str, Any]] = {
            "customers": {},
            "payments": {},
            "cards": {},
            "refunds": {},
            "webhooks": {},
        }
        self.idempotency_keys: Dict[str, Dict[str, Any]] = {}
        self._initialize_routes()

    def _initialize_routes(self) -> None:
        """Initialize API routes."""
        # Customer routes
        self.routes.append(
            Route("POST", "/customers", self._create_customer, ["firstName", "lastName"])
        )
        self.routes.append(Route("GET", "/customers/(?P<customer_id>[^/]+)", self._get_customer))
        self.routes.append(Route("GET", "/customers", self._list_customers))
        self.routes.append(
            Route("PUT", "/customers/(?P<customer_id>[^/]+)", self._update_customer)
        )
        self.routes.append(
            Route("DELETE", "/customers/(?P<customer_id>[^/]+)", self._delete_customer)
        )

        # Payment routes
        self.routes.append(
            Route(
                "POST",
                "/payments",
                self._create_payment,
                ["amount", "currencyCode", "paymentMethod"],
            )
        )
        self.routes.append(Route("GET", "/payments/(?P<payment_id>[^/]+)", self._get_payment))
        self.routes.append(Route("GET", "/payments", self._list_payments))

        # Card routes
        self.routes.append(
            Route(
                "POST",
                "/customers/(?P<customer_id>[^/]+)/cards",
                self._create_card,
                ["cardNumber", "cardExpiry"],
            )
        )
        self.routes.append(
            Route(
                "GET",
                "/customers/(?P<customer_id>[^/]+)/cards/(?P<card_id>[^/]+)",
                self._get_card,
            )
        )
        self.routes.append(
            Route("GET", "/customers/(?P<customer_id>[^/]+)/cards", self._list_cards)
        )
        self.routes.append(
            Route(
                "DELETE",
                "/customers/(?P<customer_id>[^/]+)/cards/(?P<card_id>[^/]+)",
                self._delete_card,
            )
        )

        # Refund routes
        self.routes.append(
            Route(
                "POST",
                "/payments/(?P<payment_id>[^/]+)/refunds",
                self._create_refund,
                ["amount"],
            )
        )
        self.routes.append(
            Route(
                "GET",
                "/payments/(?P<payment_id>[^/]+)/refunds/(?P<refund_id>[^/]+)",
                self._get_refund,
            )
        )
        self.routes.append(
            Route("GET", "/payments/(?P<payment_id>[^/]+)/refunds", self._list_refunds)
        )

        # Webhook routes
        self.routes.append(Route("POST", "/webhooks", self._create_webhook, ["url", "events"]))
        self.routes.append(Route("GET", "/webhooks/(?P<webhook_id>[^/]+)", self._get_webhook))
        self.routes.append(Route("GET", "/webhooks", self._list_webhooks))
        self.routes.append(
            Route("DELETE", "/webhooks/(?P<webhook_id>[^/]+)", self._delete_webhook)
        )

    def _simulate_random_behavior(self) -> Optional[MockResponse]:
        """
        Simulate random latency and failures.

        Returns:
            A mock error response if the request fails, None otherwise
        """
        # Simulate latency
        if self.latency_range != (0.0, 0.0):
            min_latency, max_latency = self.latency_range
            latency = random.uniform(min_latency, max_latency)
            time.sleep(latency)

        # Simulate random failures
        if random.random() < self.fail_rate:
            error_types = [
                (NetworkError, 500, "Network error occurred"),
                (APIError, 500, "Internal server error"),
                (RateLimitError, 429, "Rate limit exceeded"),
            ]
            error_class, status_code, message = random.choice(error_types)
            return self._create_error_response(status_code, message)

        return None

    def _create_error_response(
        self, status_code: int, message: str, code: str = "ERROR"
    ) -> MockResponse:
        """
        Create an error response.

        Args:
            status_code: HTTP status code
            message: Error message
            code: Error code

        Returns:
            A mock error response
        """
        return MockResponse(
            status_code,
            {
                "error": {
                    "code": code,
                    "message": message,
                    "details": [],
                }
            },
        )

    def _validate_params(self, params: Dict[str, Any], required: List[str]) -> Optional[MockResponse]:
        """
        Validate required parameters.

        Args:
            params: Request parameters
            required: List of required parameters

        Returns:
            A mock error response if validation fails, None otherwise
        """
        missing = [p for p in required if p not in params]
        if missing:
            missing_str = ", ".join(missing)
            return self._create_error_response(
                400, f"Missing required parameters: {missing_str}", "INVALID_REQUEST"
            )
        return None

    def _verify_auth(self, headers: Dict[str, str]) -> Optional[MockResponse]:
        """
        Verify API key authentication.

        Args:
            headers: Request headers

        Returns:
            A mock error response if authentication fails, None otherwise
        """
        auth_header = headers.get("Authorization", "")
        if not auth_header.startswith("Basic ") or self.api_key not in auth_header:
            return self._create_error_response(
                401, "Invalid API key provided", "UNAUTHORIZED"
            )
        return None

    def _handle_idempotency(
        self, headers: Dict[str, str], request_data: Dict[str, Any], method: str, path: str
    ) -> Optional[MockResponse]:
        """
        Handle idempotency keys.

        Args:
            headers: Request headers
            request_data: Request data
            method: HTTP method
            path: URL path

        Returns:
            A cached response if an idempotent request is found, None otherwise
        """
        idempotency_key = headers.get("Idempotency-Key")
        if idempotency_key and method == "POST":
            if idempotency_key in self.idempotency_keys:
                # Return cached response for the same idempotency key
                return MockResponse(
                    200, self.idempotency_keys[idempotency_key], {"Idempotent-Replayed": "true"}
                )
        return None

    def handle_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> MockResponse:
        """
        Handle an API request.

        Args:
            method: HTTP method
            path: URL path
            headers: Request headers
            params: Query parameters
            data: Request body data

        Returns:
            A mock response
        """
        # Check for random failure
        random_error = self._simulate_random_behavior()
        if random_error:
            return random_error

        # Verify authentication
        auth_error = self._verify_auth(headers)
        if auth_error:
            return auth_error

        # Handle idempotent requests
        if data:
            idempotent_response = self._handle_idempotency(headers, data, method, path)
            if idempotent_response:
                return idempotent_response

        # Find matching route
        for route in self.routes:
            if route.matches(method, path):
                path_params = route.extract_path_params(path)
                
                # Validate required parameters
                if data and route.required_params:
                    validation_error = self._validate_params(data, route.required_params)
                    if validation_error:
                        return validation_error
                
                # Handle the request
                try:
                    response = route.handler(
                        headers=headers,
                        params=params or {},
                        data=data or {},
                        path_params=path_params,
                    )
                    
                    # Cache response for idempotent requests
                    idempotency_key = headers.get("Idempotency-Key")
                    if idempotency_key and method == "POST" and response.status_code == 200:
                        self.idempotency_keys[idempotency_key] = response.json()
                        
                    return response
                except Exception as e:
                    return self._create_error_response(500, f"Server error: {str(e)}")

        # No matching route found
        return self._create_error_response(404, f"Path not found: {path}", "NOT_FOUND")

    def reset(self) -> None:
        """Reset all mock data."""
        self.data = {
            "customers": {},
            "payments": {},
            "cards": {},
            "refunds": {},
            "webhooks": {},
        }
        self.idempotency_keys = {}

    def _get_id(self, prefix: str) -> str:
        """
        Generate a unique ID with the given prefix.

        Args:
            prefix: ID prefix

        Returns:
            A unique ID
        """
        return f"{prefix}_{str(uuid.uuid4()).replace('-', '')}"

    def _timestamps(self) -> Dict[str, str]:
        """
        Generate current timestamps.

        Returns:
            Dictionary with created_at and updated_at timestamps
        """
        now = datetime.now().isoformat()
        return {"createdAt": now, "updatedAt": now}

    # Customer handlers
    def _create_customer(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Create a customer."""
        customer_id = self._get_id("cust")
        customer = {**data, "id": customer_id, **self._timestamps(), "status": "ACTIVE"}
        self.data["customers"][customer_id] = customer
        return MockResponse(200, customer)

    def _get_customer(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Get a customer by ID."""
        customer_id = path_params["customer_id"]
        if customer_id not in self.data["customers"]:
            return self._create_error_response(
                404, f"Customer not found: {customer_id}", "NOT_FOUND"
            )
        return MockResponse(200, self.data["customers"][customer_id])

    def _list_customers(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """List customers with optional filtering."""
        limit = int(params.get("limit", 10))
        offset = int(params.get("offset", 0))
        
        # Apply filters
        customers = list(self.data["customers"].values())
        if "email" in params:
            customers = [c for c in customers if params["email"] in c.get("email", "")]
        if "merchantCustomerId" in params:
            customers = [
                c for c in customers if c.get("merchantCustomerId") == params["merchantCustomerId"]
            ]
        if "status" in params:
            customers = [c for c in customers if c.get("status") == params["status"]]
            
        # Paginate results
        paginated = customers[offset:offset + limit]
        result = {
            "customers": paginated,
            "pagination": {
                "totalItems": len(customers),
                "limit": limit,
                "offset": offset,
            },
        }
        return MockResponse(200, result)

    def _update_customer(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Update a customer."""
        customer_id = path_params["customer_id"]
        if customer_id not in self.data["customers"]:
            return self._create_error_response(
                404, f"Customer not found: {customer_id}", "NOT_FOUND"
            )
            
        # Update customer
        customer = self.data["customers"][customer_id]
        updated = {**customer, **data, "updatedAt": datetime.now().isoformat()}
        self.data["customers"][customer_id] = updated
        return MockResponse(200, updated)

    def _delete_customer(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Delete a customer."""
        customer_id = path_params["customer_id"]
        if customer_id not in self.data["customers"]:
            return self._create_error_response(
                404, f"Customer not found: {customer_id}", "NOT_FOUND"
            )
            
        # Delete customer
        del self.data["customers"][customer_id]
        return MockResponse(200, {"deleted": True})

    # Payment handlers
    def _create_payment(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Create a payment."""
        payment_id = self._get_id("pmt")
        
        # Simulate payment processing
        status = "COMPLETED"
        payment_method = data.get("paymentMethod", {})
        amount = data.get("amount", 0)
        
        # Simulate card validation failures
        if payment_method.get("cardNumber", "").startswith("4000000000000"):
            if payment_method.get("cardNumber") == "4000000000000002":
                return self._create_error_response(
                    400, "Card declined: insufficient funds", "CARD_DECLINED"
                )
            elif payment_method.get("cardNumber") == "4000000000000069":
                return self._create_error_response(
                    400, "Card declined: expired card", "CARD_EXPIRED"
                )
            elif payment_method.get("cardNumber") == "4000000000000127":
                return self._create_error_response(
                    400, "Invalid CVV", "INVALID_CVV"
                )
                
        # Simulate larger payment amounts being processed
        if amount > 10000:
            status = "PENDING"
            
        payment = {
            **data,
            "id": payment_id,
            "status": status,
            **self._timestamps(),
            "availableToRefund": amount,
        }
        self.data["payments"][payment_id] = payment
        return MockResponse(200, payment)

    def _get_payment(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Get a payment by ID."""
        payment_id = path_params["payment_id"]
        if payment_id not in self.data["payments"]:
            return self._create_error_response(
                404, f"Payment not found: {payment_id}", "NOT_FOUND"
            )
        return MockResponse(200, self.data["payments"][payment_id])

    def _list_payments(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """List payments with optional filtering."""
        limit = int(params.get("limit", 10))
        offset = int(params.get("offset", 0))
        
        # Apply filters
        payments = list(self.data["payments"].values())
        if "status" in params:
            payments = [p for p in payments if p.get("status") == params["status"]]
            
        # Paginate results
        paginated = payments[offset:offset + limit]
        result = {
            "payments": paginated,
            "pagination": {
                "totalItems": len(payments),
                "limit": limit,
                "offset": offset,
            },
        }
        return MockResponse(200, result)

    # Card handlers
    def _create_card(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Create a card for a customer."""
        customer_id = path_params["customer_id"]
        if customer_id not in self.data["customers"]:
            return self._create_error_response(
                404, f"Customer not found: {customer_id}", "NOT_FOUND"
            )
            
        card_id = self._get_id("card")
        
        # Mask card number for security
        if "cardNumber" in data:
            masked = data["cardNumber"][-4:].rjust(len(data["cardNumber"]), "*")
            data["cardNumber"] = masked
            
        card = {
            **data,
            "id": card_id,
            "customerId": customer_id,
            "status": "ACTIVE",
            **self._timestamps(),
        }
        
        # Initialize cards collection for this customer if it doesn't exist
        if customer_id not in self.data["cards"]:
            self.data["cards"][customer_id] = {}
            
        self.data["cards"][customer_id][card_id] = card
        return MockResponse(200, card)

    def _get_card(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Get a card by ID."""
        customer_id = path_params["customer_id"]
        card_id = path_params["card_id"]
        
        if customer_id not in self.data["cards"] or card_id not in self.data["cards"][customer_id]:
            return self._create_error_response(
                404, f"Card not found: {card_id}", "NOT_FOUND"
            )
            
        return MockResponse(200, self.data["cards"][customer_id][card_id])

    def _list_cards(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """List cards for a customer."""
        customer_id = path_params["customer_id"]
        
        if customer_id not in self.data["customers"]:
            return self._create_error_response(
                404, f"Customer not found: {customer_id}", "NOT_FOUND"
            )
            
        if customer_id not in self.data["cards"]:
            cards = []
        else:
            cards = list(self.data["cards"][customer_id].values())
            
        # Apply filters
        if "status" in params:
            cards = [c for c in cards if c.get("status") == params["status"]]
            
        result = {
            "cards": cards,
            "pagination": {
                "totalItems": len(cards),
                "limit": len(cards),
                "offset": 0,
            },
        }
        return MockResponse(200, result)

    def _delete_card(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Delete a card."""
        customer_id = path_params["customer_id"]
        card_id = path_params["card_id"]
        
        if (
            customer_id not in self.data["cards"]
            or card_id not in self.data["cards"][customer_id]
        ):
            return self._create_error_response(
                404, f"Card not found: {card_id}", "NOT_FOUND"
            )
            
        # Delete card
        del self.data["cards"][customer_id][card_id]
        return MockResponse(200, {"deleted": True})

    # Refund handlers
    def _create_refund(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Create a refund for a payment."""
        payment_id = path_params["payment_id"]
        
        if payment_id not in self.data["payments"]:
            return self._create_error_response(
                404, f"Payment not found: {payment_id}", "NOT_FOUND"
            )
            
        payment = self.data["payments"][payment_id]
        amount = data.get("amount", 0)
        
        if amount > payment.get("availableToRefund", 0):
            return self._create_error_response(
                400, "Refund amount exceeds available amount", "INVALID_REQUEST"
            )
            
        refund_id = self._get_id("rfnd")
        refund = {
            **data,
            "id": refund_id,
            "paymentId": payment_id,
            "status": "COMPLETED",
            **self._timestamps(),
        }
        
        # Initialize refunds collection for this payment if it doesn't exist
        if payment_id not in self.data["refunds"]:
            self.data["refunds"][payment_id] = {}
            
        self.data["refunds"][payment_id][refund_id] = refund
        
        # Update available amount to refund on the payment
        payment["availableToRefund"] -= amount
        
        return MockResponse(200, refund)

    def _get_refund(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Get a refund by ID."""
        payment_id = path_params["payment_id"]
        refund_id = path_params["refund_id"]
        
        if (
            payment_id not in self.data["refunds"]
            or refund_id not in self.data["refunds"][payment_id]
        ):
            return self._create_error_response(
                404, f"Refund not found: {refund_id}", "NOT_FOUND"
            )
            
        return MockResponse(200, self.data["refunds"][payment_id][refund_id])

    def _list_refunds(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """List refunds for a payment."""
        payment_id = path_params["payment_id"]
        
        if payment_id not in self.data["payments"]:
            return self._create_error_response(
                404, f"Payment not found: {payment_id}", "NOT_FOUND"
            )
            
        if payment_id not in self.data["refunds"]:
            refunds = []
        else:
            refunds = list(self.data["refunds"][payment_id].values())
            
        result = {
            "refunds": refunds,
            "pagination": {
                "totalItems": len(refunds),
                "limit": len(refunds),
                "offset": 0,
            },
        }
        return MockResponse(200, result)

    # Webhook handlers
    def _create_webhook(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Create a webhook subscription."""
        webhook_id = self._get_id("whk")
        webhook = {
            **data,
            "id": webhook_id,
            "status": "ACTIVE",
            **self._timestamps(),
        }
        self.data["webhooks"][webhook_id] = webhook
        return MockResponse(200, webhook)

    def _get_webhook(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Get a webhook by ID."""
        webhook_id = path_params["webhook_id"]
        
        if webhook_id not in self.data["webhooks"]:
            return self._create_error_response(
                404, f"Webhook not found: {webhook_id}", "NOT_FOUND"
            )
            
        return MockResponse(200, self.data["webhooks"][webhook_id])

    def _list_webhooks(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """List webhooks."""
        webhooks = list(self.data["webhooks"].values())
        
        # Apply filters
        if "status" in params:
            webhooks = [w for w in webhooks if w.get("status") == params["status"]]
            
        result = {
            "webhooks": webhooks,
            "pagination": {
                "totalItems": len(webhooks),
                "limit": len(webhooks),
                "offset": 0,
            },
        }
        return MockResponse(200, result)

    def _delete_webhook(
        self,
        headers: Dict[str, str],
        params: Dict[str, Any],
        data: Dict[str, Any],
        path_params: Dict[str, str],
    ) -> MockResponse:
        """Delete a webhook."""
        webhook_id = path_params["webhook_id"]
        
        if webhook_id not in self.data["webhooks"]:
            return self._create_error_response(
                404, f"Webhook not found: {webhook_id}", "NOT_FOUND"
            )
            
        # Delete webhook
        del self.data["webhooks"][webhook_id]
        return MockResponse(200, {"deleted": True})
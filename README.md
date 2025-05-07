# Paysafe Python SDK

A modern, Python 3.7+ compatible SDK for the Paysafe API. This SDK provides a simple, idiomatic interface for interacting with Paysafe's payment processing services.

[![PyPI version](https://badge.fury.io/py/paysafe.svg)](https://badge.fury.io/py/paysafe)
[![Python Versions](https://img.shields.io/pypi/pyversions/paysafe.svg)](https://pypi.org/project/paysafe/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Full Paysafe API support with an idiomatic Python interface
- Strong typing with comprehensive type hints
- Data validation through Pydantic
- Support for both synchronous and asynchronous API calls
- Detailed error handling with a comprehensive exception hierarchy
- Google-style docstrings for excellent IDE integration
- PEP 8 compliant with snake_case naming conventions
- Comprehensive test suite including unit and integration tests

## Installation

```bash
pip install paysafe
```

## Quick Start

### Client Initialization

```python
from paysafe import Client

# For sandbox testing
client = Client(api_key="your_api_key", environment="sandbox")

# For production
# client = Client(api_key="your_api_key", environment="production")
```

### Process a Payment

```python
from paysafe import Client
from paysafe.models.payment import Payment, CardPaymentMethod

# Initialize the client
client = Client(api_key="your_api_key", environment="sandbox")

# Create a payment method
payment_method = CardPaymentMethod(
    card_number="4111111111111111",
    card_expiry={"month": 12, "year": 25},
    card_holder_name="John Doe",
    card_cvv="123"
)

# Create a payment
payment = Payment(
    amount=1000,  # $10.00
    currency_code="USD",
    payment_method=payment_method,
    description="Test payment"
)

# Submit the payment
payment_resource = client.Payment
result = payment_resource.create(payment)

print(f"Payment created with ID: {result.id}")
print(f"Status: {result.status}")
```

### Managing Customers

```python
from paysafe import Client
from paysafe.models.customer import Customer

# Initialize the client
client = Client(api_key="your_api_key", environment="sandbox")

# Create a customer
customer = Customer(
    first_name="John",
    last_name="Doe",
    email="john.doe@example.com",
    phone="1234567890"
)

# Submit the customer
customer_resource = client.Customer
result = customer_resource.create(customer)

print(f"Customer created with ID: {result.id}")
```

### Using Async API

To use the asynchronous API, install with async support:

```bash
pip install "paysafe[async]"
```

Then use the async client and resources:

```python
import asyncio
from paysafe import create_async_client
from paysafe.api_resources.async_payment import AsyncPayment
from paysafe.models.payment import CardPaymentMethod, Payment

async def process_payment():
    # Initialize the async client
    client = create_async_client(api_key="your_api_key", environment="sandbox")
    
    # Create a payment method
    payment_method = CardPaymentMethod(
        card_number="4111111111111111",
        card_expiry={"month": 12, "year": 25},
        card_holder_name="John Doe",
        card_cvv="123"
    )
    
    # Create a payment
    payment = Payment(
        amount=1000,  # $10.00
        currency_code="USD",
        payment_method=payment_method,
        description="Async test payment"
    )
    
    # Submit the payment asynchronously
    payment_resource = AsyncPayment(client)
    result = await payment_resource.create(payment)
    
    print(f"Payment created with ID: {result.id}")
    print(f"Status: {result.status}")

# Run the async function
asyncio.run(process_payment())
```

### Handling Errors

```python
from paysafe import Client
from paysafe.exceptions import (
    PaysafeError,
    AuthenticationError,
    InvalidRequestError,
    APIError,
    NetworkError,
    RateLimitError
)

try:
    # Try some API operation
    client = Client(api_key="your_api_key", environment="sandbox")
    payment_resource = client.Payment
    payment = payment_resource.retrieve("nonexistent_id")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except InvalidRequestError as e:
    print(f"Invalid request: {e}")
except APIError as e:
    print(f"API error: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except PaysafeError as e:
    print(f"An error occurred: {e}")
```

## API Resources

The SDK provides the following API resources:

- **Payment**: Create, retrieve, and manage payments
- **Customer**: Create, retrieve, update, and delete customers
- **Card**: Manage cards for customers
- **Refund**: Process refunds for payments
- **Webhook**: Manage webhooks for event notifications

## Error Handling

The SDK provides a comprehensive exception hierarchy:

- `PaysafeError`: Base exception for all Paysafe-related errors
- `AuthenticationError`: Raised when authentication fails
- `InvalidRequestError`: Raised when request parameters are invalid
- `APIError`: Raised when the Paysafe API returns an error
- `NetworkError`: Raised when there are network-related issues
- `RateLimitError`: Raised when the API rate limit is exceeded
- `ValidationError`: Raised when data validation fails

## Documentation

For complete documentation, see the [Paysafe API Reference](https://developer.paysafe.com/en/api-reference/).

## Development

### Setup

1. Clone the repository
2. Install development dependencies:
   ```
   pip install -e ".[dev]"
   ```

### Running tests

```
pytest
```

### Running with coverage

```
pytest --cov=paysafe
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
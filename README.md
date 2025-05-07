# Paysafe Python SDK

A modern, type-safe Python client for the Paysafe API with comprehensive support for both synchronous and asynchronous operations.

[![PyPI version](https://img.shields.io/pypi/v/paysafe-sdk.svg)](https://pypi.org/project/paysafe-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/paysafe-sdk.svg)](https://pypi.org/project/paysafe-sdk/)
[![License](https://img.shields.io/pypi/l/paysafe-sdk.svg)](https://pypi.org/project/paysafe-sdk/)
[![Tests](https://github.com/paysafe/paysafe-sdk-python/workflows/Tests/badge.svg)](https://github.com/paysafe/paysafe-sdk-python/actions)

## Features

- 🔒 **Type Safety**: Comprehensive type annotations and Pydantic models for static type checking and IDE autocomplete
- ⚡ **Async Support**: Built-in asynchronous API client for high-performance applications using modern Python async/await syntax
- 🛡️ **Robust Error Handling**: Detailed and specific exception classes for proper error handling and debugging
- 📚 **Comprehensive Documentation**: Thorough documentation with examples for all API operations
- 🧪 **Extensive Test Coverage**: Unit tests and integration tests for all API resources
- 🐍 **Modern Python**: Requires Python 3.7+ and follows best practices for Python package development

## Installation

```bash
pip install paysafe-sdk
```

## Quick Start

### Initialize Client

```python
import paysafe
from paysafe.models.payment import Payment

# Synchronous client
client = paysafe.Client(
    api_key="your_api_key",
    environment="sandbox"  # Use 'production' for live environment
)

# Asynchronous client
async_client = paysafe.AsyncClient(
    api_key="your_api_key",
    environment="sandbox"
)
```

### Create a Payment

#### Synchronous

```python
payment = paysafe.Payment.create(
    client=client,
    payment_method="card",
    amount=1000,  # Amount in cents
    currency_code="USD",
    card={
        "card_number": "4111111111111111",
        "expiry_month": 12,
        "expiry_year": 2025,
        "cvv": "123"
    },
    merchant_reference_number="order-123",
    description="Test payment"
)

print(f"Payment ID: {payment.id}")
print(f"Status: {payment.status}")
```

#### Asynchronous

```python
import asyncio
import paysafe

async def create_payment():
    # Initialize the async client
    client = paysafe.AsyncClient(
        api_key="your_api_key",
        environment="sandbox"
    )

    # Create a payment asynchronously
    payment = await paysafe.AsyncPayment.create(
        client=client,
        payment_method="card",
        amount=1000,
        currency_code="USD",
        card={
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        },
        merchant_reference_number="order-123",
        description="Async test payment"
    )

    print(f"Payment ID: {payment.id}")
    print(f"Status: {payment.status}")

# Run the async function
asyncio.run(create_payment())
```

### Retrieve a Payment

```python
payment = paysafe.Payment.retrieve(
    client=client,
    payment_id="payment_id_here"
)

print(f"Payment amount: {payment.amount / 100} {payment.currency_code}")
print(f"Payment status: {payment.status}")
```

### List Payments

```python
from datetime import datetime, timedelta

# Get payments from the last 7 days
one_week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
today = datetime.now().strftime("%Y-%m-%d")

payments = paysafe.Payment.list(
    client=client,
    created_from=one_week_ago,
    created_to=today,
    status="COMPLETED",
    limit=10
)

# Print payment details
for payment in payments:
    print(f"Payment ID: {payment.id}")
    print(f"Amount: {payment.amount / 100} {payment.currency_code}")
    print(f"Status: {payment.status}")
    print("---")
```

### Error Handling

```python
from paysafe.exceptions import (
    AuthenticationError,
    InvalidRequestError,
    APIError,
    NetworkError,
    RateLimitError,
    PaysafeError
)

try:
    # Try to retrieve a non-existent payment
    payment = paysafe.Payment.retrieve(
        client=client,
        payment_id="non_existent_id"
    )
except AuthenticationError as e:
    print(f"Authentication error: {str(e)}")
except InvalidRequestError as e:
    print(f"Invalid request error: {str(e)}")
except APIError as e:
    print(f"API error: {str(e)}")
except NetworkError as e:
    print(f"Network error: {str(e)}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {str(e)}")
except PaysafeError as e:
    print(f"Other Paysafe error: {str(e)}")
```

## Customer Operations

### Create a Customer

```python
customer = paysafe.Customer.create(
    client=client,
    email="customer@example.com",
    first_name="John",
    last_name="Doe",
    billing_details={
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "country": "US",
        "zip": "12345",
        "phone": "5555555555"
    }
)

print(f"Customer ID: {customer.id}")
print(f"Email: {customer.email}")
```

### Update a Customer

```python
updated_customer = paysafe.Customer.update(
    client=client,
    customer_id="customer_id_here",
    email="new_email@example.com",
    phone="6665555555"
)

print(f"Updated customer: {updated_customer.first_name} {updated_customer.last_name}")
print(f"New email: {updated_customer.email}")
```

## Card Operations

### Save a Card for a Customer

```python
card = paysafe.Card.create(
    client=client,
    customer_id="customer_id_here",
    card_number="4111111111111111",
    expiry_month=12,
    expiry_year=2025,
    cvv="123",
    nickname="Primary Card"
)

print(f"Card ID: {card.id}")
print(f"Card type: {card.card_type}")
print(f"Last 4 digits: {card.last_four}")
```

## Development and Testing

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/paysafe/paysafe-sdk-python.git
   cd paysafe-sdk-python
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Running Tests

To run unit tests:
```bash
pytest
```

To run integration tests (requires API key):
```bash
export PAYSAFE_TEST_API_KEY="your_test_api_key"
pytest --integration
```

## Integration Tests

The integration tests require a valid Paysafe sandbox API key. These tests make real API calls to the Paysafe API, so they are skipped by default.

To run integration tests:

1. Set your Paysafe test API key as an environment variable:
   ```bash
   export PAYSAFE_TEST_API_KEY="your_test_api_key"
   ```

2. Run the tests with the integration flag:
   ```bash
   pytest --integration
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions about the SDK, please [open an issue](https://github.com/paysafe/paysafe-sdk-python/issues) on GitHub.
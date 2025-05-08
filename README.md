# Paysafe Python SDK

A modern, type-safe Python client for the Paysafe API with comprehensive support for both synchronous and asynchronous operations.

## Features

- 🔒 **Type Safety**: Comprehensive type annotations and Pydantic models for static type checking and IDE autocomplete
- ⚡ **Async Support**: Built-in asynchronous API client for high-performance applications using modern Python async/await syntax
- 🛡️ **Robust Error Handling**: Detailed and specific exception classes for proper error handling and debugging
- 🔐 **Credential Management**: Support for loading credentials from Postman-format JSON files or environment variables
- 🤖 **AI-Powered Agents**: Optional AI capabilities for transaction analysis, subscription management, and customer insights
- 🔄 **Intelligent Retry**: Configurable retry strategies with exponential backoff and jitter for improved reliability
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

# Synchronous client with direct API key
client = paysafe.Client(
    api_key="your_api_key",
    environment="sandbox"  # Use 'production' for live environment
)

# Asynchronous client with direct API key
async_client = paysafe.AsyncClient(
    api_key="your_api_key",
    environment="sandbox"
)

# Using a credentials file (Postman format)
client_with_credentials_file = paysafe.Client(
    credentials_file="path/to/paysafe_credentials.json",
    environment="sandbox"
)

# Using environment variable for credentials file path
# First, set the environment variable:
# export PAYSAFE_CREDENTIALS_FILE="path/to/paysafe_credentials.json"
client_with_env_var = paysafe.Client(environment="sandbox")
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
   git clone <github url> paysafe-sdk-python
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

## Credentials File Support

The SDK supports loading Paysafe API credentials from a JSON file in Postman environment format. This is useful for:

- Separating credentials from code
- Supporting environment-based configuration
- Easily switching between different accounts or environments

### Credentials File Format

The credentials file should be in Postman environment format:

```json
{
  "id": "paysafe-environment",
  "name": "Paysafe Environment",
  "values": [
    {
      "key": "public_key",
      "value": "your_public_key",
      "type": "default",
      "enabled": true
    },
    {
      "key": "private_key",
      "value": "your_private_key",
      "type": "default",
      "enabled": true
    },
    {
      "key": "account_id",
      "value": "your_account_id",
      "type": "default",
      "enabled": true
    }
  ],
  "_postman_variable_scope": "environment"
}
```

### Using a Credentials File

There are three ways to use credentials files:

1. **Direct path in constructor**:
   ```python
   client = paysafe.Client(
       credentials_file="path/to/paysafe_credentials.json",
       environment="sandbox"
   )
   ```

2. **Environment variable**:
   ```bash
   export PAYSAFE_CREDENTIALS_FILE="path/to/paysafe_credentials.json"
   ```
   ```python
   client = paysafe.Client(environment="sandbox")
   ```

3. **Load manually and extract API key**:
   ```python
   from paysafe.utils import load_credentials_from_file, get_api_key_from_credentials
   
   credentials = load_credentials_from_file("path/to/paysafe_credentials.json")
   api_key = get_api_key_from_credentials(credentials)
   
   client = paysafe.Client(api_key=api_key, environment="sandbox")
   ```

For a full example, see the [credentials_file_demo.py](examples/credentials_file_demo.py) file.

## Retry Mechanisms

The SDK includes robust retry mechanisms for handling transient failures and network issues. You can configure retry behavior at the global, client, and individual request levels.

### Retry Configuration

```python
from paysafe import Client, RetryStrategy, RetryCondition

# Configure a client with retry settings
client = Client(
    api_key="your_api_key",
    environment="sandbox",
    retry_config={
        "strategy": RetryStrategy.EXPONENTIAL_JITTER,  # Exponential backoff with jitter
        "max_retries": 3,                            # Maximum retry attempts
        "initial_delay": 0.5,                        # Initial delay in seconds
        "max_delay": 5.0,                            # Maximum delay in seconds
        "jitter_factor": 0.25,                       # Random jitter factor (0-1)
        "retry_conditions": [                        # Conditions to trigger retry
            RetryCondition.NETWORK_ERROR,            # Network connectivity issues
            RetryCondition.SERVER_ERROR,             # 5xx server errors
            RetryCondition.RATE_LIMIT_ERROR,         # Rate limit (429) responses
        ]
    }
)
```

### Retry Strategies

The SDK supports the following retry strategies:

- `RetryStrategy.NONE`: No retries will be performed
- `RetryStrategy.FIXED`: Fixed delay between retry attempts
- `RetryStrategy.EXPONENTIAL`: Exponential backoff (delay increases exponentially)
- `RetryStrategy.EXPONENTIAL_JITTER`: Exponential backoff with random jitter (recommended)

### Retry Conditions

You can specify which conditions should trigger a retry:

- `RetryCondition.NETWORK_ERROR`: Network connectivity issues
- `RetryCondition.SERVER_ERROR`: 5xx server errors
- `RetryCondition.RATE_LIMIT_ERROR`: Rate limit (429) responses
- `RetryCondition.TIMEOUT_ERROR`: Request timeouts
- `RetryCondition.IDEMPOTENT_OPERATION`: Only retry idempotent operations (GET, HEAD, OPTIONS)

### Request-Level Retry

You can also override retry settings for individual requests:

```python
# Override retry settings for a specific request
payment = paysafe.Payment.retrieve(
    client=client,
    payment_id="payment_id_here",
    retry_config={
        "strategy": RetryStrategy.EXPONENTIAL,
        "max_retries": 5,
        "initial_delay": 1.0
    }
)
```

### Async Retry Support

The retry mechanisms work identically with the AsyncClient:

```python
from paysafe import AsyncClient, RetryStrategy, RetryCondition

async_client = AsyncClient(
    api_key="your_api_key",
    environment="sandbox",
    retry_config={
        "strategy": RetryStrategy.EXPONENTIAL_JITTER,
        "max_retries": 3,
        "initial_delay": 0.5
    }
)

# Use the async client with retry capabilities
payment = await paysafe.AsyncPayment.retrieve(
    client=async_client,
    payment_id="payment_id_here"
)
```

## AI Capabilities

The SDK includes optional AI-powered capabilities via OpenAI's models. These features can enhance your payment integration with intelligent risk analysis, subscription optimization, and customer insights.

### Setting Up AI

To use AI features, you need an OpenAI API key:

```python
import paysafe
from paysafe.ai import PaymentAgent, SubscriptionAgent, CustomerAgent
from paysafe.ai.config import AIConfig

# Configure AI
ai_config = AIConfig(
    api_key="your_openai_api_key",  # Required for AI features
    model="gpt-4o",                 # Model to use (default: gpt-4o)
    temperature=0.2,                # Controls randomness (0-1)
    log_requests=True,              # Log AI requests
    log_responses=True              # Log AI responses
)

# Create AI agents
payment_agent = PaymentAgent(client=client, ai_config=ai_config)
subscription_agent = SubscriptionAgent(client=client, ai_config=ai_config)
customer_agent = CustomerAgent(client=client, ai_config=ai_config)
```

You can also use environment variables for the OpenAI API key:

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

```python
# AI config will automatically use the environment variable
ai_config = AIConfig()
```

### Using AI Agents

#### Payment Analysis

Analyze transaction risk and optimize payment processing:

```python
# Analyze transaction risk
payment_data = {
    "amount": 1000,
    "currency_code": "USD",
    "payment_method": "card",
    "country": "US"
}
risk_assessment = payment_agent.analyze_transaction_risk(payment_data)
print(f"Risk level: {risk_assessment['risk_level']}")
print(f"Risk score: {risk_assessment['risk_score']}")

# Optimize payment processing based on history
payment_history = [...]  # List of previous payments
optimization = payment_agent.suggest_payment_optimization(payment_history)
print(f"Suggested methods: {optimization['optimal_payment_methods']}")
```

#### Subscription Management

Predict churn risk and optimize subscription strategies:

```python
# Predict churn risk
churn_risk = subscription_agent.predict_churn_risk(
    customer_data, 
    subscription_history
)
print(f"Churn risk: {churn_risk['churn_risk_level']}")
print(f"Probability: {churn_risk['churn_probability']}%")

# Optimize renewal strategy
renewal_strategy = subscription_agent.optimize_renewal_strategy(
    subscription_data,
    payment_history
)
print(f"Optimal timing: {renewal_strategy['optimal_timing']}")
```

#### Customer Insights

Segment customers and analyze lifetime value:

```python
# Segment a customer
segmentation = customer_agent.segment_customer(
    customer_data,
    transaction_history
)
print(f"Customer segment: {segmentation['customer_segment']}")
print(f"Value tier: {segmentation['value_tier']}")

# Analyze lifetime value
lifetime_value = customer_agent.analyze_lifetime_value(
    customer_data,
    transaction_history,
    months_to_project=24
)
print(f"Current value: ${lifetime_value['current_value']}")
print(f"Projected value: ${lifetime_value['projected_value']}")
```

### Async AI Operations

The AI agents support asynchronous operations for long-running tasks:

```python
import asyncio
from paysafe.ai import SubscriptionAgent

subscription_agent = SubscriptionAgent(client=async_client, ai_config=ai_config)

async def manage_subscriptions():
    # Autonomous subscription lifecycle management
    lifecycle_plan = await subscription_agent.manage_subscription_lifecycle(
        customer_id="customer_123",
        subscription_id="subscription_456",
        days_to_monitor=90  # 3 months of monitoring
    )
    
    print("Subscription lifecycle plan created:")
    print(lifecycle_plan["final_management_plan"])

# Run the async function
asyncio.run(manage_subscriptions())
```

### AI Integration Testing

AI agents can be used in integration tests to enhance testing capabilities:

```python
import pytest
from paysafe.ai import PaymentAgent

def test_payment_risk_analysis(client, ai_config):
    payment_agent = PaymentAgent(client=client, ai_config=ai_config)
    
    # Test payment data
    payment_data = {...}
    
    # Run risk analysis
    risk_assessment = payment_agent.analyze_transaction_risk(payment_data)
    
    # Assert on the results
    assert "risk_level" in risk_assessment
    assert "risk_score" in risk_assessment
    assert isinstance(risk_assessment["risk_score"], (int, float))
    assert 0 <= risk_assessment["risk_score"] <= 100
```

For complete examples, see the [ai_agent_demo.py](examples/ai_agent_demo.py) and [ai_long_running_demo.py](examples/ai_long_running_demo.py) files.

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

You can also use a credentials file for integration tests:
```bash
export PAYSAFE_CREDENTIALS_FILE="path/to/paysafe_credentials.json"
pytest --integration
```

For AI-powered integration tests, set your OpenAI API key:
```bash
export OPENAI_API_KEY="your_openai_api_key"
pytest --integration
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions about the SDK, please [open an issue](https://github.com/paysafe/paysafe-sdk-python/issues) on GitHub.
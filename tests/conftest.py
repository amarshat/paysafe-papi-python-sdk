"""
Fixtures for testing the Paysafe SDK.
"""

import json
import os
import uuid
import tempfile
import logging
from datetime import datetime
from unittest import mock
from pathlib import Path

import pytest
from requests import Response

from paysafe import Client
from paysafe.models.customer import Customer, CustomerBillingDetails
from paysafe.models.payment import BankAccountPaymentMethod, CardPaymentMethod, Payment, PaymentStatus


# Skip integration tests by default unless the --integration flag is passed
def pytest_addoption(parser):
    """Add command-line options to pytest."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests that make real API calls",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration tests."""
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="Need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


@pytest.fixture
def api_key():
    """Return a mock API key for testing."""
    return "test_api_key_" + str(uuid.uuid4()).replace("-", "")


@pytest.fixture
def client():
    """Mock Paysafe API client."""
    client = mock.MagicMock(spec=Client)
    client.session = mock.MagicMock()
    return client


@pytest.fixture
def successful_response():
    """Create a successful API response with provided data."""
    def _create_response(data):
        response = mock.MagicMock(spec=Response)
        response.status_code = 200
        response.ok = True
        response.json.return_value = data
        response.text = json.dumps(data)
        response.content = json.dumps(data).encode("utf-8")
        return response
    return _create_response


@pytest.fixture
def error_response():
    """Create an error API response with provided status code and error message."""
    def _create_response(status_code, error_message, error_code="ERROR"):
        response = mock.MagicMock(spec=Response)
        response.status_code = status_code
        response.ok = False
        error_data = {
            "error": {
                "code": error_code,
                "message": error_message,
                "details": []
            }
        }
        response.json.return_value = error_data
        response.text = json.dumps(error_data)
        response.content = json.dumps(error_data).encode("utf-8")
        return response
    return _create_response


@pytest.fixture
def sample_customer():
    """Sample customer data for testing."""
    return Customer(
        id="cust_" + str(uuid.uuid4()).replace("-", ""),
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890",
        billing_details=CustomerBillingDetails(
            street="123 Main St",
            city="Anytown",
            state="CA",
            country="US",
            zip="12345"
        )
    )


@pytest.fixture
def sample_payment():
    """Sample payment data for testing."""
    return Payment(
        id="pay_" + str(uuid.uuid4()).replace("-", ""),
        amount=1000,
        currency_code="USD",
        description="Test payment",
        customer_id="cust_" + str(uuid.uuid4()).replace("-", ""),
        status=PaymentStatus.COMPLETED,
        payment_method=CardPaymentMethod(
            card_number="4111111111111111", 
            card_expiry={"month": 12, "year": 25},
            card_holder_name="John Doe",
            card_cvv="123"
        ),
        created_at=datetime.now().isoformat()
    )


@pytest.fixture
def sample_bank_payment():
    """Sample bank account payment data for testing."""
    return Payment(
        id="pay_" + str(uuid.uuid4()).replace("-", ""),
        amount=2000,
        currency_code="USD",
        description="Test bank payment",
        customer_id="cust_" + str(uuid.uuid4()).replace("-", ""),
        status=PaymentStatus.PENDING,
        payment_method=BankAccountPaymentMethod(
            account_number="1234567890",
            routing_number="123456789",
            account_holder_name="John Doe",
            account_type="checking"
        ),
        created_at=datetime.now().isoformat()
    )


@pytest.fixture
def mock_payment_response(successful_response, sample_payment):
    """Mock payment API response."""
    # Convert the Pydantic model to a dict
    payment_dict = sample_payment.model_dump(exclude_none=True)
    # Convert datetime to string if it's not already
    if isinstance(payment_dict.get("created_at"), datetime):
        payment_dict["created_at"] = payment_dict["created_at"].isoformat()
    return successful_response(payment_dict)


@pytest.fixture
def mock_payment_list_response(successful_response):
    """Mock payment list API response."""
    payments = [
        {
            "id": "pay_" + str(uuid.uuid4()).replace("-", ""),
            "amount": 1000,
            "currency_code": "USD",
            "description": "Test payment 1",
            "customer_id": "cust_" + str(uuid.uuid4()).replace("-", ""),
            "status": "completed",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "pay_" + str(uuid.uuid4()).replace("-", ""),
            "amount": 2000,
            "currency_code": "EUR",
            "description": "Test payment 2",
            "customer_id": "cust_" + str(uuid.uuid4()).replace("-", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    return successful_response({
        "payments": payments,
        "pagination": {
            "has_more": False,
            "total_count": 2
        }
    })


@pytest.fixture
def mock_customer_response(successful_response, sample_customer):
    """Mock customer API response."""
    customer_dict = sample_customer.model_dump(exclude_none=True)
    return successful_response(customer_dict)


@pytest.fixture
def mock_customer_list_response(successful_response):
    """Mock customer list API response."""
    customers = [
        {
            "id": "cust_" + str(uuid.uuid4()).replace("-", ""),
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "cust_" + str(uuid.uuid4()).replace("-", ""),
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "0987654321",
            "created_at": datetime.now().isoformat()
        }
    ]
    
    return successful_response({
        "customers": customers,
        "pagination": {
            "has_more": False,
            "total_count": 2
        }
    })


@pytest.fixture
def mock_customer_delete_response(successful_response):
    """Mock customer delete API response."""
    return successful_response({"deleted": True})


@pytest.fixture
def mock_response():
    """Generic mock response for API client tests."""
    response = mock.MagicMock(spec=Response)
    response.status_code = 200
    response.ok = True
    response.json.return_value = {"success": True}
    response.text = json.dumps({"success": True})
    response.content = json.dumps({"success": True}).encode("utf-8")
    return response


@pytest.fixture
def integration_api_key():
    """Return a real API key for integration tests."""
    api_key = os.environ.get("PAYSAFE_TEST_API_KEY")
    if not api_key:
        pytest.skip("PAYSAFE_TEST_API_KEY environment variable not set")
    return api_key


@pytest.fixture
def integration_client(integration_api_key):
    """Create a real client for integration tests."""
    return Client(api_key=integration_api_key, environment="sandbox")


@pytest.fixture(scope="session")
def payload_log_file(request):
    """Create a log file in a persistent directory to record API request/response payloads."""
    # Get the log file path from pytest config
    log_file = getattr(request.config, "payload_log_file", None)
    
    if not log_file:
        # If log file wasn't set in pytest_configure, create a fallback
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"api_payloads_fallback_{timestamp}.log")
    
    # Set up logging
    payload_logger = logging.getLogger("paysafe.api.payloads")
    payload_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    for handler in payload_logger.handlers[:]:
        payload_logger.removeHandler(handler)
    
    # Create file handler
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Add handler to logger
    payload_logger.addHandler(fh)
    
    # Log file info
    payload_logger.info(f"API Payload Log File: {log_file}")
    payload_logger.info("="*80)
    
    # Print log file location to console
    print(f"\n\n🔍 API PAYLOAD LOG: {log_file}\n")
    
    # Return the log file path
    return log_file


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Add a section at the end of the pytest output to display the log file location.
    """
    payload_log = getattr(config, "payload_log_file", None)
    if payload_log:
        terminalreporter.write_sep("=", "API Payload Log Information")
        terminalreporter.write_line(f"📋 API payloads are logged to: {payload_log}")
        terminalreporter.write_line(f"Use 'cat {payload_log}' to view the contents")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test that makes real API calls"
    )
    
    # Create a persistent log directory in the project root
    try:
        # Create a logs directory in the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"api_payloads_{timestamp}.log")
        
        # Store the log file path in the config for later use
        config.payload_log_file = log_file
        
        print(f"\n📋 API payloads will be logged to: {log_file}\n")
    except Exception as e:
        print(f"⚠️ Warning: Could not set up payload log file: {e}")
        config.payload_log_file = None
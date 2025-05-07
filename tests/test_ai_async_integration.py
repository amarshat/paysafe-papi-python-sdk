"""
Async integration tests for AI agents.

These tests demonstrate the use of async AI agents in real integration testing scenarios.
They require both a Paysafe API key and an OpenAI API key to run.
"""

import os
import json
import pytest
import pytest_asyncio
from datetime import datetime, timedelta

import paysafe
from paysafe.ai import PaymentAgent, SubscriptionAgent, CustomerAgent
from paysafe.ai.config import AIConfig


# Skip these tests if not running integration tests or if OpenAI API key is not available
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.skipif(
        os.environ.get("OPENAI_API_KEY") is None,
        reason="OPENAI_API_KEY environment variable is not set"
    )
]


@pytest_asyncio.fixture
async def async_client():
    """Create an async client for testing."""
    api_key = os.environ.get("PAYSAFE_TEST_API_KEY")
    if not api_key and os.environ.get("PAYSAFE_CREDENTIALS_FILE"):
        # Load from credentials file if available
        from paysafe.utils import load_credentials_from_file, get_api_key_from_credentials
        credentials = load_credentials_from_file(os.environ.get("PAYSAFE_CREDENTIALS_FILE"))
        api_key = get_api_key_from_credentials(credentials)
    
    if not api_key:
        pytest.skip("No API key available for integration tests")
    
    return paysafe.AsyncClient(
        api_key=api_key,
        environment="sandbox"
    )


@pytest.fixture
def ai_config():
    """Create an AI configuration for testing."""
    return AIConfig(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        temperature=0.2,
    )


@pytest_asyncio.fixture
async def payment_agent(async_client, ai_config):
    """Create a payment agent for testing."""
    return PaymentAgent(client=async_client, ai_config=ai_config)


@pytest_asyncio.fixture
async def subscription_agent(async_client, ai_config):
    """Create a subscription agent for testing."""
    return SubscriptionAgent(client=async_client, ai_config=ai_config)


@pytest_asyncio.fixture
async def customer_agent(async_client, ai_config):
    """Create a customer agent for testing."""
    return CustomerAgent(client=async_client, ai_config=ai_config)


@pytest.fixture
def sample_payment_ids():
    """Create sample payment IDs for testing."""
    return [f"payment_{i}" for i in range(5)]


@pytest.fixture
def sample_customer_id():
    """Create a sample customer ID for testing."""
    return "test_customer_123"


@pytest.fixture
def sample_subscription_id():
    """Create a sample subscription ID for testing."""
    return "test_subscription_456"


class TestAsyncPaymentAgent:
    """Tests for the async PaymentAgent methods."""
    
    async def test_monitor_payment_patterns(self, payment_agent, sample_payment_ids):
        """Test monitoring payment patterns."""
        # Verify AI is available
        assert payment_agent.is_ai_available, "AI features should be available"
        
        # Monitor payment patterns
        patterns = await payment_agent.monitor_payment_patterns(
            payment_ids=sample_payment_ids,
            lookback_days=30
        )
        
        # Verify the response structure
        assert isinstance(patterns, dict)
        assert "identified_patterns" in patterns or "patterns" in patterns
        assert "anomalies" in patterns or "outliers" in patterns
        assert "fraud_indicators" in patterns or "risk_indicators" in patterns
        assert "recommendations" in patterns


class TestAsyncSubscriptionAgent:
    """Tests for the async SubscriptionAgent methods."""
    
    async def test_manage_subscription_lifecycle(self, subscription_agent, sample_customer_id, sample_subscription_id):
        """Test managing subscription lifecycle."""
        # Verify AI is available
        assert subscription_agent.is_ai_available, "AI features should be available"
        
        # Manage subscription lifecycle
        lifecycle_plan = await subscription_agent.manage_subscription_lifecycle(
            customer_id=sample_customer_id,
            subscription_id=sample_subscription_id,
            days_to_monitor=30  # Using a short period for testing
        )
        
        # Verify the response structure
        assert isinstance(lifecycle_plan, dict)
        assert "customer_id" in lifecycle_plan
        assert "subscription_id" in lifecycle_plan
        assert "management_duration_days" in lifecycle_plan
        assert "phase_plans" in lifecycle_plan
        assert "final_management_plan" in lifecycle_plan
        
        # Verify the phase plans
        assert isinstance(lifecycle_plan["phase_plans"], dict)
        assert len(lifecycle_plan["phase_plans"]) > 0
        
        # Verify the final management plan
        assert isinstance(lifecycle_plan["final_management_plan"], dict)


class TestAsyncCustomerAgent:
    """Tests for the async CustomerAgent methods."""
    
    async def test_build_customer_insights(self, customer_agent, sample_customer_id):
        """Test building customer insights."""
        # Verify AI is available
        assert customer_agent.is_ai_available, "AI features should be available"
        
        # Build customer insights
        insights = await customer_agent.build_customer_insights(
            customer_id=sample_customer_id
        )
        
        # Verify the response structure
        assert isinstance(insights, dict)
        assert "customer_id" in insights
        assert "category_insights" in insights
        assert "comprehensive_profile" in insights
        
        # Verify the category insights
        assert isinstance(insights["category_insights"], dict)
        assert len(insights["category_insights"]) > 0
        
        # Verify the comprehensive profile
        assert isinstance(insights["comprehensive_profile"], dict)
"""
Integration tests for AI agents.

These tests demonstrate the use of AI agents in real integration testing scenarios.
They require both a Paysafe API key and an OpenAI API key to run.
"""

import os
import json
import pytest
from datetime import datetime, timedelta

import paysafe
from paysafe.ai import PaymentAgent, SubscriptionAgent, CustomerAgent
from paysafe.ai.config import AIConfig


# Skip these tests if not running integration tests or if OpenAI API key is not available
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("OPENAI_API_KEY") is None,
        reason="OPENAI_API_KEY environment variable is not set"
    )
]


@pytest.fixture
def ai_config():
    """Create an AI configuration for testing."""
    return AIConfig(
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        temperature=0.2,
    )


@pytest.fixture
def payment_agent(client, ai_config):
    """Create a payment agent for testing."""
    return PaymentAgent(client=client, ai_config=ai_config)


@pytest.fixture
def subscription_agent(client, ai_config):
    """Create a subscription agent for testing."""
    return SubscriptionAgent(client=client, ai_config=ai_config)


@pytest.fixture
def customer_agent(client, ai_config):
    """Create a customer agent for testing."""
    return CustomerAgent(client=client, ai_config=ai_config)


@pytest.fixture
def sample_payment_data():
    """Create sample payment data for testing."""
    return {
        "amount": 1000,
        "currency_code": "USD",
        "payment_method": "card",
        "card": {
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        },
        "country": "US",
        "time": datetime.now().isoformat()
    }


@pytest.fixture
def sample_subscription_data():
    """Create sample subscription data for testing."""
    return {
        "id": "test_subscription",
        "customer_id": "test_customer",
        "status": "active",
        "start_date": (datetime.now() - timedelta(days=90)).isoformat(),
        "renewal_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "plan": "premium",
        "amount": 1999,
        "currency": "USD",
        "frequency": "monthly"
    }


@pytest.fixture
def sample_payment_history():
    """Create sample payment history for testing."""
    return [
        {
            "id": f"payment_{i}",
            "customer_id": "test_customer",
            "amount": 1999,
            "currency": "USD",
            "status": "completed",
            "date": (datetime.now() - timedelta(days=(i+1)*30)).isoformat(),
            "payment_method": "card"
        }
        for i in range(3)
    ]


@pytest.fixture
def sample_customer_data():
    """Create sample customer data for testing."""
    return {
        "id": "test_customer",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "created_at": (datetime.now() - timedelta(days=120)).isoformat(),
        "country": "US",
        "state": "CA"
    }


class TestPaymentAgent:
    """Tests for the PaymentAgent class."""
    
    def test_analyze_transaction_risk(self, payment_agent, sample_payment_data):
        """Test analyzing transaction risk."""
        # Verify AI is available
        assert payment_agent.is_ai_available, "AI features should be available"
        
        # Analyze the transaction risk
        risk_assessment = payment_agent.analyze_transaction_risk(sample_payment_data)
        
        # Verify the response structure
        assert isinstance(risk_assessment, dict)
        assert "risk_level" in risk_assessment
        assert "risk_score" in risk_assessment
        assert "risk_factors" in risk_assessment
        assert "recommendations" in risk_assessment
    
    def test_suggest_payment_optimization(self, payment_agent, sample_payment_history):
        """Test suggesting payment optimization."""
        # Verify AI is available
        assert payment_agent.is_ai_available, "AI features should be available"
        
        # Get payment optimization suggestions
        optimization = payment_agent.suggest_payment_optimization(sample_payment_history)
        
        # Verify the response structure
        assert isinstance(optimization, dict)
        assert any(key in optimization for key in [
            "optimal_payment_methods", 
            "routing_strategies", 
            "cost_savings",
            "conversion_improvements",
            "recurring_opportunities"
        ])


class TestSubscriptionAgent:
    """Tests for the SubscriptionAgent class."""
    
    def test_predict_churn_risk(self, subscription_agent, sample_customer_data, sample_payment_history):
        """Test predicting churn risk."""
        # Verify AI is available
        assert subscription_agent.is_ai_available, "AI features should be available"
        
        # Predict churn risk
        churn_risk = subscription_agent.predict_churn_risk(
            sample_customer_data,
            sample_payment_history
        )
        
        # Verify the response structure
        assert isinstance(churn_risk, dict)
        assert "churn_risk_level" in churn_risk
        assert "churn_probability" in churn_risk
        assert "risk_factors" in churn_risk
        assert "retention_recommendations" in churn_risk
    
    def test_optimize_renewal_strategy(self, subscription_agent, sample_subscription_data, sample_payment_history):
        """Test optimizing renewal strategy."""
        # Verify AI is available
        assert subscription_agent.is_ai_available, "AI features should be available"
        
        # Optimize renewal strategy
        renewal_strategy = subscription_agent.optimize_renewal_strategy(
            sample_subscription_data,
            sample_payment_history
        )
        
        # Verify the response structure
        assert isinstance(renewal_strategy, dict)
        assert any(key in renewal_strategy for key in [
            "optimal_timing", 
            "preferred_payment_method", 
            "pricing_strategy",
            "communication_plan",
            "recovery_strategy"
        ])


class TestCustomerAgent:
    """Tests for the CustomerAgent class."""
    
    def test_segment_customer(self, customer_agent, sample_customer_data, sample_payment_history):
        """Test customer segmentation."""
        # Verify AI is available
        assert customer_agent.is_ai_available, "AI features should be available"
        
        # Segment the customer
        segmentation = customer_agent.segment_customer(
            sample_customer_data,
            sample_payment_history
        )
        
        # Verify the response structure
        assert isinstance(segmentation, dict)
        assert "customer_segment" in segmentation
        assert "value_tier" in segmentation
        assert "behavioral_patterns" in segmentation
        assert "preferred_payment_methods" in segmentation
    
    def test_analyze_lifetime_value(self, customer_agent, sample_customer_data, sample_payment_history):
        """Test analyzing customer lifetime value."""
        # Verify AI is available
        assert customer_agent.is_ai_available, "AI features should be available"
        
        # Analyze lifetime value
        lifetime_value = customer_agent.analyze_lifetime_value(
            sample_customer_data,
            sample_payment_history,
            months_to_project=24
        )
        
        # Verify the response structure
        assert isinstance(lifetime_value, dict)
        assert "current_value" in lifetime_value
        assert "projected_value" in lifetime_value
        assert "monthly_projection" in lifetime_value
        assert "key_factors" in lifetime_value
        assert "strategies" in lifetime_value
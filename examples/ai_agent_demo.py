"""
Demonstrate the use of AI agents in the Paysafe SDK.

This example shows how to use the AI-powered agents to analyze payments,
optimize subscription strategies, and generate customer insights.
"""

import os
import json
from datetime import datetime, timedelta

import paysafe
from paysafe.ai import PaymentAgent, SubscriptionAgent, CustomerAgent
from paysafe.ai.config import AIConfig

# Load environment variables for credentials
api_key = os.environ.get("PAYSAFE_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Check if OpenAI API key is available
if not openai_api_key:
    print(
        "OPENAI_API_KEY environment variable is not set. "
        "AI features will be disabled. "
        "Set this variable to use AI-powered features."
    )

# Initialize Paysafe client
client = paysafe.Client(
    api_key=api_key,
    environment="sandbox"  # Use 'production' for live environment
)

# Configure AI
ai_config = AIConfig(
    api_key=openai_api_key,
    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    temperature=0.2,
    log_requests=True,
    log_responses=True,
)

# Create AI agents
payment_agent = PaymentAgent(client=client, ai_config=ai_config)
subscription_agent = SubscriptionAgent(client=client, ai_config=ai_config)
customer_agent = CustomerAgent(client=client, ai_config=ai_config)

# Check if AI is available
print(f"AI available: {payment_agent.is_ai_available}")

# Only proceed with AI operations if API key is available
if payment_agent.is_ai_available:
    # Example 1: Analyze transaction risk
    payment_data = {
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
    
    try:
        risk_assessment = payment_agent.analyze_transaction_risk(payment_data)
        print("\n=== Transaction Risk Assessment ===")
        print(json.dumps(risk_assessment, indent=2))
    except Exception as e:
        print(f"Error in transaction risk analysis: {e}")
    
    # Example 2: Optimize renewal strategy
    subscription_data = {
        "id": "subscription_123",
        "customer_id": "customer_456",
        "status": "active",
        "start_date": (datetime.now() - timedelta(days=90)).isoformat(),
        "renewal_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "plan": "premium",
        "amount": 1999,
        "currency": "USD",
        "frequency": "monthly"
    }
    
    payment_history = [
        {
            "id": "payment_001",
            "customer_id": "customer_456",
            "amount": 1999,
            "currency": "USD",
            "status": "completed",
            "date": (datetime.now() - timedelta(days=90)).isoformat(),
            "payment_method": "card"
        },
        {
            "id": "payment_002",
            "customer_id": "customer_456",
            "amount": 1999,
            "currency": "USD",
            "status": "completed",
            "date": (datetime.now() - timedelta(days=60)).isoformat(),
            "payment_method": "card"
        },
        {
            "id": "payment_003",
            "customer_id": "customer_456",
            "amount": 1999,
            "currency": "USD",
            "status": "completed",
            "date": (datetime.now() - timedelta(days=30)).isoformat(),
            "payment_method": "card"
        }
    ]
    
    try:
        renewal_strategy = subscription_agent.optimize_renewal_strategy(
            subscription_data,
            payment_history
        )
        print("\n=== Subscription Renewal Strategy ===")
        print(json.dumps(renewal_strategy, indent=2))
    except Exception as e:
        print(f"Error in renewal strategy optimization: {e}")
    
    # Example 3: Customer segmentation
    customer_data = {
        "id": "customer_456",
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "created_at": (datetime.now() - timedelta(days=120)).isoformat(),
        "country": "US",
        "state": "CA"
    }
    
    try:
        segmentation = customer_agent.segment_customer(
            customer_data,
            payment_history  # Reusing payment history from above
        )
        print("\n=== Customer Segmentation ===")
        print(json.dumps(segmentation, indent=2))
    except Exception as e:
        print(f"Error in customer segmentation: {e}")
else:
    print("\nAI features are disabled. Set the OPENAI_API_KEY environment variable to enable them.")
    print("Example usage (bash):")
    print("export OPENAI_API_KEY=your_openai_api_key")
    print("export PAYSAFE_API_KEY=your_paysafe_api_key")
    print("python examples/ai_agent_demo.py")
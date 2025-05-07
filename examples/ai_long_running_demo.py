"""
Demonstrate the use of AI agents for autonomous long-running operations.

This example shows how to use the AI-powered agents to autonomously manage
subscription lifecycles and monitor payment patterns over time.
"""

import os
import json
import asyncio
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

# Initialize Paysafe async client
async_client = paysafe.AsyncClient(
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

# Create AI agents with the async client
payment_agent = PaymentAgent(client=async_client, ai_config=ai_config)
subscription_agent = SubscriptionAgent(client=async_client, ai_config=ai_config)
customer_agent = CustomerAgent(client=async_client, ai_config=ai_config)


async def simulate_payment_monitoring():
    """Simulate monitoring payment patterns for anomalies."""
    # In a real scenario, these would be actual payment IDs from your system
    payment_ids = [
        "payment_001", 
        "payment_002", 
        "payment_003",
        "payment_004", 
        "payment_005"
    ]
    
    print("\n=== Monitoring Payment Patterns ===")
    print(f"Monitoring {len(payment_ids)} payments for patterns and anomalies...")
    
    try:
        # This is a long-running operation that would typically monitor payments over time
        # For demonstration purposes, we're using simulated data
        patterns = await payment_agent.monitor_payment_patterns(
            payment_ids=payment_ids,
            lookback_days=30
        )
        print("\nPayment Pattern Analysis Results:")
        print(json.dumps(patterns, indent=2))
    except Exception as e:
        if isinstance(e, ValueError) and "AI features are not available" in str(e):
            print("AI features are not available. Set OPENAI_API_KEY to enable them.")
        else:
            print(f"Error in payment pattern monitoring: {e}")


async def simulate_subscription_lifecycle_management():
    """Simulate autonomous subscription lifecycle management."""
    # In a real scenario, these would be actual customer and subscription IDs
    customer_id = "customer_abc"
    subscription_id = "subscription_xyz"
    
    print("\n=== Subscription Lifecycle Management ===")
    print(f"Managing subscription {subscription_id} for customer {customer_id}...")
    
    try:
        # This is a long-running operation that would typically manage a subscription over months
        # For demonstration purposes, we're using simulated data with a short timeframe
        lifecycle_plan = await subscription_agent.manage_subscription_lifecycle(
            customer_id=customer_id,
            subscription_id=subscription_id,
            days_to_monitor=90  # 3 months of monitoring
        )
        print("\nSubscription Lifecycle Management Plan:")
        print(json.dumps(lifecycle_plan["final_management_plan"], indent=2))
    except Exception as e:
        if isinstance(e, ValueError) and "AI features are not available" in str(e):
            print("AI features are not available. Set OPENAI_API_KEY to enable them.")
        else:
            print(f"Error in subscription lifecycle management: {e}")


async def simulate_customer_insights():
    """Simulate building comprehensive customer insights."""
    # In a real scenario, this would be an actual customer ID
    customer_id = "customer_abc"
    
    print("\n=== Building Customer Insights ===")
    print(f"Analyzing customer {customer_id} for comprehensive insights...")
    
    try:
        # This is a complex operation that gathers and analyzes customer data
        # For demonstration purposes, we're using simulated data
        insights = await customer_agent.build_customer_insights(
            customer_id=customer_id
        )
        print("\nComprehensive Customer Profile:")
        print(json.dumps(insights["comprehensive_profile"], indent=2))
    except Exception as e:
        if isinstance(e, ValueError) and "AI features are not available" in str(e):
            print("AI features are not available. Set OPENAI_API_KEY to enable them.")
        else:
            print(f"Error in building customer insights: {e}")


async def main():
    """Run all simulations in sequence."""
    # Check if AI is available
    if payment_agent.is_ai_available:
        print("AI features are enabled.")
        
        # Run the simulations
        await simulate_payment_monitoring()
        await simulate_subscription_lifecycle_management()
        await simulate_customer_insights()
        
        print("\nAll simulations completed.")
    else:
        print("\nAI features are disabled. Set the OPENAI_API_KEY environment variable to enable them.")
        print("Example usage (bash):")
        print("export OPENAI_API_KEY=your_openai_api_key")
        print("export PAYSAFE_API_KEY=your_paysafe_api_key")
        print("python examples/ai_long_running_demo.py")


if __name__ == "__main__":
    asyncio.run(main())
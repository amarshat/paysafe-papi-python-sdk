"""
Demonstrate how to use AI agents in integration testing.

This example shows how to use AI agents to enhance your integration testing
by providing intelligent analysis and decision-making capabilities.
"""

import os
import json
import logging
from datetime import datetime, timedelta

import paysafe
from paysafe.ai import PaymentAgent, SubscriptionAgent, CustomerAgent
from paysafe.ai.config import AIConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables for credentials
paysafe_api_key = os.environ.get("PAYSAFE_TEST_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

# Check if API keys are available
if not paysafe_api_key:
    logger.warning(
        "PAYSAFE_TEST_API_KEY environment variable is not set. "
        "This example requires a valid Paysafe API key to run."
    )

if not openai_api_key:
    logger.warning(
        "OPENAI_API_KEY environment variable is not set. "
        "AI features will be disabled. "
        "Set this variable to use AI-powered features."
    )


def run_payment_integration_test():
    """Run an integration test for payment processing with AI analysis."""
    
    # Skip if no API key is available
    if not paysafe_api_key:
        logger.error("Skipping test: No Paysafe API key available")
        return
    
    # Initialize Paysafe client
    client = paysafe.Client(
        api_key=paysafe_api_key,
        environment="sandbox"
    )
    
    # Configure AI
    ai_config = AIConfig(api_key=openai_api_key)
    
    # Create AI agent
    payment_agent = PaymentAgent(client=client, ai_config=ai_config)
    
    # Check if AI is available (requires OpenAI API key)
    if not payment_agent.is_ai_available:
        logger.warning("AI features are not available. Skipping AI analysis.")
    
    # Test data for creating a payment
    payment_data = {
        "payment_method": "card",
        "amount": 1000,  # $10.00
        "currency_code": "USD",
        "card": {
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": datetime.now().year + 1,
            "cvv": "123"
        },
        "merchant_reference_number": f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "description": "Integration test payment"
    }
    
    try:
        # Create payment
        logger.info("Creating test payment...")
        payment = paysafe.Payment.create(
            client=client,
            **payment_data
        )
        
        logger.info(f"Payment created successfully with ID: {payment.id}")
        logger.info(f"Status: {payment.status}")
        
        # Perform AI analysis if available
        if payment_agent.is_ai_available:
            # Add additional data for AI analysis
            analysis_data = {
                **payment_data,
                "id": payment.id,
                "status": payment.status,
                "time": datetime.now().isoformat(),
                "country": "US",
            }
            
            logger.info("Performing AI risk analysis on the payment...")
            risk_assessment = payment_agent.analyze_transaction_risk(analysis_data)
            
            logger.info("Risk Assessment Results:")
            logger.info(f"Risk Level: {risk_assessment.get('risk_level')}")
            logger.info(f"Risk Score: {risk_assessment.get('risk_score')}")
            
            # Log risk factors
            if 'risk_factors' in risk_assessment:
                logger.info("Risk Factors:")
                for factor in risk_assessment['risk_factors']:
                    logger.info(f"- {factor}")
            
            # Log recommendations
            if 'recommendations' in risk_assessment:
                logger.info("Recommendations:")
                for rec in risk_assessment['recommendations']:
                    logger.info(f"- {rec}")
            
            # Create a test assertion based on the risk assessment
            assert 'risk_level' in risk_assessment, "Risk level should be present in assessment"
            assert 'risk_score' in risk_assessment, "Risk score should be present in assessment"
            
            # Verify risk score is a number between 0-100
            if isinstance(risk_assessment.get('risk_score'), (int, float)):
                assert 0 <= risk_assessment.get('risk_score') <= 100, "Risk score should be between 0 and 100"
        
        # Create assertions about the payment
        assert payment.id is not None, "Payment ID should not be None"
        assert payment.status is not None, "Payment status should not be None"
        assert payment.amount == payment_data['amount'], "Payment amount should match the request"
        assert payment.currency_code == payment_data['currency_code'], "Currency should match the request"
        
        logger.info("Integration test passed successfully!")
        
        return payment
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise


def run_payment_optimization_test():
    """Run an integration test for payment optimization with AI."""
    
    # Skip if no API key is available
    if not paysafe_api_key:
        logger.error("Skipping test: No Paysafe API key available")
        return
    
    # Initialize Paysafe client
    client = paysafe.Client(
        api_key=paysafe_api_key,
        environment="sandbox"
    )
    
    # Configure AI
    ai_config = AIConfig(api_key=openai_api_key)
    
    # Create AI agent
    payment_agent = PaymentAgent(client=client, ai_config=ai_config)
    
    # Check if AI is available (requires OpenAI API key)
    if not payment_agent.is_ai_available:
        logger.warning("AI features are not available. Skipping AI analysis.")
        return
    
    # Simulate a payment history
    payment_history = [
        {
            "id": f"payment_{i}",
            "customer_id": "customer_test",
            "amount": 1000 + (i * 100),
            "currency_code": "USD",
            "payment_method": ["card", "bank_transfer"][i % 2],
            "status": ["completed", "completed", "failed", "completed", "completed"][i % 5],
            "created_at": (datetime.now() - timedelta(days=i*7)).isoformat(),
            "country": "US"
        }
        for i in range(10)
    ]
    
    try:
        logger.info("Running payment optimization analysis...")
        
        # Get optimization suggestions
        optimization = payment_agent.suggest_payment_optimization(payment_history)
        
        logger.info("Payment Optimization Results:")
        
        # Log optimal payment methods
        if 'optimal_payment_methods' in optimization:
            logger.info("Optimal Payment Methods:")
            for method in optimization['optimal_payment_methods']:
                logger.info(f"- {method}")
        
        # Log other key optimization areas
        for key in ['routing_strategies', 'cost_savings', 'conversion_improvements']:
            if key in optimization:
                logger.info(f"\n{key.replace('_', ' ').title()}:")
                if isinstance(optimization[key], list):
                    for item in optimization[key]:
                        logger.info(f"- {item}")
                else:
                    logger.info(f"- {optimization[key]}")
        
        # Create assertions based on the optimization results
        assert isinstance(optimization, dict), "Optimization result should be a dictionary"
        assert len(optimization) > 0, "Optimization result should not be empty"
        
        # Check for at least one key area
        assert any(key in optimization for key in [
            'optimal_payment_methods', 
            'routing_strategies', 
            'cost_savings',
            'conversion_improvements'
        ]), "Optimization should include at least one key area"
        
        logger.info("Payment optimization test passed successfully!")
        
        return optimization
        
    except Exception as e:
        logger.error(f"Payment optimization test failed: {e}")
        raise


if __name__ == "__main__":
    print("\n===== Running Integration Tests with AI Analysis =====\n")
    
    payment = None
    try:
        # Run payment integration test
        payment = run_payment_integration_test()
        
        # Run payment optimization test if the first test passed
        if payment:
            run_payment_optimization_test()
            
    except Exception as e:
        print(f"\nIntegration tests failed: {e}")
    
    print("\n===== Integration Tests Complete =====")
    
    if not paysafe_api_key or not openai_api_key:
        print("\nTo run this demo with full functionality, set these environment variables:")
        if not paysafe_api_key:
            print("export PAYSAFE_TEST_API_KEY=your_paysafe_api_key")
        if not openai_api_key:
            print("export OPENAI_API_KEY=your_openai_api_key")
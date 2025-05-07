"""
Specialized AI agents for Paysafe SDK.

This module provides AI-powered agents for specific use cases in the Paysafe SDK.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

from paysafe import Client, AsyncClient
from paysafe.models.payment import Payment
from paysafe.models.customer import Customer
from paysafe.ai.base import BaseAIAgent, ClientType
from paysafe.ai.config import AIConfig

# Set up logging
logger = logging.getLogger("paysafe.ai.agents")


class PaymentAgent(BaseAIAgent):
    """
    AI agent for payment operations.
    
    This agent provides AI-powered assistance for payment operations,
    including fraud detection, payment recommendation, and decision-making.
    """
    
    def analyze_transaction_risk(
        self,
        payment_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze the risk level of a transaction.
        
        Args:
            payment_data: Payment data to analyze, including transaction details.
            
        Returns:
            A dictionary containing risk assessment details.
        """
        self._ensure_ai_available()
        
        # Construct the prompt
        prompt = f"""
        Analyze the following payment transaction for risk:
        
        Transaction Details:
        - Amount: {payment_data.get('amount')}
        - Currency: {payment_data.get('currency_code')}
        - Payment Method: {payment_data.get('payment_method')}
        - Country: {payment_data.get('country', 'Unknown')}
        - Time: {payment_data.get('time', datetime.now().isoformat())}
        
        Provide a detailed risk assessment including:
        1. Overall risk level (low, medium, high)
        2. Risk score (0-100)
        3. Specific risk factors identified
        4. Recommendations for handling this transaction
        """
        
        system_prompt = """
        You are an expert risk assessment system for payment transactions.
        Analyze the transaction details and provide a comprehensive risk assessment.
        Always consider factors like transaction amount, country, payment method, and timing.
        """
        
        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
        )
    
    def suggest_payment_optimization(
        self,
        payment_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Suggest optimizations for payment processing based on payment history.
        
        Args:
            payment_history: A list of previous payment transactions.
            
        Returns:
            A dictionary containing optimization suggestions.
        """
        self._ensure_ai_available()
        
        # Prepare the payment history for the prompt
        history_str = "\n\n".join([
            f"Payment {i+1}:\n" + 
            "\n".join([f"- {k}: {v}" for k, v in payment.items()])
            for i, payment in enumerate(payment_history[:10])  # Limit to 10 for brevity
        ])
        
        prompt = f"""
        Based on the following payment history, suggest optimizations for payment processing:
        
        {history_str}
        
        Provide suggestions for:
        1. Optimal payment methods to offer
        2. Preferred processors or routing strategies
        3. Potential cost savings opportunities
        4. Ways to increase conversion rates
        5. Recurring payment opportunities if applicable
        """
        
        system_prompt = """
        You are a payment optimization expert. Analyze the payment history and provide 
        actionable suggestions to improve payment acceptance rates, reduce costs, 
        and enhance the overall payment experience.
        """
        
        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
        )
    
    async def monitor_payment_patterns(
        self,
        payment_ids: List[str],
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Monitor payment patterns for anomalies or fraud indicators.
        
        This is a long-running task that analyzes payment patterns over time.
        
        Args:
            payment_ids: List of payment IDs to monitor.
            lookback_days: Number of days to look back for pattern analysis.
            
        Returns:
            A dictionary containing pattern analysis results.
        """
        self._ensure_ai_available()
        
        # Ensure the client is async
        if not isinstance(self.client, AsyncClient):
            raise ValueError("This method requires an AsyncClient")
        client = cast(AsyncClient, self.client)
        
        # Get each payment
        payments = []
        for payment_id in payment_ids:
            try:
                payment = await Payment.async_retrieve(
                    client=client,
                    payment_id=payment_id,
                )
                payments.append(payment.model_dump())
            except Exception as e:
                logger.warning(f"Failed to retrieve payment {payment_id}: {e}")
        
        # Get additional historical payments for context
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            historical_payments = await Payment.async_list(
                client=client,
                created_from=start_date,
                created_to=end_date,
                limit=50,  # Reasonable limit for analysis
            )
            historical_data = [p.model_dump() for p in historical_payments]
        except Exception as e:
            logger.warning(f"Failed to retrieve historical payments: {e}")
            historical_data = []
        
        # Prepare data for AI analysis
        payment_data_str = json.dumps(payments)
        historical_data_str = json.dumps(historical_data[:10])  # Limit to avoid token limits
        
        prompt = f"""
        Analyze the following payments for patterns and potential anomalies:
        
        Target Payments:
        {payment_data_str}
        
        Historical Context (Sample):
        {historical_data_str}
        
        Provide a detailed analysis including:
        1. Identified patterns in payment behavior
        2. Any anomalies or outliers detected
        3. Potential fraud indicators
        4. Recommendations for further monitoring or action
        """
        
        system_prompt = """
        You are a payment monitoring expert system. Analyze payment patterns
        to identify anomalies, potential fraud, or concerning behavior.
        Focus on metrics like amount distributions, frequency, geographical patterns,
        and unusual timing. Provide actionable insights.
        """
        
        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
        )


class SubscriptionAgent(BaseAIAgent):
    """
    AI agent for subscription and recurring payment management.
    
    This agent provides AI-powered assistance for subscription-related operations,
    including lifecycle management, renewal optimization, and retention strategies.
    """
    
    def predict_churn_risk(
        self,
        customer_data: Dict[str, Any],
        subscription_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Predict the risk of churn for a subscription customer.
        
        Args:
            customer_data: Customer data including profile information.
            subscription_history: List of subscription events and transactions.
            
        Returns:
            A dictionary containing churn risk assessment.
        """
        self._ensure_ai_available()
        
        # Format customer data for the prompt
        customer_info = "\n".join([f"- {k}: {v}" for k, v in customer_data.items()])
        
        # Format subscription history for the prompt
        history_str = "\n\n".join([
            f"Event {i+1}:\n" + 
            "\n".join([f"- {k}: {v}" for k, v in event.items()])
            for i, event in enumerate(subscription_history[:10])  # Limit to 10 for brevity
        ])
        
        prompt = f"""
        Analyze the following customer and subscription data to predict churn risk:
        
        Customer Information:
        {customer_info}
        
        Subscription History:
        {history_str}
        
        Provide a detailed churn risk assessment including:
        1. Overall churn risk level (low, medium, high)
        2. Churn probability percentage
        3. Key risk factors identified
        4. Recommended retention actions
        5. Optimal timeframe for intervention
        """
        
        system_prompt = """
        You are a subscription analytics expert. Analyze customer and subscription data
        to predict the likelihood of subscription cancellation or non-renewal.
        Focus on identifying patterns associated with churn and provide actionable 
        recommendations to improve retention.
        """
        
        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
        )
    
    def optimize_renewal_strategy(
        self,
        subscription_data: Dict[str, Any],
        payment_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Optimize the renewal strategy for a subscription.
        
        Args:
            subscription_data: Current subscription data.
            payment_history: Payment history for the subscription.
            
        Returns:
            A dictionary containing optimized renewal strategy.
        """
        self._ensure_ai_available()
        
        # Format subscription data
        subscription_info = "\n".join([f"- {k}: {v}" for k, v in subscription_data.items()])
        
        # Format payment history
        payment_info = "\n\n".join([
            f"Payment {i+1}:\n" + 
            "\n".join([f"- {k}: {v}" for k, v in payment.items()])
            for i, payment in enumerate(payment_history[:10])
        ])
        
        prompt = f"""
        Optimize the renewal strategy for the following subscription:
        
        Subscription Details:
        {subscription_info}
        
        Payment History:
        {payment_info}
        
        Provide a detailed optimization strategy including:
        1. Optimal renewal timing
        2. Preferred payment method for renewals
        3. Pricing strategy recommendations
        4. Communication plan for renewal notifications
        5. Recovery strategy for failed payments
        """
        
        system_prompt = """
        You are a subscription renewal optimization expert. Analyze subscription and payment data
        to determine the most effective renewal strategy that maximizes retention and minimizes
        failed payments. Focus on timing, pricing, communication, and recovery strategies.
        """
        
        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
        )
    
    async def manage_subscription_lifecycle(
        self,
        customer_id: str,
        subscription_id: str,
        days_to_monitor: int = 90,
    ) -> Dict[str, Any]:
        """
        Autonomously manage subscription lifecycle over time.
        
        This is a long-running task that monitors and optimizes a subscription over time.
        
        Args:
            customer_id: Customer ID associated with the subscription.
            subscription_id: Subscription ID to manage.
            days_to_monitor: Number of days to monitor and manage the subscription.
            
        Returns:
            A dictionary containing lifecycle management results.
        """
        self._ensure_ai_available()
        
        # Ensure the client is async
        if not isinstance(self.client, AsyncClient):
            raise ValueError("This method requires an AsyncClient")
        client = cast(AsyncClient, self.client)
        
        # Get customer data
        try:
            customer = await Customer.async_retrieve(
                client=client,
                customer_id=customer_id,
            )
            customer_data = customer.model_dump()
        except Exception as e:
            logger.warning(f"Failed to retrieve customer {customer_id}: {e}")
            customer_data = {"id": customer_id}
        
        # Get subscription data (simplified - actual implementation would get subscription details)
        subscription_data = {"id": subscription_id}
        
        # Get payment history
        try:
            # In a real implementation, this would filter by subscription ID
            payment_history = await Payment.async_list(
                client=client,
                limit=50,
            )
            payment_data = [p.model_dump() for p in payment_history]
        except Exception as e:
            logger.warning(f"Failed to retrieve payment history: {e}")
            payment_data = []
        
        # Simulate subscription lifecycle steps
        steps = [
            "initial_assessment",
            "risk_analysis",
            "payment_optimization",
            "renewal_planning",
            "churn_prevention",
        ]
        
        # Build a comprehensive lifecycle management plan
        lifecycle_plan = {}
        
        for step in steps:
            prompt = f"""
            Perform the following subscription lifecycle management step: {step}
            
            Customer Data:
            {json.dumps(customer_data)}
            
            Subscription Data:
            {json.dumps(subscription_data)}
            
            Payment History (sample):
            {json.dumps(payment_data[:5])}
            
            Management Duration: {days_to_monitor} days
            
            Provide a detailed plan for this lifecycle step including:
            1. Specific actions to take
            2. Timing recommendations
            3. Key metrics to monitor
            4. Success criteria
            5. Contingency plans
            """
            
            system_prompt = f"""
            You are a subscription lifecycle management expert focusing on the '{step}' phase.
            Create a comprehensive plan for this phase of subscription management that optimizes
            customer satisfaction, minimizes payment failures, and maximizes long-term retention.
            """
            
            lifecycle_plan[step] = self.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
            )
        
        # Synthesize the final lifecycle management plan
        synthesis_prompt = f"""
        Synthesize a comprehensive subscription lifecycle management plan based on the following step plans:
        
        {json.dumps(lifecycle_plan)}
        
        Create a unified plan for managing this subscription over {days_to_monitor} days that:
        1. Provides a timeline of actions and interventions
        2. Establishes key monitoring metrics and thresholds
        3. Details proactive retention strategies
        4. Outlines communication touchpoints
        5. Includes recovery procedures for potential issues
        """
        
        system_prompt = """
        You are a subscription lifecycle management expert. Create a comprehensive, actionable
        plan that synthesizes multiple management phases into a cohesive strategy for long-term
        subscription optimization and customer retention.
        """
        
        final_plan = self.generate_json(
            prompt=synthesis_prompt,
            system_prompt=system_prompt,
        )
        
        return {
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "management_duration_days": days_to_monitor,
            "phase_plans": lifecycle_plan,
            "final_management_plan": final_plan,
        }


class CustomerAgent(BaseAIAgent):
    """
    AI agent for customer-related operations.
    
    This agent provides AI-powered assistance for customer operations,
    including segmentation, value analysis, and personalization.
    """
    
    def segment_customer(
        self,
        customer_data: Dict[str, Any],
        transaction_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Segment a customer based on their profile and transaction history.
        
        Args:
            customer_data: Customer profile data.
            transaction_history: Customer's transaction history.
            
        Returns:
            A dictionary containing customer segmentation results.
        """
        self._ensure_ai_available()
        
        # Format customer data
        customer_info = "\n".join([f"- {k}: {v}" for k, v in customer_data.items()])
        
        # Format transaction history
        transaction_info = "\n\n".join([
            f"Transaction {i+1}:\n" + 
            "\n".join([f"- {k}: {v}" for k, v in tx.items()])
            for i, tx in enumerate(transaction_history[:15])
        ])
        
        prompt = f"""
        Segment the following customer based on their profile and transaction history:
        
        Customer Profile:
        {customer_info}
        
        Transaction History:
        {transaction_info}
        
        Provide a detailed customer segmentation including:
        1. Primary customer segment (e.g., high-value, occasional, new)
        2. Customer value tier (low, medium, high)
        3. Behavioral patterns identified
        4. Preferred payment methods
        5. Spending habits and preferences
        6. Recommended personalization approach
        """
        
        system_prompt = """
        You are a customer segmentation expert. Analyze customer profile data and transaction history
        to categorize customers into meaningful segments that can inform business strategy.
        Focus on identifying patterns in spending behavior, payment preferences, and transaction frequency.
        """
        
        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
        )
    
    def analyze_lifetime_value(
        self,
        customer_data: Dict[str, Any],
        transaction_history: List[Dict[str, Any]],
        months_to_project: int = 24,
    ) -> Dict[str, Any]:
        """
        Analyze and predict customer lifetime value.
        
        Args:
            customer_data: Customer profile data.
            transaction_history: Customer's transaction history.
            months_to_project: Number of months to project future value.
            
        Returns:
            A dictionary containing customer lifetime value analysis.
        """
        self._ensure_ai_available()
        
        # Format customer data
        customer_info = "\n".join([f"- {k}: {v}" for k, v in customer_data.items()])
        
        # Format transaction history with focus on amounts and dates
        transaction_info = "\n".join([
            f"- Date: {tx.get('date', 'Unknown')}, Amount: {tx.get('amount', 'Unknown')}, "
            f"Type: {tx.get('type', 'Unknown')}"
            for tx in transaction_history[:20]
        ])
        
        prompt = f"""
        Analyze the lifetime value for the following customer:
        
        Customer Profile:
        {customer_info}
        
        Transaction History:
        {transaction_info}
        
        Projection Period: {months_to_project} months
        
        Provide a detailed customer lifetime value analysis including:
        1. Current estimated lifetime value
        2. Projected lifetime value over the next {months_to_project} months
        3. Monthly value projection
        4. Key factors influencing the projection
        5. Recommended strategies to increase lifetime value
        6. Confidence level in the projection (percentage)
        """
        
        system_prompt = """
        You are a customer lifetime value (CLV) analysis expert. Calculate and project
        the total value a customer will bring to the business over their lifetime,
        based on historical transaction patterns and customer characteristics.
        Consider factors like purchase frequency, average order value, retention likelihood,
        and market trends in your analysis.
        """
        
        return self.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
        )
    
    async def build_customer_insights(
        self,
        customer_id: str,
    ) -> Dict[str, Any]:
        """
        Build comprehensive insights for a customer.
        
        This method gathers data from various sources and uses AI to generate
        actionable customer insights.
        
        Args:
            customer_id: The ID of the customer to analyze.
            
        Returns:
            A dictionary containing comprehensive customer insights.
        """
        self._ensure_ai_available()
        
        # Ensure the client is async
        if not isinstance(self.client, AsyncClient):
            raise ValueError("This method requires an AsyncClient")
        client = cast(AsyncClient, self.client)
        
        # Get customer data
        try:
            customer = await Customer.async_retrieve(
                client=client,
                customer_id=customer_id,
            )
            customer_data = customer.model_dump()
        except Exception as e:
            logger.warning(f"Failed to retrieve customer {customer_id}: {e}")
            customer_data = {"id": customer_id}
        
        # Get payment history
        try:
            # In a real implementation, this would filter by customer ID
            payment_history = await Payment.async_list(
                client=client,
                limit=100,
            )
            payment_data = [p.model_dump() for p in payment_history]
        except Exception as e:
            logger.warning(f"Failed to retrieve payment history: {e}")
            payment_data = []
        
        # Generate insights on different aspects of the customer
        insight_categories = [
            "behavior_patterns",
            "payment_preferences",
            "risk_profile",
            "growth_opportunities",
            "retention_strategies",
        ]
        
        all_insights = {}
        
        for category in insight_categories:
            prompt = f"""
            Generate insights for the following customer in the category: {category}
            
            Customer Data:
            {json.dumps(customer_data)}
            
            Payment History (sample):
            {json.dumps(payment_data[:10])}
            
            Provide detailed insights specifically focusing on {category}, including:
            1. Key observations
            2. Notable patterns
            3. Actionable recommendations
            4. Supporting data points
            5. Confidence level in these insights
            """
            
            system_prompt = f"""
            You are a customer insights expert specializing in {category}.
            Analyze the customer data and payment history to extract meaningful patterns
            and actionable insights in this specific area. Focus on providing insights
            that can drive business decisions and improve customer relationship management.
            """
            
            all_insights[category] = self.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
            )
        
        # Synthesize the insights into a comprehensive profile
        synthesis_prompt = f"""
        Synthesize the following customer insights into a comprehensive customer profile:
        
        {json.dumps(all_insights)}
        
        Create a unified customer profile that:
        1. Summarizes key characteristics and behaviors
        2. Identifies the most valuable insights across categories
        3. Prioritizes recommendations by potential impact
        4. Highlights opportunities for personalization
        5. Outlines a strategic approach for customer management
        """
        
        system_prompt = """
        You are a customer insight synthesis expert. Create a comprehensive, actionable
        customer profile by integrating insights from multiple categories into a cohesive
        view that can inform business strategy and customer relationship management.
        """
        
        customer_profile = self.generate_json(
            prompt=synthesis_prompt,
            system_prompt=system_prompt,
        )
        
        return {
            "customer_id": customer_id,
            "category_insights": all_insights,
            "comprehensive_profile": customer_profile,
        }
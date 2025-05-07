"""
Example demonstrating synchronous usage of the Paysafe SDK.
"""

import os
from typing import Optional

from paysafe import Client
from paysafe.api_resources.payment import Payment as PaymentResource
from paysafe.models.payment import CardPaymentMethod, Payment


def create_payment(api_key: str, amount: int = 1000, currency: str = "USD") -> Optional[str]:
    """
    Create a payment using the synchronous API.
    
    Args:
        api_key: Your Paysafe API key.
        amount: The payment amount in cents (default: 1000 = $10.00).
        currency: The payment currency code (default: USD).
        
    Returns:
        The ID of the created payment if successful, None otherwise.
    """
    try:
        # Initialize the client
        client = Client(api_key=api_key, environment="sandbox")
        
        # Create a payment resource
        payment_resource = PaymentResource(client)
        
        # Create a payment method
        payment_method = CardPaymentMethod(
            card_number="4111111111111111",
            card_expiry={"month": 12, "year": 25},
            card_holder_name="John Doe",
            card_cvv="123"
        )
        
        # Create a test payment
        payment = Payment(
            amount=amount,
            currency_code=currency,
            payment_method=payment_method,
            description="Sync test payment"
        )
        
        # Submit the payment
        result = payment_resource.create(payment)
        
        print(f"Payment created successfully:")
        print(f"  ID: {result.id}")
        print(f"  Status: {result.status}")
        print(f"  Amount: {result.amount/100} {result.currency_code}")
        
        return result.id
    
    except Exception as e:
        print(f"Error creating payment: {e}")
        return None


def retrieve_payment(api_key: str, payment_id: str) -> None:
    """
    Retrieve a payment using the synchronous API.
    
    Args:
        api_key: Your Paysafe API key.
        payment_id: The ID of the payment to retrieve.
    """
    try:
        # Initialize the client
        client = Client(api_key=api_key, environment="sandbox")
        
        # Create a payment resource
        payment_resource = PaymentResource(client)
        
        # Retrieve the payment
        result = payment_resource.retrieve(payment_id)
        
        print(f"\nPayment {payment_id} details:")
        print(f"  Status: {result.status}")
        print(f"  Amount: {result.amount/100} {result.currency_code}")
        print(f"  Created at: {result.created_at}")
        
    except Exception as e:
        print(f"Error retrieving payment: {e}")


def main():
    """Run the example."""
    # Get API key from environment variable
    api_key = os.environ.get("PAYSAFE_API_KEY")
    
    if not api_key:
        print("Please set the PAYSAFE_API_KEY environment variable.")
        return
    
    # Create a payment
    payment_id = create_payment(api_key)
    
    if payment_id:
        # Retrieve the payment
        retrieve_payment(api_key, payment_id)


if __name__ == "__main__":
    main()
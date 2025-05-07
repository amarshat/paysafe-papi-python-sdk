Quick Start Guide
===============

This guide will help you get started with the Paysafe Python SDK quickly.

Client Initialization
--------------------

The first step is to initialize the Paysafe client with your API key and the desired environment.

.. code-block:: python

    from paysafe import Client

    # Create a client instance for the sandbox environment
    client = Client(api_key="your_api_key", environment="sandbox")

    # Or for production
    # client = Client(api_key="your_api_key", environment="production")

Creating a Payment
----------------

Here's how to create a payment:

.. code-block:: python

    from paysafe import Client
    from paysafe.models.payment import Payment, CardPaymentMethod

    # Initialize the client
    client = Client(api_key="your_api_key", environment="sandbox")

    # Create a payment method
    payment_method = CardPaymentMethod(
        card_number="4111111111111111",
        card_expiry={"month": 12, "year": 25},
        card_holder_name="John Doe",
        card_cvv="123"
    )

    # Create a payment
    payment = Payment(
        amount=1000,  # $10.00
        currency_code="USD",
        payment_method=payment_method,
        description="Test payment"
    )

    # Submit the payment
    payment_resource = client.Payment
    result = payment_resource.create(payment)

    print(f"Payment created with ID: {result.id}")
    print(f"Status: {result.status}")

Managing Customers
----------------

Creating and managing customers:

.. code-block:: python

    from paysafe import Client
    from paysafe.models.customer import Customer

    # Initialize the client
    client = Client(api_key="your_api_key", environment="sandbox")

    # Create a customer
    customer = Customer(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="1234567890"
    )

    # Submit the customer
    customer_resource = client.Customer
    result = customer_resource.create(customer)

    print(f"Customer created with ID: {result.id}")

    # Retrieve a customer
    customer = customer_resource.retrieve(result.id)

    # Update a customer
    customer.last_name = "Smith"
    updated_customer = customer_resource.update(customer.id, customer)

Card Management
-------------

Working with payment cards:

.. code-block:: python

    from paysafe import Client
    from paysafe.models.card import Card, CardExpiry

    # Initialize the client
    client = Client(api_key="your_api_key", environment="sandbox")

    # Create a card for a customer
    card = Card(
        card_number="4111111111111111",
        expiry=CardExpiry(month=12, year=25),
        holder_name="John Doe",
        cvv="123"
    )

    # Add the card to a customer
    card_resource = client.Card
    result = card_resource.create("customer_id", card)

    print(f"Card created with ID: {result.id}")

    # List all cards for a customer
    cards = card_resource.list("customer_id")
    for card in cards:
        print(f"Card ID: {card.id}, Last Digits: {card.last_digits}")

Error Handling
------------

Proper error handling:

.. code-block:: python

    from paysafe import Client
    from paysafe.exceptions import (
        PaysafeError,
        AuthenticationError,
        InvalidRequestError,
        APIError,
        NetworkError,
        RateLimitError
    )

    # Initialize the client
    client = Client(api_key="your_api_key", environment="sandbox")

    try:
        # Try to retrieve a non-existent payment
        payment_resource = client.Payment
        payment = payment_resource.retrieve("nonexistent_id")
    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
    except InvalidRequestError as e:
        print(f"Invalid request: {e}")
    except APIError as e:
        print(f"API error: {e}")
    except NetworkError as e:
        print(f"Network error: {e}")
    except RateLimitError as e:
        print(f"Rate limit exceeded: {e}")
    except PaysafeError as e:
        print(f"An error occurred: {e}")

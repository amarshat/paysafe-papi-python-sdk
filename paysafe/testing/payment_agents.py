"""
AI agents for testing payment workflows.

This module provides intelligent agents that can test different payment
workflows, handle failures, and explore various code paths. The agents
are designed to work with the mock client and server for local testing.
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from paysafe.api_resources.customer import Customer
from paysafe.api_resources.payment import Payment
from paysafe.api_resources.refund import Refund
from paysafe.exceptions import PaysafeError
from paysafe.models.customer import Customer as CustomerModel
from paysafe.models.payment import (
    CardPaymentMethod,
    Payment as PaymentModel,
    PaymentStatus,
)
from paysafe.models.refund import Refund as RefundModel
from paysafe.testing.mock_client import MockClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("paysafe.testing.agents")


class PaymentScenario(Enum):
    """Possible payment test scenarios."""

    SUCCESSFUL_PAYMENT = "successful_payment"
    DECLINED_PAYMENT = "declined_payment"
    EXPIRED_CARD = "expired_card"
    INVALID_CVV = "invalid_cvv"
    PARTIAL_REFUND = "partial_refund"
    FULL_REFUND = "full_refund"
    EXCESSIVE_REFUND = "excessive_refund"
    HIGH_VALUE_PAYMENT = "high_value_payment"
    IDEMPOTENT_REQUEST = "idempotent_request"
    NETWORK_ERROR = "network_error"


@dataclass
class TestResult:
    """Results of a payment test."""

    scenario: PaymentScenario
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    payment_id: Optional[str] = None
    refund_id: Optional[str] = None
    customer_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Get string representation of the test result."""
        status_str = "✅ SUCCESS" if self.success else "❌ FAILURE"
        message = f"{status_str} - {self.scenario.value} - {self.execution_time:.2f}s"
        
        if self.error_message:
            message += f"\n  Error: {self.error_message}"
        
        if self.payment_id:
            message += f"\n  Payment ID: {self.payment_id}"
            
        if self.status:
            message += f"\n  Status: {self.status}"
            
        if self.amount is not None:
            message += f"\n  Amount: ${self.amount/100:.2f}"
            
        if self.refund_id:
            message += f"\n  Refund ID: {self.refund_id}"
            
        if self.customer_id:
            message += f"\n  Customer ID: {self.customer_id}"
            
        return message


class Agent(ABC):
    """Base class for payment testing agents."""

    def __init__(self, client: MockClient):
        """
        Initialize the agent.

        Args:
            client: Mock Paysafe client
        """
        self.client = client
        self.payment_resource = Payment(client)
        self.customer_resource = Customer(client)
        self.refund_resource = Refund(client)

    @abstractmethod
    def run(self) -> List[TestResult]:
        """
        Run the agent's tests.

        Returns:
            List of test results
        """
        pass

    def _create_test_customer(self) -> Tuple[str, CustomerModel]:
        """
        Create a test customer.

        Returns:
            Tuple of customer ID and customer model
        """
        customer = CustomerModel(
            first_name=f"Test{random.randint(1000, 9999)}",
            last_name=f"User{random.randint(1000, 9999)}",
            email=f"test.user{random.randint(1000, 9999)}@example.com",
            phone=f"555{random.randint(1000, 9999)}",
        )
        
        result = self.customer_resource.create(customer)
        return result.id, result

    def _create_payment_method(self, card_type: str = "valid") -> CardPaymentMethod:
        """
        Create a payment method with different card types for testing.

        Args:
            card_type: Type of card to create (valid, declined, expired, invalid_cvv)

        Returns:
            Card payment method
        """
        card_number = "4111111111111111"  # Default valid card
        
        if card_type == "declined":
            card_number = "4000000000000002"  # Card that will be declined
        elif card_type == "expired":
            card_number = "4000000000000069"  # Expired card
        elif card_type == "invalid_cvv":
            card_number = "4000000000000127"  # Invalid CVV
            
        return CardPaymentMethod(
            card_number=card_number,
            card_expiry={"month": 12, "year": 25},
            card_holder_name=f"Test User {random.randint(1000, 9999)}",
            card_cvv=str(random.randint(100, 999)),  # Random CVV
        )

    def _execute_test(
        self, scenario: PaymentScenario, test_func: callable
    ) -> TestResult:
        """
        Execute a test with timing and error handling.

        Args:
            scenario: Test scenario
            test_func: Function to execute

        Returns:
            Test result
        """
        start_time = time.time()
        result = TestResult(scenario=scenario, success=False, execution_time=0)
        
        try:
            test_result = test_func()
            result.success = True
            
            # Update result with test-specific data
            if isinstance(test_result, dict):
                for key, value in test_result.items():
                    setattr(result, key, value)
        except PaysafeError as e:
            result.error_message = str(e)
            # Some errors are expected in certain scenarios
            if (
                (scenario == PaymentScenario.DECLINED_PAYMENT and "declined" in str(e).lower())
                or (scenario == PaymentScenario.EXPIRED_CARD and "expired" in str(e).lower())
                or (scenario == PaymentScenario.INVALID_CVV and "cvv" in str(e).lower())
                or (scenario == PaymentScenario.EXCESSIVE_REFUND and "exceed" in str(e).lower())
                or (scenario == PaymentScenario.NETWORK_ERROR and isinstance(e, PaysafeError))
            ):
                result.success = True
        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"
            
        result.execution_time = time.time() - start_time
        return result


class PaymentAgent(Agent):
    """
    Agent for testing basic payment workflows.

    This agent tests the core payment flows including successful payments,
    declined payments, and refunds.
    """

    def run(self) -> List[TestResult]:
        """
        Run the payment agent's tests.

        Returns:
            List of test results
        """
        results = []
        
        # Test successful payment
        results.append(self._execute_test(
            PaymentScenario.SUCCESSFUL_PAYMENT,
            self._test_successful_payment
        ))
        
        # Test declined payment
        results.append(self._execute_test(
            PaymentScenario.DECLINED_PAYMENT,
            self._test_declined_payment
        ))
        
        # Test expired card
        results.append(self._execute_test(
            PaymentScenario.EXPIRED_CARD,
            self._test_expired_card
        ))
        
        # Test invalid CVV
        results.append(self._execute_test(
            PaymentScenario.INVALID_CVV,
            self._test_invalid_cvv
        ))
        
        # Test full refund
        results.append(self._execute_test(
            PaymentScenario.FULL_REFUND,
            self._test_full_refund
        ))
        
        # Test partial refund
        results.append(self._execute_test(
            PaymentScenario.PARTIAL_REFUND,
            self._test_partial_refund
        ))
        
        # Test excessive refund
        results.append(self._execute_test(
            PaymentScenario.EXCESSIVE_REFUND,
            self._test_excessive_refund
        ))
        
        return results

    def _test_successful_payment(self) -> Dict[str, Any]:
        """Test successful payment flow."""
        # Create a customer
        customer_id, _ = self._create_test_customer()
        
        # Create a payment
        payment_method = self._create_payment_method()
        payment = PaymentModel(
            amount=1000,  # $10.00
            currency_code="USD",
            payment_method=payment_method,
            description="Test payment",
        )
        
        result = self.payment_resource.create(payment)
        
        return {
            "payment_id": result.id,
            "status": result.status,
            "amount": result.amount,
            "customer_id": customer_id,
        }

    def _test_declined_payment(self) -> Dict[str, Any]:
        """Test declined payment flow."""
        # Create a payment with a card that will be declined
        payment_method = self._create_payment_method("declined")
        payment = PaymentModel(
            amount=1000,  # $10.00
            currency_code="USD",
            payment_method=payment_method,
            description="Test declined payment",
        )
        
        # This should raise an error that gets caught by _execute_test
        result = self.payment_resource.create(payment)
        return {}  # This should not be reached

    def _test_expired_card(self) -> Dict[str, Any]:
        """Test payment with expired card."""
        # Create a payment with an expired card
        payment_method = self._create_payment_method("expired")
        payment = PaymentModel(
            amount=1000,  # $10.00
            currency_code="USD",
            payment_method=payment_method,
            description="Test payment with expired card",
        )
        
        # This should raise an error that gets caught by _execute_test
        result = self.payment_resource.create(payment)
        return {}  # This should not be reached

    def _test_invalid_cvv(self) -> Dict[str, Any]:
        """Test payment with invalid CVV."""
        # Create a payment with invalid CVV
        payment_method = self._create_payment_method("invalid_cvv")
        payment = PaymentModel(
            amount=1000,  # $10.00
            currency_code="USD",
            payment_method=payment_method,
            description="Test payment with invalid CVV",
        )
        
        # This should raise an error that gets caught by _execute_test
        result = self.payment_resource.create(payment)
        return {}  # This should not be reached

    def _test_full_refund(self) -> Dict[str, Any]:
        """Test full refund flow."""
        # Create a successful payment first
        payment_method = self._create_payment_method()
        payment = PaymentModel(
            amount=2000,  # $20.00
            currency_code="USD",
            payment_method=payment_method,
            description="Payment for full refund test",
        )
        
        payment_result = self.payment_resource.create(payment)
        
        # Create a full refund
        refund = RefundModel(
            amount=payment_result.amount,
            currency_code=payment_result.currency_code,
            description="Full refund",
        )
        
        refund_result = self.refund_resource.create(payment_result.id, refund)
        
        return {
            "payment_id": payment_result.id,
            "refund_id": refund_result.id,
            "status": refund_result.status,
            "amount": refund_result.amount,
        }

    def _test_partial_refund(self) -> Dict[str, Any]:
        """Test partial refund flow."""
        # Create a successful payment first
        payment_method = self._create_payment_method()
        payment = PaymentModel(
            amount=5000,  # $50.00
            currency_code="USD",
            payment_method=payment_method,
            description="Payment for partial refund test",
        )
        
        payment_result = self.payment_resource.create(payment)
        
        # Create a partial refund
        refund_amount = payment_result.amount // 2  # Refund half the amount
        refund = RefundModel(
            amount=refund_amount,
            currency_code=payment_result.currency_code,
            description="Partial refund",
        )
        
        refund_result = self.refund_resource.create(payment_result.id, refund)
        
        return {
            "payment_id": payment_result.id,
            "refund_id": refund_result.id,
            "status": refund_result.status,
            "amount": refund_result.amount,
            "details": {
                "original_amount": payment_result.amount,
                "refund_amount": refund_amount,
            },
        }

    def _test_excessive_refund(self) -> Dict[str, Any]:
        """Test refund with amount exceeding payment amount."""
        # Create a successful payment first
        payment_method = self._create_payment_method()
        payment = PaymentModel(
            amount=1000,  # $10.00
            currency_code="USD",
            payment_method=payment_method,
            description="Payment for excessive refund test",
        )
        
        payment_result = self.payment_resource.create(payment)
        
        # Create a refund with excessive amount
        refund = RefundModel(
            amount=payment_result.amount * 2,  # Double the payment amount
            currency_code=payment_result.currency_code,
            description="Excessive refund",
        )
        
        # This should raise an error that gets caught by _execute_test
        refund_result = self.refund_resource.create(payment_result.id, refund)
        return {}  # This should not be reached


class FraudDetectionAgent(Agent):
    """
    Agent for testing fraud detection and risk management.

    This agent performs tests related to fraud detection, including
    high-value payments and suspicious activity patterns.
    """

    def run(self) -> List[TestResult]:
        """
        Run the fraud detection agent's tests.

        Returns:
            List of test results
        """
        results = []
        
        # Test high-value payment
        results.append(self._execute_test(
            PaymentScenario.HIGH_VALUE_PAYMENT,
            self._test_high_value_payment
        ))
        
        # Test rapid successive payments
        results.extend(self._test_rapid_payments())
        
        # Test multiple failed attempts followed by success
        results.extend(self._test_multiple_failures_then_success())
        
        return results

    def _test_high_value_payment(self) -> Dict[str, Any]:
        """Test high-value payment that might trigger additional verification."""
        # Create a high-value payment
        payment_method = self._create_payment_method()
        payment = PaymentModel(
            amount=50000,  # $500.00
            currency_code="USD",
            payment_method=payment_method,
            description="High-value payment test",
        )
        
        result = self.payment_resource.create(payment)
        
        return {
            "payment_id": result.id,
            "status": result.status,  # This might be PENDING for high-value payments
            "amount": result.amount,
            "details": {
                "is_high_value": True,
                "requires_additional_verification": result.status == "PENDING",
            },
        }

    def _test_rapid_payments(self) -> List[TestResult]:
        """Test making multiple rapid payments to detect velocity patterns."""
        results = []
        payment_method = self._create_payment_method()
        
        # Make several payments in quick succession
        for i in range(3):
            scenario = PaymentScenario.SUCCESSFUL_PAYMENT
            result = self._execute_test(
                scenario,
                lambda: self._make_payment(
                    payment_method, 1000, f"Rapid payment test {i+1}"
                ),
            )
            results.append(result)
            
        return results

    def _test_multiple_failures_then_success(self) -> List[TestResult]:
        """Test multiple failed payments followed by a successful one."""
        results = []
        
        # Create several failed payments
        for i in range(2):
            scenario = PaymentScenario.DECLINED_PAYMENT
            result = self._execute_test(
                scenario,
                lambda: self._make_payment_with_card(
                    "declined", 1000, f"Failed payment test {i+1}"
                ),
            )
            results.append(result)
        
        # Then make a successful payment
        scenario = PaymentScenario.SUCCESSFUL_PAYMENT
        result = self._execute_test(
            scenario,
            lambda: self._make_payment_with_card(
                "valid", 1000, "Successful payment after failures"
            ),
        )
        results.append(result)
        
        return results

    def _make_payment(
        self, payment_method: CardPaymentMethod, amount: int, description: str
    ) -> Dict[str, Any]:
        """Helper to make a payment with the given parameters."""
        payment = PaymentModel(
            amount=amount,
            currency_code="USD",
            payment_method=payment_method,
            description=description,
        )
        
        result = self.payment_resource.create(payment)
        
        return {
            "payment_id": result.id,
            "status": result.status,
            "amount": result.amount,
            "details": {"description": description},
        }

    def _make_payment_with_card(
        self, card_type: str, amount: int, description: str
    ) -> Dict[str, Any]:
        """Helper to make a payment with a specific card type."""
        payment_method = self._create_payment_method(card_type)
        return self._make_payment(payment_method, amount, description)


class RecoveryAgent(Agent):
    """
    Agent for testing recovery and resilience.

    This agent tests the system's ability to recover from errors and
    handle network issues gracefully.
    """

    def run(self) -> List[TestResult]:
        """
        Run the recovery agent's tests.

        Returns:
            List of test results
        """
        results = []
        
        # Test idempotent request
        results.append(self._execute_test(
            PaymentScenario.IDEMPOTENT_REQUEST,
            self._test_idempotent_request
        ))
        
        # Test recovery from network error
        # We'll simulate this by temporarily increasing the fail rate
        results.append(self._execute_test(
            PaymentScenario.NETWORK_ERROR,
            self._test_recovery_from_network_error
        ))
        
        return results

    def _test_idempotent_request(self) -> Dict[str, Any]:
        """Test idempotent request handling."""
        # Create a payment with an idempotency key
        payment_method = self._create_payment_method()
        payment = PaymentModel(
            amount=1500,  # $15.00
            currency_code="USD",
            payment_method=payment_method,
            description="Idempotent payment test",
        )
        
        # Generate a unique idempotency key
        idempotency_key = f"idempotency-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        headers = {"Idempotency-Key": idempotency_key}
        
        # Make the initial request
        first_result = self.payment_resource.create(payment, headers=headers)
        
        # Make the same request again with the same idempotency key
        second_result = self.payment_resource.create(payment, headers=headers)
        
        # Verify both requests returned the same payment ID
        is_idempotent = first_result.id == second_result.id
        
        return {
            "payment_id": first_result.id,
            "status": first_result.status,
            "amount": first_result.amount,
            "details": {
                "idempotency_key": idempotency_key,
                "is_idempotent": is_idempotent,
                "first_payment_id": first_result.id,
                "second_payment_id": second_result.id,
            },
        }

    def _test_recovery_from_network_error(self) -> Dict[str, Any]:
        """Test recovery from network errors with retries."""
        original_fail_rate = self.client.mock_server.fail_rate
        try:
            # Temporarily increase the fail rate to simulate network errors
            self.client.mock_server.fail_rate = 0.8  # 80% chance of failure
            
            # Create a payment with retries
            payment_method = self._create_payment_method()
            payment = PaymentModel(
                amount=2500,  # $25.00
                currency_code="USD",
                payment_method=payment_method,
                description="Network recovery test",
            )
            
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    result = self.payment_resource.create(payment)
                    return {
                        "payment_id": result.id,
                        "status": result.status,
                        "amount": result.amount,
                        "details": {
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                            "recovery_successful": True,
                        },
                    }
                except PaysafeError as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise
                    logger.info(f"Retrying after error: {str(e)}")
                    time.sleep(0.5)  # Short delay between retries
            
            return {}  # This should not be reached
        finally:
            # Restore the original fail rate
            self.client.mock_server.fail_rate = original_fail_rate


class StressTestAgent(Agent):
    """
    Agent for stress testing the system.

    This agent tests the system's performance under high load by
    making many concurrent requests.
    """

    def run(self) -> List[TestResult]:
        """
        Run the stress test agent's tests.

        Returns:
            List of test results
        """
        results = []
        
        # Test concurrent payments
        start_time = time.time()
        concurrent_results = self._test_concurrent_payments(10)  # 10 concurrent payments
        execution_time = time.time() - start_time
        
        # Aggregate results
        success_count = sum(1 for r in concurrent_results if r.get("success", False))
        
        result = TestResult(
            scenario=PaymentScenario.SUCCESSFUL_PAYMENT,
            success=success_count > 0,
            execution_time=execution_time,
            details={
                "concurrent_requests": len(concurrent_results),
                "successful_requests": success_count,
                "failed_requests": len(concurrent_results) - success_count,
                "total_amount_processed": sum(r.get("amount", 0) for r in concurrent_results),
                "average_response_time": sum(r.get("execution_time", 0) for r in concurrent_results)
                / len(concurrent_results),
            },
        )
        
        results.append(result)
        return results

    def _test_concurrent_payments(self, count: int) -> List[Dict[str, Any]]:
        """
        Test making multiple concurrent payments.

        Args:
            count: Number of concurrent payments to make

        Returns:
            List of payment results
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=count) as executor:
            futures = [
                executor.submit(self._make_random_payment) for _ in range(count)
            ]
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
                    
        return results

    def _make_random_payment(self) -> Dict[str, Any]:
        """Make a payment with random amount and description."""
        start_time = time.time()
        try:
            # Create a random payment
            payment_method = self._create_payment_method()
            amount = random.randint(500, 5000)  # Random amount between $5 and $50
            payment = PaymentModel(
                amount=amount,
                currency_code="USD",
                payment_method=payment_method,
                description=f"Stress test payment {random.randint(1000, 9999)}",
            )
            
            result = self.payment_resource.create(payment)
            
            return {
                "success": True,
                "payment_id": result.id,
                "status": result.status,
                "amount": result.amount,
                "execution_time": time.time() - start_time,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
            }
"""
Example demonstrating how to use AI agents for payment testing.

This script shows how to use the intelligent agents to test payment workflows,
handle failures, and explore various code paths without needing real API credentials.
"""

import logging
import time
from typing import List

from paysafe.testing.mock_client import MockClient
from paysafe.testing.payment_agents import (
    FraudDetectionAgent,
    PaymentAgent,
    RecoveryAgent,
    StressTestAgent,
    TestResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agent_testing")


def print_results(agent_name: str, results: List[TestResult]) -> None:
    """
    Print the test results for an agent.

    Args:
        agent_name: Name of the agent
        results: List of test results
    """
    print(f"\n{'=' * 80}")
    print(f"Results for {agent_name}:")
    print(f"{'=' * 80}")
    
    success_count = sum(1 for r in results if r.success)
    print(f"Success rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    for i, result in enumerate(results, 1):
        print(f"\nTest {i}: {result}")


def run_payment_agent(client: MockClient) -> None:
    """
    Run the basic payment agent.

    Args:
        client: Mock client
    """
    logger.info("Running PaymentAgent tests...")
    agent = PaymentAgent(client)
    start_time = time.time()
    results = agent.run()
    execution_time = time.time() - start_time
    
    print_results("PaymentAgent", results)
    print(f"Total execution time: {execution_time:.2f}s")


def run_fraud_detection_agent(client: MockClient) -> None:
    """
    Run the fraud detection agent.

    Args:
        client: Mock client
    """
    logger.info("Running FraudDetectionAgent tests...")
    agent = FraudDetectionAgent(client)
    start_time = time.time()
    results = agent.run()
    execution_time = time.time() - start_time
    
    print_results("FraudDetectionAgent", results)
    print(f"Total execution time: {execution_time:.2f}s")


def run_recovery_agent(client: MockClient) -> None:
    """
    Run the recovery agent.

    Args:
        client: Mock client
    """
    logger.info("Running RecoveryAgent tests...")
    agent = RecoveryAgent(client)
    start_time = time.time()
    results = agent.run()
    execution_time = time.time() - start_time
    
    print_results("RecoveryAgent", results)
    print(f"Total execution time: {execution_time:.2f}s")


def run_stress_test_agent(client: MockClient) -> None:
    """
    Run the stress test agent.

    Args:
        client: Mock client
    """
    logger.info("Running StressTestAgent tests...")
    agent = StressTestAgent(client)
    start_time = time.time()
    results = agent.run()
    execution_time = time.time() - start_time
    
    print_results("StressTestAgent", results)
    print(f"Total execution time: {execution_time:.2f}s")


def main() -> None:
    """Run the example."""
    print("Starting payment testing with AI agents...")
    
    # Initialize mock client with moderate failure rate and latency
    client = MockClient(
        api_key="mock_api_key",
        environment="sandbox",
        fail_rate=0.05,  # 5% chance of random failure
        latency=(0.1, 0.5),  # Random latency between 0.1 and 0.5 seconds
    )
    
    # Reset the mock server before each agent
    client.reset_mock_server()
    run_payment_agent(client)
    
    client.reset_mock_server()
    run_fraud_detection_agent(client)
    
    client.reset_mock_server()
    run_recovery_agent(client)
    
    client.reset_mock_server()
    run_stress_test_agent(client)
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    main()
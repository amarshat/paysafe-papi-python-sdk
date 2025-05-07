"""
Main entry point for the Paysafe SDK demonstration and testing interface.

This module provides a simple web interface for exploring the Paysafe SDK
features and running tests.
"""

import os
from flask import Flask, render_template, jsonify, request, redirect, url_for

from paysafe.testing.mock_client import MockClient
from paysafe.testing.payment_agents import (
    PaymentAgent,
    FraudDetectionAgent,
    RecoveryAgent,
    StressTestAgent,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "paysafe_sdk_secret")

# Create a mock client for demonstrations
mock_client = MockClient(
    api_key="mock_api_key",
    environment="sandbox",
    fail_rate=0.05,
    latency=(0.1, 0.3),
)


@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')


@app.route('/api/sdk-info')
def sdk_info():
    """Return SDK information."""
    return jsonify({
        "name": "Paysafe Python SDK",
        "version": "0.1.0",
        "description": "Python SDK for the Paysafe API with both synchronous and asynchronous interfaces",
        "features": [
            "Full API support with idiomatic Python interface",
            "Strong typing with comprehensive type hints",
            "Pydantic data validation",
            "Synchronous and asynchronous APIs",
            "Detailed error handling",
            "Mock server for local testing",
            "AI agents for payment workflow testing",
        ]
    })


@app.route('/api/run-tests', methods=['POST'])
def run_tests():
    """Run selected tests using the AI agents."""
    test_types = request.json.get('test_types', [])
    results = []
    
    # Reset the mock server before running tests
    mock_client.reset_mock_server()
    
    if 'payment' in test_types:
        agent = PaymentAgent(mock_client)
        results.extend(agent.run())
        
    if 'fraud' in test_types:
        agent = FraudDetectionAgent(mock_client)
        results.extend(agent.run())
        
    if 'recovery' in test_types:
        agent = RecoveryAgent(mock_client)
        results.extend(agent.run())
        
    if 'stress' in test_types:
        agent = StressTestAgent(mock_client)
        results.extend(agent.run())
    
    # Format results for JSON response
    formatted_results = []
    for result in results:
        formatted_results.append({
            "scenario": result.scenario.value,
            "success": result.success,
            "execution_time": result.execution_time,
            "error_message": result.error_message,
            "payment_id": result.payment_id,
            "status": result.status,
            "amount": result.amount,
            "details": result.details,
        })
    
    return jsonify({
        "success": True,
        "results": formatted_results,
        "total_tests": len(formatted_results),
        "successful_tests": sum(1 for r in formatted_results if r["success"]),
    })


@app.route('/examples')
def examples():
    """Render the examples page."""
    return render_template('examples.html')


@app.route('/documentation')
def documentation():
    """Render the documentation page."""
    return render_template('documentation.html')


@app.route('/testing')
def testing():
    """Render the testing page."""
    return render_template('testing.html')


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)
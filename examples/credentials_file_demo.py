"""
Example of using Paysafe SDK with a credentials file.

This script demonstrates how to use the Paysafe SDK with a credentials file
in Postman format, which contains API keys and other configuration.
"""

import json
import os
import sys
import logging
from pathlib import Path

# Add the parent directory to the path to import the paysafe package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paysafe
from paysafe.utils import load_credentials_from_file, get_api_key_from_credentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_credentials_file(file_path, public_key, private_key, account_id):
    """
    Create a credentials file in Postman format.
    
    Args:
        file_path: Path to save the credentials file
        public_key: The Paysafe public key
        private_key: The Paysafe private key
        account_id: The Paysafe account ID
    """
    credentials = {
        "id": "paysafe-environment",
        "name": "Paysafe Environment",
        "values": [
            {
                "key": "public_key",
                "value": public_key,
                "type": "default",
                "enabled": True
            },
            {
                "key": "private_key",
                "value": private_key,
                "type": "default",
                "enabled": True
            },
            {
                "key": "account_id",
                "value": account_id,
                "type": "default",
                "enabled": True
            }
        ],
        "_postman_variable_scope": "environment"
    }
    
    with open(file_path, 'w') as f:
        json.dump(credentials, f, indent=2)
    
    logger.info(f"Created credentials file at {file_path}")


def main():
    """Main function to demonstrate the credentials file usage."""
    # Example values (these are dummy values, replace with real ones)
    example_public_key = "public_key_from_env_or_input"
    example_private_key = "private_key_from_env_or_input"
    example_account_id = "account_id_from_env_or_input"
    
    # Check if keys are provided as environment variables
    example_public_key = os.environ.get("PAYSAFE_PUBLIC_KEY", example_public_key)
    example_private_key = os.environ.get("PAYSAFE_PRIVATE_KEY", example_private_key)
    example_account_id = os.environ.get("PAYSAFE_ACCOUNT_ID", example_account_id)
    
    # Create a temporary credentials file
    credentials_file = "paysafe_credentials.json"
    create_credentials_file(
        credentials_file,
        example_public_key,
        example_private_key,
        example_account_id
    )
    
    try:
        # Method 1: Load credentials manually
        logger.info("Method 1: Loading credentials manually")
        credentials = load_credentials_from_file(credentials_file)
        logger.info(f"Loaded credentials: {list(credentials.keys())}")
        
        api_key = get_api_key_from_credentials(credentials)
        logger.info(f"API key extracted: {api_key[:10]}...")
        
        # Method 2: Initialize client with credentials file directly
        logger.info("\nMethod 2: Initializing client with credentials file")
        client = paysafe.Client(credentials_file=credentials_file, environment="sandbox")
        logger.info(f"Client initialized with API key: {client.api_key[:10]}...")
        
        # Method 3: Set environment variable and initialize client
        logger.info("\nMethod 3: Using environment variable")
        os.environ["PAYSAFE_CREDENTIALS_FILE"] = credentials_file
        
        # No need to specify credentials_file parameter since it will use the environment variable
        client = paysafe.Client(environment="sandbox")
        logger.info(f"Client initialized with API key from env: {client.api_key[:10]}...")
        
        # Make a test request if we have valid credentials (uncomment for real testing)
        # logger.info("\nTesting API call")
        # try:
        #     response = client.get("customervault/v1/profiles")
        #     logger.info(f"API response: {response}")
        # except Exception as e:
        #     logger.error(f"API call failed: {e}")
        
    finally:
        # Clean up the temporary file
        if os.path.exists(credentials_file):
            os.remove(credentials_file)
            logger.info(f"Removed temporary credentials file: {credentials_file}")


if __name__ == "__main__":
    main()
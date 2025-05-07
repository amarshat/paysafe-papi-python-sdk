"""
Utility functions for the Paysafe SDK.
"""

import json
import os
import re
from typing import Dict, Any, List, Optional, Union, TypeVar, cast


T = TypeVar('T')


def load_credentials_from_file(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Paysafe credentials from a JSON file.

    Args:
        file_path: Path to the JSON credentials file. If not provided,
                  the function will check the PAYSAFE_CREDENTIALS_FILE environment variable.

    Returns:
        Dictionary containing the credentials.

    Raises:
        FileNotFoundError: If the credentials file doesn't exist.
        ValueError: If the credentials file is invalid JSON or missing required fields.
    """
    # Check for file path from environment variable if not provided
    if not file_path:
        file_path = os.environ.get("PAYSAFE_CREDENTIALS_FILE")
        if not file_path:
            raise ValueError(
                "No credentials file path provided and PAYSAFE_CREDENTIALS_FILE environment variable not set."
            )

    # Check if file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Credentials file not found: {file_path}")

    # Load JSON file
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in credentials file: {file_path}")

    # Extract credentials
    credentials = {}
    if not data.get("values"):
        raise ValueError("Missing 'values' key in credentials file")

    # Process the postman environment format
    for item in data.get("values", []):
        key = item.get("key")
        value = item.get("value")
        if key and value and item.get("enabled", True):
            credentials[key] = value

    return credentials


def get_api_key_from_credentials(credentials: Dict[str, Any]) -> str:
    """
    Extract the API key from the credentials dictionary.
    For Paysafe, the API key is typically the combination of the public_key and private_key.

    Args:
        credentials: Dictionary containing the credentials.

    Returns:
        API key string.

    Raises:
        ValueError: If the required credentials are missing.
    """
    private_key = credentials.get("private_key")
    if not private_key:
        raise ValueError("Missing 'private_key' in credentials")
    
    # For some Paysafe integrations, the private key is sufficient as the API key
    return private_key


def _snake_to_camel(snake_str: str) -> str:
    """
    Convert a snake_case string to camelCase.

    Args:
        snake_str: The snake_case string to convert.

    Returns:
        The converted camelCase string.
    """
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + ''.join(x.title() for x in components[1:])


def _camel_to_snake(camel_str: str) -> str:
    """
    Convert a camelCase string to snake_case.

    Args:
        camel_str: The camelCase string to convert.

    Returns:
        The converted snake_case string.
    """
    # Add underscore before any uppercase letter followed by a lowercase one
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    # Add underscore before any uppercase letter that has a lowercase letter before it
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def transform_keys_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform all dictionary keys from snake_case to camelCase.

    Args:
        data: The dictionary with snake_case keys.

    Returns:
        A new dictionary with camelCase keys and the same values.
    """
    if not isinstance(data, dict):
        return data
        
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            value = transform_keys_to_camel_case(value)
        elif isinstance(value, list):
            value = [
                transform_keys_to_camel_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        camel_key = _snake_to_camel(key)
        result[camel_key] = value
        
    return result


def transform_keys_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform all dictionary keys from camelCase to snake_case.

    Args:
        data: The dictionary with camelCase keys.

    Returns:
        A new dictionary with snake_case keys and the same values.
    """
    if not isinstance(data, dict):
        return data
        
    result: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            value = transform_keys_to_snake_case(value)
        elif isinstance(value, list):
            value = [
                transform_keys_to_snake_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        snake_key = _camel_to_snake(key)
        result[snake_key] = value
        
    return result


def validate_id(id_str: Optional[str]) -> None:
    """
    Validate that the ID is a valid ID format for Paysafe.

    Args:
        id_str: The ID to validate.

    Raises:
        ValueError: If the ID is invalid.
    """
    if id_str is None:
        raise ValueError("ID cannot be None")
        
    if not id_str:
        raise ValueError("ID cannot be empty")
        
    if not isinstance(id_str, str):
        raise ValueError(f"ID must be a string, got {type(id_str)}")


def validate_parameters(params: Dict[str, Any], required: List[str]) -> None:
    """
    Validate that required parameters are present.

    Args:
        params: Dictionary of parameters.
        required: List of required parameter names.

    Raises:
        ValueError: If any required parameter is missing.
    """
    for param in required:
        if param not in params:
            raise ValueError(f"Missing required parameter: {param}")
            
        if params[param] is None:
            raise ValueError(f"Parameter {param} cannot be None")
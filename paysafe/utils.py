"""
Utility functions for the Paysafe Python SDK.

This module provides helper functions used across the SDK.
"""

import re
from typing import Any, Dict, List, Optional, Union


def to_snake_case(camel_str: str) -> str:
    """
    Convert a camelCase string to snake_case.

    Args:
        camel_str: A string in camelCase format.

    Returns:
        The string converted to snake_case.
    """
    # First, add an underscore before any uppercase letter that follows a lowercase letter
    # or a digit and isn't at the beginning of the string
    s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', camel_str)
    # Then convert the whole string to lowercase
    return s1.lower()


def to_camel_case(snake_str: str) -> str:
    """
    Convert a snake_case string to camelCase.

    Args:
        snake_str: A string in snake_case format.

    Returns:
        The string converted to camelCase.
    """
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    return components[0] + ''.join(x.title() for x in components[1:])


def transform_keys_to_snake_case(data: Union[Dict[str, Any], List[Any]]) -> Union[Dict[str, Any], List[Any]]:
    """
    Recursively convert all dictionary keys from camelCase to snake_case.

    Args:
        data: A dictionary or list to transform.

    Returns:
        The transformed dictionary or list.
    """
    if isinstance(data, list):
        return [transform_keys_to_snake_case(item) for item in data]
    elif isinstance(data, dict):
        return {
            to_snake_case(key): transform_keys_to_snake_case(value)
            for key, value in data.items()
        }
    else:
        return data


def transform_keys_to_camel_case(data: Union[Dict[str, Any], List[Any]]) -> Union[Dict[str, Any], List[Any]]:
    """
    Recursively convert all dictionary keys from snake_case to camelCase.

    Args:
        data: A dictionary or list to transform.

    Returns:
        The transformed dictionary or list.
    """
    if isinstance(data, list):
        return [transform_keys_to_camel_case(item) for item in data]
    elif isinstance(data, dict):
        return {
            to_camel_case(key): transform_keys_to_camel_case(value)
            for key, value in data.items()
        }
    else:
        return data


def validate_id(resource_id: str, name: str = "id") -> None:
    """
    Validate that the provided ID is not None or empty.

    Args:
        resource_id: The ID to validate.
        name: The name of the ID for error messages.

    Raises:
        ValueError: If the ID is None or empty.
    """
    if not resource_id:
        raise ValueError(f"{name} cannot be None or empty")


def validate_parameters(params: Dict[str, Any], required: List[str]) -> None:
    """
    Validate that required parameters are present.

    Args:
        params: Dictionary of parameters.
        required: List of required parameter names.

    Raises:
        ValueError: If a required parameter is missing.
    """
    missing = [param for param in required if param not in params or params[param] is None]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")


def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from a dictionary.

    Args:
        data: A dictionary to filter.

    Returns:
        A new dictionary with None values removed.
    """
    return {k: v for k, v in data.items() if v is not None}

"""
Configuration for AI agents in the Paysafe SDK.

This module provides the configuration classes for AI agents.
"""

import os
from typing import Optional, Dict, Any, Union


class AIConfig:
    """
    Configuration for AI agents in the Paysafe SDK.
    
    This class manages configuration for OpenAI-powered AI agents.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        log_requests: bool = False,
        log_responses: bool = False,
    ):
        """
        Initialize the AI configuration.
        
        Args:
            api_key: OpenAI API key. If not provided, will check the OPENAI_API_KEY environment variable.
            model: The OpenAI model to use, defaults to "gpt-4o".
            temperature: Controls randomness. Lower values are more deterministic.
            max_tokens: Maximum number of tokens to generate.
            log_requests: Whether to log requests to the OpenAI API.
            log_responses: Whether to log responses from the OpenAI API.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    @property
    def is_configured(self) -> bool:
        """Check if the AI configuration is properly set up with an API key."""
        return self.api_key is not None and len(self.api_key.strip()) > 0
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Get model parameters for OpenAI API calls."""
        params = {
            "model": self.model,
            "temperature": self.temperature,
        }
        
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
            
        return params
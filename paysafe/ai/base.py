"""
Base AI agent class for the Paysafe SDK.

This module provides the base class for all AI agents in the Paysafe SDK.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union, TypeVar, cast

import openai

from paysafe import Client, AsyncClient
from paysafe.ai.config import AIConfig

# Create a type variable for the client
ClientType = TypeVar('ClientType', Client, AsyncClient)

# Set up logging
logger = logging.getLogger("paysafe.ai")


class BaseAIAgent:
    """
    Base class for all AI agents in the Paysafe SDK.
    
    This class provides common functionality for AI agents.
    """
    
    def __init__(
        self,
        client: ClientType,
        ai_config: Optional[AIConfig] = None,
    ):
        """
        Initialize a new AI agent.
        
        Args:
            client: Paysafe API client (sync or async).
            ai_config: AI configuration. If not provided, a default configuration will be used.
        """
        self.client = client
        self.ai_config = ai_config or AIConfig()
        
        # Set up OpenAI client if API key is available
        if self.ai_config.is_configured:
            self.openai_client = openai.OpenAI(api_key=self.ai_config.api_key)
        else:
            self.openai_client = None
            logger.warning(
                "AI agent created without a valid OpenAI API key. "
                "AI-powered features will not be available. "
                "Set the OPENAI_API_KEY environment variable or pass an api_key to AIConfig."
            )
    
    @property
    def is_ai_available(self) -> bool:
        """Check if AI is available for this agent."""
        return self.openai_client is not None
    
    def _ensure_ai_available(self) -> None:
        """Ensure AI is available, raising an exception if not."""
        if not self.is_ai_available:
            raise ValueError(
                "AI features are not available. "
                "Make sure to provide a valid OpenAI API key in the AIConfig."
            )
    
    def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_response: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Generate a completion from the OpenAI API.
        
        Args:
            prompt: The prompt to send to the model.
            system_prompt: Optional system prompt to set context for the model.
            json_response: Whether to request a JSON response from the model.
            **kwargs: Additional parameters to pass to the OpenAI API.
            
        Returns:
            The generated text from the model.
            
        Raises:
            ValueError: If AI is not available.
        """
        self._ensure_ai_available()
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Get model parameters with any overrides
        params = self.ai_config.get_model_parameters()
        params.update(kwargs)
        
        # Add response format for JSON if requested
        if json_response:
            params["response_format"] = {"type": "json_object"}
        
        # Log request if enabled
        if self.ai_config.log_requests:
            logger.info(f"AI Request: {messages}")
            logger.info(f"AI Parameters: {params}")
        
        # Make the API call
        response = self.openai_client.chat.completions.create(
            messages=messages,
            **params,
        )
        
        # Get the response content
        content = response.choices[0].message.content
        
        # Log response if enabled
        if self.ai_config.log_responses:
            logger.info(f"AI Response: {content}")
        
        return content
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from the OpenAI API.
        
        Args:
            prompt: The prompt to send to the model.
            system_prompt: Optional system prompt to set context for the model.
            **kwargs: Additional parameters to pass to the OpenAI API.
            
        Returns:
            The parsed JSON response from the model.
            
        Raises:
            ValueError: If AI is not available or if the response is not valid JSON.
        """
        # Ensure system prompt includes instructions for JSON output
        if system_prompt:
            system_prompt += " Always respond with valid JSON."
        else:
            system_prompt = "You are a helpful assistant that always responds with valid JSON."
        
        # Generate the completion with JSON format
        json_text = self.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            json_response=True,
            **kwargs,
        )
        
        try:
            # Parse the JSON response
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # Log the error and the invalid JSON response
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Invalid JSON response: {json_text}")
            raise ValueError(f"Failed to parse JSON response from AI: {e}")
    
    def __repr__(self) -> str:
        """Return a string representation of the agent."""
        client_type = "AsyncClient" if isinstance(self.client, AsyncClient) else "Client"
        ai_status = "available" if self.is_ai_available else "not available"
        return f"<{self.__class__.__name__} client={client_type} ai={ai_status}>"
"""
API Client for handling communication with AI providers.
Supports multiple providers including OpenAI and Anthropic.
"""
from typing import Dict, Any, List, Tuple, Optional


class APIClient:
    """Handles API communication with AI providers.
    
    This class abstracts away the details of communicating with different
    AI providers, providing a unified interface for making API calls.
    """
    
    def __init__(self, config):
        """Initialize the API client with configuration.
        
        Args:
            config: The application configuration object containing API settings
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not hasattr(self.config, 'unified_client'):
            raise ValueError("Configuration must include 'unified_client'")
    
    def make_api_call(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        task: str = "main"
    ) -> Tuple[str, int]:
        """Make an API call using the unified client.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Override the default model for the task
            temperature: Override the default temperature for the task
            max_tokens: Override the default max tokens for the task
            task: The task type (e.g., 'main', 'summarization', 'analysis')

        Returns:
            Tuple of (response_content, tokens_used)

        Raises:
            Exception: If the API call fails
        """
        # Use task-based model selection if model not specified
        if model is None:
            model = self.config.get_model_for_task(task)
        
        # Get provider for the task
        provider = self.config.get_provider_for_task(task)
        
        # Use task-based temperature if not specified
        if temperature is None:
            temperature = self.config.get_temperature_for_task(task)
            
        # Use task-based max_tokens if not specified
        if max_tokens is None:
            max_tokens = self.config.get_max_tokens_for_task(task)
            
        try:
            # Use unified client for seamless OpenAI/Anthropic switching
            response = self.config.unified_client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                provider=provider
            )
            
            # Log truncation warning if response was truncated
            if response.truncated:
                print(f"⚠️  WARNING: Response was truncated (hit {max_tokens} token limit) - Task: {task}, Model: {model}")

            # Store truncation status for later retrieval if needed
            self.last_response_truncated = response.truncated

            return response.content, response.tokens_used
            
        except Exception as e:
            error_msg = str(e)
            raise Exception(f"API call failed: {error_msg}") from e

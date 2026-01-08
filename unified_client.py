"""
Unified AI Client System
Provides seamless interoperability between OpenAI and Anthropic models
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None




class UnifiedResponse:
    """Standardized response format for all providers."""

    def __init__(self, content: str, tokens_used: int = 0, model: str = "", provider: str = "", truncated: bool = False, finish_reason: str = ""):
        self.content = content
        self.tokens_used = tokens_used
        self.model = model
        self.provider = provider
        self.truncated = truncated
        self.finish_reason = finish_reason


class BaseAIClient(ABC):
    """Base class for AI client implementations."""
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, Any]], 
                       model: str, temperature: float = 0.1, 
                       max_tokens: int = 64000) -> UnifiedResponse:
        """Make a chat completion request."""
        pass
    
    @abstractmethod
    def supports_vision(self, model: str) -> bool:
        """Check if model supports vision inputs."""
        pass


class OpenAIClient(BaseAIClient):
    """OpenAI client wrapper."""
    
    def __init__(self, api_key: str, timeout: float = 90.0, max_retries: int = 3):
        if not openai:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        # Try with all parameters first, fall back if there's an issue
        try:
            self.client = openai.OpenAI(
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries
            )
        except TypeError as e:
            if 'proxies' in str(e):
                # Fallback for compatibility issues with httpx/OpenAI versions
                print("Warning: OpenAI client initialization issue detected, using fallback initialization")
                self.client = openai.OpenAI(api_key=api_key)
            else:
                raise
    
    def chat_completion(self, messages: List[Dict[str, Any]], 
                       model: str, temperature: float = 0.1, 
                       max_tokens: int = 64000) -> UnifiedResponse:
        """Make OpenAI chat completion request."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0

            # Check for truncation
            finish_reason = response.choices[0].finish_reason if response.choices else ""
            truncated = finish_reason == "length"

            return UnifiedResponse(
                content=content,
                tokens_used=tokens_used,
                model=model,
                provider="openai",
                truncated=truncated,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")
    
    def supports_vision(self, model: str) -> bool:
        """Check if OpenAI model supports vision."""
        vision_models = ["gpt-4o", "gpt-4-vision-preview", "gpt-4o-mini"]
        return any(vm in model for vm in vision_models)


class AnthropicClient(BaseAIClient):
    """Anthropic client wrapper."""
    
    def __init__(self, api_key: str, timeout: float = 180.0):
        if not anthropic:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")

        self.client = anthropic.Anthropic(
            api_key=api_key,
            timeout=timeout
        )
    
    def chat_completion(self, messages: List[Dict[str, Any]], 
                       model: str, temperature: float = 0.1, 
                       max_tokens: int = 64000) -> UnifiedResponse:
        """Make Anthropic chat completion request."""
        try:
            # Convert OpenAI format to Anthropic format
            anthropic_messages = self._convert_messages_to_anthropic(messages)
            
            response = self.client.messages.create(
                model=model,
                messages=anthropic_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else 0

            # Check for truncation
            stop_reason = response.stop_reason if hasattr(response, 'stop_reason') else ""
            truncated = stop_reason == "max_tokens"

            return UnifiedResponse(
                content=content,
                tokens_used=tokens_used,
                model=model,
                provider="anthropic",
                truncated=truncated,
                finish_reason=stop_reason
            )
            
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")
    
    def supports_vision(self, model: str) -> bool:
        """Check if Anthropic model supports vision."""
        vision_models = ["claude-3", "claude-sonnet", "claude-haiku", "claude-opus"]
        return any(vm in model for vm in vision_models)
    
    def _convert_messages_to_anthropic(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI message format to Anthropic format."""
        anthropic_messages = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # Skip system messages (handled separately in Anthropic)
            if role == "system":
                continue
            
            # Handle different content types
            if isinstance(content, str):
                # Simple text message
                anthropic_messages.append({
                    "role": role,
                    "content": content
                })
            elif isinstance(content, list):
                # Multi-modal content (text + images)
                anthropic_content = []
                
                for item in content:
                    if item.get("type") == "text":
                        anthropic_content.append({
                            "type": "text",
                            "text": item.get("text", "")
                        })
                    elif item.get("type") == "image_url":
                        # Convert image URL to Anthropic format
                        image_url = item.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:image"):
                            # Extract base64 data
                            media_type, base64_data = image_url.split(",", 1)
                            image_format = media_type.split(";")[0].split("/")[1]
                            
                            anthropic_content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": f"image/{image_format}",
                                    "data": base64_data
                                }
                            })
                
                if anthropic_content:
                    anthropic_messages.append({
                        "role": role,
                        "content": anthropic_content
                    })
        
        return anthropic_messages



class UnifiedAIClient:
    """Unified client that can work with both OpenAI and Anthropic models."""
    
    def __init__(self, openai_api_key: str = "", anthropic_api_key: str = "",
                 timeout: float = 180.0, max_retries: int = 3):
        self.clients = {}

        # Initialize available clients
        if openai_api_key:
            try:
                self.clients["openai"] = OpenAIClient(openai_api_key, timeout, max_retries)
            except ImportError as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")

        if anthropic_api_key:
            try:
                self.clients["anthropic"] = AnthropicClient(anthropic_api_key, timeout)
            except ImportError as e:
                print(f"Warning: Could not initialize Anthropic client: {e}")
    
    def chat_completion(self, messages: List[Dict[str, Any]], 
                       model: str, temperature: float = 0.1, 
                       max_tokens: int = 64000, provider: str = None) -> UnifiedResponse:
        """Make a chat completion request using the appropriate provider."""
        if provider is None:
            raise ValueError(f"Provider must be specified for model: {model}")
        
        if provider not in self.clients:
            raise RuntimeError(f"No {provider} client available. Check API keys.")
        
        client = self.clients[provider]
        return client.chat_completion(messages, model, temperature, max_tokens)
    
    def get_available_providers(self) -> List[str]:
        """Get all available providers."""
        return list(self.clients.keys())
    
    def supports_vision(self, model: str) -> bool:
        """Check if model supports vision (basic implementation)."""
        # Most modern models support vision, but you can customize this logic
        vision_models = ["gpt-4", "gpt-4o", "claude"]
        return any(pattern in model.lower() for pattern in vision_models)
# config.py
"""
OCR Processor Configuration
Simple, centralized configuration management
"""

import os
from dataclasses import dataclass

if not os.getenv("SPACE_ID"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

@dataclass
class Config:
    """Centralized configuration for OCR processing."""

    # Vision OCR Settings
    vision_corruption_threshold: float = 0.1
    max_vision_calls_per_doc: int = 100
    dpi: int = 300  

    # Main Agent Settings (Content Formatting)
    main_model: str = "claude-sonnet-4-5-20250929"        # Main processing model (content formatting, etc.)
    main_provider: str = "anthropic"                      # Provider for main model
    main_temperature: float = 0.0                         # Temperature for main processing (balanced creativity/consistency)
    main_max_tokens: int = 16384                          # Max tokens for main processing
    
    # Vision OCR Agent Settings
    vision_model: str = "claude-sonnet-4-5-20250929"                          # Vision OCR model (image text extraction)  
    vision_provider: str = "anthropic"                       # Provider for vision model
    vision_temperature: float = 0.0                       # Temperature for vision OCR (low for accurate extraction)
    vision_max_tokens: int = 4096                         # Max tokens for vision OCR (shorter responses needed)

    # Evaluation Agent Settings  
    evaluation_model: str = "gpt-4o-mini"                 # Evaluation model (faster/cheaper for quality checks)
    evaluation_provider: str = "openai"                   # Provider for evaluation model
    evaluation_temperature: float = 0.1                   # Temperature for evaluation (low for objective analysis)
    evaluation_max_tokens: int = 8192                     # Max tokens for evaluation
    
    # Corruption Detection Agent Settings
    corruption_model: str = "claude-sonnet-4-5-20250929"  # Corruption detection model (text quality analysis)
    corruption_provider: str = "anthropic"                # Provider for corruption model
    corruption_temperature: float = 0.0                   # Temperature for corruption analysis (deterministic JSON)
    corruption_max_tokens: int = 500                      # Max tokens for corruption analysis (short responses)
    
    # Anthropic Settings (used for evaluation comparison)
    anthropic_evaluator_model: str = "claude-sonnet-4-20250514"  # Anthropic model for document evaluation
    anthropic_evaluator_provider: str = "anthropic"        # Provider for anthropic evaluator
    anthropic_evaluator_temperature: float = 0.0           # Temperature for Anthropic evaluation calls
    anthropic_evaluator_max_tokens: int = 8192             # Maximum tokens for Anthropic evaluation
    
    # Agent Control Settings
    enable_content_formatting_agent: bool = os.getenv("ENABLE_CONTENT_FORMATTING_AGENT", "true").lower() == "true"
    enable_summary_agent: bool = os.getenv("ENABLE_SUMMARY_AGENT", "false").lower() == "true"
    use_parallel_vision: bool = os.getenv("USE_PARALLEL_VISION", "true").lower() == "true"  # Enable parallel vision processing

    # Download Settings
    use_local_downloads_directory: bool = os.getenv("USE_LOCAL_DOWNLOADS_DIRECTORY", "true").lower() == "true"  # Change to false for HuggingFace deployment

    # Evaluation Settings
    use_files_api_for_evaluation: bool = False  # Files API doesn't support PDFs for vision (only individual images)
    compare_evaluation_methods: bool = True  # Run both OpenAI and Anthropic for comparison (base64 mode)
    
    # Debug Settings
    debug_ocr_pipeline: bool = os.getenv("DEBUG_OCR_PIPELINE", "false").lower() == "true"  # Enable detailed OCR stage logging

    # Unified AI Client Settings
    @property 
    def unified_client(self):
        """Get unified AI client instance (lazy initialization)."""
        if not hasattr(self, '_unified_client'):
            from unified_client import UnifiedAIClient
            self._unified_client = UnifiedAIClient(
                openai_api_key=self.openai_api_key,
                anthropic_api_key=self.anthropic_api_key
            )
        return self._unified_client

    # Helper methods for getting model-specific settings
    def get_model_for_task(self, task: str) -> str:
        """Get the appropriate model for a specific task."""
        task_models = {
            "main": self.main_model,
            "vision": self.vision_model,
            "evaluation": self.evaluation_model,
            "corruption": self.corruption_model,
            "anthropic_evaluation": self.anthropic_evaluator_model
        }
        return task_models.get(task, self.main_model)
    
    def get_provider_for_task(self, task: str) -> str:
        """Get the appropriate provider for a specific task."""
        task_providers = {
            "main": self.main_provider,
            "vision": self.vision_provider,
            "evaluation": self.evaluation_provider,
            "corruption": self.corruption_provider,
            "anthropic_evaluation": self.anthropic_evaluator_provider
        }
        return task_providers.get(task, self.main_provider)
    
    def get_temperature_for_task(self, task: str) -> float:
        """Get the appropriate temperature for a specific task."""
        task_temperatures = {
            "main": self.main_temperature,
            "vision": self.vision_temperature,
            "evaluation": self.evaluation_temperature,
            "corruption": self.corruption_temperature,
            "anthropic_evaluation": self.anthropic_evaluator_temperature
        }
        return task_temperatures.get(task, self.main_temperature)
    
    def get_max_tokens_for_task(self, task: str) -> int:
        """Get the appropriate max tokens for a specific task."""
        task_tokens = {
            "main": self.main_max_tokens,
            "vision": self.vision_max_tokens,
            "evaluation": self.evaluation_max_tokens,
            "corruption": self.corruption_max_tokens,
            "anthropic_evaluation": self.anthropic_evaluator_max_tokens
        }
        return task_tokens.get(task, self.main_max_tokens)

    # Backward compatibility properties (deprecated - use new unified system)
    @property
    def temperature(self) -> float:
        """Legacy property for backward compatibility."""
        return self.main_temperature
    
    @property
    def max_output_tokens(self) -> int:
        """Legacy property for backward compatibility."""
        return self.main_max_tokens
        
    @property
    def openai_model(self) -> str:
        """Legacy property for backward compatibility."""
        return self.main_model
        
    @property
    def openai_vision_model(self) -> str:
        """Legacy property for backward compatibility."""
        return self.vision_model
        
    @property
    def openai_evaluation_model(self) -> str:
        """Legacy property for backward compatibility."""
        return self.evaluation_model
        
    @property
    def openai_corruption_model(self) -> str:
        """Legacy property for backward compatibility."""
        return self.corruption_model
        
    @property
    def anthropic_model(self) -> str:
        """Legacy property for backward compatibility."""
        return self.anthropic_evaluator_model
        
    @property
    def anthropic_temperature(self) -> float:
        """Legacy property for backward compatibility."""
        return self.anthropic_evaluator_temperature
        
    @property
    def anthropic_max_tokens(self) -> int:
        """Legacy property for backward compatibility."""
        return self.anthropic_evaluator_max_tokens

    # API Keys
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        return os.getenv("OPENAI_API_KEY", "")
    
    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment."""
        return os.getenv("ANTHROPIC_API_KEY", "")

    @property
    def tally_form_id(self) -> str:
        """Get Tally form ID from environment."""
        return os.getenv("TALLY_FORM_ID", "")

    def validate(self) -> bool:
        """Validate configuration settings."""
        # OpenAI API key is now optional - only required if using vision OCR
        return True

config = Config()

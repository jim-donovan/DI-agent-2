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

    openai_model: str = "gpt-4o"
    temperature: float = 0.1
    max_output_tokens: int = 16384  # GPT-4o maximum completion tokens
    enable_content_formatting_agent: bool = os.getenv("ENABLE_CONTENT_FORMATTING_AGENT", "true").lower() == "true"
    
    # Anthropic Settings for Evaluation  
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_temperature: float = 0.0
    anthropic_max_tokens: int = 8192
    
    # Evaluation Settings
    use_files_api_for_evaluation: bool = False  # Files API doesn't support PDFs for vision (only individual images)
    compare_evaluation_methods: bool = True  # Run both OpenAI and Anthropic for comparison (base64 mode)
    
    # Debug Settings
    debug_ocr_pipeline: bool = os.getenv("DEBUG_OCR_PIPELINE", "false").lower() == "true"  # Enable detailed OCR stage logging
    
    # Vision prompt for OCR - Enhanced for complex tables
    vision_prompt: str = """You are an OCR extraction model. 
Your ONLY task is to extract all visible text, numbers, and symbols from the provided image **exactly as they appear**.

Rules:
- Output raw text only. Do NOT add commentary, labels, or formatting (e.g., no Markdown, no code blocks).
- Copy text, punctuation, capitalization, line breaks, and spacing exactly as shown. 
  Do not collapse multiple spaces, tabs, or blank lines.
- Preserve bullets, dashes, special characters, and symbols in their original form.
- **Do not omit any text.**

CRITICAL TABLE EXTRACTION RULES:
- For tables with nested/multi-level headers: Extract headers in hierarchical order (top-level first, then sub-headers)
- Preserve the visual alignment and relationships between columns and rows
- For merged cells or spanning headers: Include the header text at the start of each relevant section
- Extract tables row by row, maintaining column separation with consistent spacing or tab characters
- Include ALL cells even if empty - represent empty cells with appropriate spacing
- For complex nested tables: First extract all column headers (including nested levels), then extract data rows
- Maintain the association between row labels and their corresponding values across all columns

Example for nested table headers:
                Plan A          Plan B
            Cost | Coverage | Cost | Coverage
Service 1   $10  |   80%    | $15  |   90%
Service 2   $20  |   70%    | $25  |   85%

If a character or symbol is unclear or corrupted, replace it with `�` without guessing.
If multiple languages or scripts appear, reproduce them exactly as written without translation.
Do not summarize, interpret, normalize, or reformat in any way.

Your entire output must consist of the extracted text only."""

    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        return os.getenv("OPENAI_API_KEY", "")
    
    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment."""
        return os.getenv("ANTHROPIC_API_KEY", "")

    def validate(self) -> bool:
        """Validate configuration settings."""
        # OpenAI API key is now optional - only required if using vision OCR
        return True

config = Config()

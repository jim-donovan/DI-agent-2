"""
Prompts module for loading and managing AI model prompts
"""

from .prompt_loader import PromptLoader

# Global prompt loader instance
prompts = PromptLoader()

# Convenience functions for common prompts
def get_vision_ocr_prompt() -> str:
    """Get the vision OCR prompt."""
    return prompts.get("vision_ocr")

def get_corruption_analysis_prompt() -> str:
    """Get the corruption analysis prompt."""  
    return prompts.get("corruption_analysis")

def get_content_formatting_prompt() -> str:
    """Get the content formatting prompt."""
    return prompts.get("content_formatting")

def get_evaluation_prompt() -> str:
    """Get the evaluation prompt."""
    return prompts.get("evaluation")
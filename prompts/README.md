# Prompts Directory

This directory contains AI model prompts organized as individual text files for easy management, version control, and editing.

## Structure

- `*.txt` - Individual prompt files
- `prompt_loader.py` - Utility for loading prompts with caching
- `__init__.py` - Convenience functions for common prompts

## Usage

```python
from prompts import get_vision_ocr_prompt

# Get a specific prompt
prompt = get_vision_ocr_prompt()

# Or use the loader directly
from prompts import prompts
prompt = prompts.get("vision_ocr")
```

## Available Prompts

- `vision_ocr.txt` - Vision OCR extraction prompt for accurate text extraction from images
- `corruption_analysis.txt` - Corruption detection prompt (planned)
- `content_formatting.txt` - Content formatting prompt (planned)
- `evaluation.txt` - Document evaluation prompt (planned)

## Benefits

1. **Separation of Concerns** - Prompts are content, not configuration
2. **Easy Editing** - Edit prompts in dedicated files without touching code
3. **Version Control** - Track prompt changes separately from code changes
4. **Reusability** - Prompts can be shared across different agents
5. **Caching** - Prompts are loaded once and cached for performance

## Adding New Prompts

1. Create a new `.txt` file in this directory
2. Add a convenience function in `__init__.py` if needed
3. Use `prompts.get("your_prompt_name")` in your code
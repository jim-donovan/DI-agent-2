"""
Prompt Loader Utility
Loads AI model prompts from text files with caching
"""

import os
from pathlib import Path
from typing import Dict, Optional


class PromptLoader:
    """Loads and caches prompts from text files."""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files. If None, uses ./prompts
        """
        if prompts_dir is None:
            # Default to prompts directory relative to this file
            self.prompts_dir = Path(__file__).parent
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self._cache: Dict[str, str] = {}
        
    def get(self, prompt_name: str, force_reload: bool = False) -> str:
        """
        Get a prompt by name.
        
        Args:
            prompt_name: Name of the prompt (without .txt extension)
            force_reload: If True, reload from file even if cached
            
        Returns:
            The prompt content as a string
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            IOError: If prompt file can't be read
        """
        # Check cache first (unless forcing reload)
        if not force_reload and prompt_name in self._cache:
            return self._cache[prompt_name]
        
        # Load from file
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Cache the content
            self._cache[prompt_name] = content
            return content
            
        except Exception as e:
            raise IOError(f"Failed to read prompt file {prompt_file}: {e}")
    
    def list_available_prompts(self) -> list:
        """Get list of available prompt names."""
        if not self.prompts_dir.exists():
            return []
        
        prompt_files = list(self.prompts_dir.glob("*.txt"))
        return [f.stem for f in prompt_files]
    
    def reload_all(self) -> None:
        """Clear cache and reload all prompts."""
        self._cache.clear()
        
    def preload_all(self) -> None:
        """Preload all available prompts into cache."""
        for prompt_name in self.list_available_prompts():
            try:
                self.get(prompt_name)
            except (FileNotFoundError, IOError):
                # Skip prompts that can't be loaded
                continue
    
    def add_prompt(self, name: str, content: str) -> None:
        """
        Add a prompt programmatically (useful for testing).
        
        Args:
            name: Prompt name
            content: Prompt content
        """
        self._cache[name] = content
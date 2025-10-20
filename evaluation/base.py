"""
Base evaluator class for document quality assessment.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

class Recommendation(Enum):
    """Evaluation recommendation levels."""
    ACCEPT = "ACCEPT"
    REVIEW = "REVIEW" 
    REJECT = "REJECT"

@dataclass
class EvaluationResult:
    """Structured result from document evaluation."""
    missing_items: List[Dict[str, Any]]
    added_items: List[Dict[str, Any]]
    overall_score: float
    recommendation: Recommendation
    summary: str
    raw_response: str = ""
    evaluator_name: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "missing_items": self.missing_items,
            "added_items": self.added_items,
            "overall_score": self.overall_score,
            "recommendation": self.recommendation.value,
            "summary": self.summary,
            "evaluator_name": self.evaluator_name,
            "error": self.error
        }

class BaseEvaluator(ABC):
    """Abstract base class for document evaluators."""
    
    def __init__(self, name: str, logger=None):
        """
        Initialize evaluator.
        
        Args:
            name: Name of the evaluator
            logger: Optional logger instance
        """
        self.name = name
        self.logger = logger
        
    @abstractmethod
    def evaluate(self, 
                 markdown_content: str,
                 pdf_images: List[Any],
                 original_text: str = "",
                 context: Dict[str, Any] = None) -> EvaluationResult:
        """
        Evaluate document quality.
        
        Args:
            markdown_content: Processed markdown text
            pdf_images: List of PDF page images
            original_text: Original extracted text
            context: Additional context
            
        Returns:
            EvaluationResult object
        """
        pass
    
    def log(self, message: str, level: str = "info"):
        """Log a message if logger is available."""
        if self.logger:
            if level == "error":
                self.logger.log_error(message)
            elif level == "success":
                self.logger.log_success(message)
            else:
                self.logger.info(message)  # Fixed: use info() not log_info()
    
    def parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """
        Parse evaluation response into structured format.
        
        Args:
            response: Raw response string
            
        Returns:
            Parsed evaluation dictionary
        """
        import json
        import re
        
        # Try to extract JSON from the response
        try:
            # First try parsing the entire response as JSON
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        try:
            # Look for JSON in code blocks
            json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_block_match:
                return json.loads(json_block_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass

        try:
            # Look for JSON block anywhere in response (match balanced braces)
            # Find first { and try to parse from there
            start_idx = response.find('{')
            if start_idx != -1:
                # Try to find matching closing brace
                brace_count = 0
                for i, char in enumerate(response[start_idx:], start=start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_str = response[start_idx:i+1]
                            return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError, ValueError):
            pass
        
        # Fallback parsing logic
        result = {
            "missing_items": [],
            "added_items": [],
            "overall_score": 0.0,
            "recommendation": "REVIEW",
            "summary": "Unable to parse evaluation response"
        }
        
        # Try to extract score
        score_match = re.search(r'overall_score["\s:]+(\d+\.?\d*)', response, re.IGNORECASE)
        if score_match:
            result["overall_score"] = float(score_match.group(1))
        
        # Try to extract recommendation
        for rec in ["ACCEPT", "REVIEW", "REJECT"]:
            if rec in response.upper():
                result["recommendation"] = rec
                break
        
        return result
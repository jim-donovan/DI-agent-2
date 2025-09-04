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
            # Look for JSON block in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
        except (json.JSONDecodeError, AttributeError):
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
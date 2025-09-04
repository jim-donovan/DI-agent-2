"""
Evaluation module for document quality assessment.
Provides modular evaluation using OpenAI and Anthropic models.
"""

from .base import BaseEvaluator, EvaluationResult
from .openai_evaluator import OpenAIEvaluator
from .anthropic_evaluator import AnthropicEvaluator
from .comparator import EvaluationComparator
from .prompts import EVALUATION_SYSTEM_PROMPT

__all__ = [
    'BaseEvaluator',
    'EvaluationResult',
    'OpenAIEvaluator', 
    'AnthropicEvaluator',
    'EvaluationComparator',
    'EVALUATION_SYSTEM_PROMPT'
]
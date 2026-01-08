"""
Evaluation comparison and scoring module.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from .base import EvaluationResult, Recommendation

@dataclass
class ComparisonResult:
    """Result of comparing two evaluations."""
    openai_result: EvaluationResult
    anthropic_result: Optional[EvaluationResult]
    agreement_score: float
    final_score: float
    final_recommendation: Recommendation
    comparison_summary: str
    detailed_comparison: Dict[str, Any]

class EvaluationComparator:
    """Compare and analyze multiple evaluation results."""
    
    def __init__(self, logger=None):
        """Initialize comparator with optional logger."""
        self.logger = logger
        
    def compare(self,
                openai_result: EvaluationResult,
                anthropic_result: Optional[EvaluationResult] = None) -> ComparisonResult:
        """
        Compare evaluation results from different evaluators.
        
        Args:
            openai_result: OpenAI evaluation result
            anthropic_result: Optional Anthropic evaluation result
            
        Returns:
            ComparisonResult with analysis
        """
        if not anthropic_result:
            # Single evaluation - return OpenAI result
            return ComparisonResult(
                openai_result=openai_result,
                anthropic_result=None,
                agreement_score=100.0,
                final_score=openai_result.overall_score,
                final_recommendation=openai_result.recommendation,
                comparison_summary="Single evaluation (OpenAI only)",
                detailed_comparison={"single_evaluation": True}
            )
        
        # Compare both evaluations
        agreement_score = self._calculate_agreement(openai_result, anthropic_result)
        final_score = self._calculate_final_score(openai_result, anthropic_result)
        final_recommendation = self._determine_final_recommendation(
            openai_result, anthropic_result, agreement_score
        )
        
        # Generate detailed comparison
        detailed_comparison = self._generate_detailed_comparison(
            openai_result, anthropic_result
        )
        
        # Generate summary
        comparison_summary = self._generate_comparison_summary(
            openai_result, anthropic_result, agreement_score
        )
        
        return ComparisonResult(
            openai_result=openai_result,
            anthropic_result=anthropic_result,
            agreement_score=agreement_score,
            final_score=final_score,
            final_recommendation=final_recommendation,
            comparison_summary=comparison_summary,
            detailed_comparison=detailed_comparison
        )
    
    def _calculate_agreement(self,
                            result1: EvaluationResult,
                            result2: EvaluationResult) -> float:
        """Calculate average score between two evaluations."""
        # Simple average of the two scores
        return (result1.overall_score + result2.overall_score) / 2
    
    def _are_recommendations_adjacent(self, rec1: Recommendation, rec2: Recommendation) -> bool:
        """Check if two recommendations are adjacent (e.g., ACCEPT and REVIEW)."""
        order = [Recommendation.ACCEPT, Recommendation.REVIEW, Recommendation.REJECT]
        idx1 = order.index(rec1)
        idx2 = order.index(rec2)
        return abs(idx1 - idx2) == 1
    
    def _calculate_item_overlap(self, items1: List[Dict], items2: List[Dict]) -> float:
        """Calculate overlap percentage between two lists of items."""
        if not items1 and not items2:
            return 100.0
        if not items1 or not items2:
            return 0.0
        
        # Extract content for comparison
        content1 = {item.get("content", "").lower().strip() for item in items1}
        content2 = {item.get("content", "").lower().strip() for item in items2}
        
        # Calculate Jaccard similarity
        intersection = len(content1.intersection(content2))
        union = len(content1.union(content2))
        
        if union == 0:
            return 100.0
        
        return (intersection / union) * 100
    
    def _calculate_final_score(self,
                               result1: EvaluationResult,
                               result2: EvaluationResult) -> float:
        """Calculate final score as simple average."""
        return (result1.overall_score + result2.overall_score) / 2
    
    def _determine_final_recommendation(self,
                                       result1: EvaluationResult,
                                       result2: EvaluationResult,
                                       average_score: float) -> Recommendation:
        """Determine final recommendation based on average score."""
        # Use the average score to determine recommendation
        if average_score >= 90:
            return Recommendation.ACCEPT
        elif average_score >= 70:
            return Recommendation.REVIEW
        else:
            return Recommendation.REJECT
    
    def _generate_detailed_comparison(self,
                                     result1: EvaluationResult,
                                     result2: EvaluationResult) -> Dict[str, Any]:
        """Generate detailed comparison data."""
        return {
            "score_difference": abs(result1.overall_score - result2.overall_score),
            "recommendation_match": result1.recommendation == result2.recommendation,
            "missing_items_comparison": {
                "openai_count": len(result1.missing_items),
                "anthropic_count": len(result2.missing_items),
                "overlap_percentage": self._calculate_item_overlap(
                    result1.missing_items, result2.missing_items
                )
            },
            "added_items_comparison": {
                "openai_count": len(result1.added_items),
                "anthropic_count": len(result2.added_items),
                "overlap_percentage": self._calculate_item_overlap(
                    result1.added_items, result2.added_items
                )
            }
        }
    
    def _generate_comparison_summary(self,
                                    result1: EvaluationResult,
                                    result2: EvaluationResult,
                                    average_score: float) -> str:
        """Generate human-readable comparison summary."""
        summary = f"Average: {average_score:.1f}/100\n"
        summary += f"OpenAI Score: {result1.overall_score:.1f} ({result1.recommendation.value})\n"
        summary += f"Anthropic Score: {result2.overall_score:.1f} ({result2.recommendation.value})\n"

        if result1.recommendation != result2.recommendation:
            summary += "⚠️ Evaluators disagree on recommendation\n"

        return summary
"""
Refactored Checker Agent using modular evaluation system.
This is a cleaner, more maintainable version using the evaluation module.
"""

import time
from typing import Dict, Any, Optional

from agent_base import BaseAgent, AgentResponse
from logger import ProcessingLogger
from config import config
from api_client import APIClient

# Import modular evaluation components
from evaluation import (
    OpenAIEvaluator,
    AnthropicEvaluator,
    EvaluationComparator
)

class CheckerAgent(BaseAgent):
    """Agent specialized for quality evaluation using modular evaluators."""
    
    def __init__(self, logger: ProcessingLogger, api_client: Optional[APIClient] = None):
        """Initialize checker agent with modular evaluators.
        
        Args:
            logger: Logger instance for recording activities
            api_client: Optional APIClient instance (will be created if not provided)
        """
        super().__init__("checker_agent", logger, api_client=api_client)
        
        # Initialize evaluators with the API client
        self.openai_evaluator = OpenAIEvaluator(
            self.api_client,
            task="evaluation",
            logger=logger
        )
        
        # Initialize Anthropic evaluator if API key is configured
        self.anthropic_evaluator = None
        if config.anthropic_api_key:
            try:
                self.anthropic_evaluator = AnthropicEvaluator(
                    self.api_client,
                    task="anthropic_evaluation",
                    logger=logger
                )
                self.logger.log("✅ Anthropic evaluator initialized with task-based routing")
            except Exception as e:
                self.logger.log_error(f"Failed to initialize Anthropic evaluator: {e}")
                import traceback
                self.logger.log_error(f"Traceback: {traceback.format_exc()}")
        else:
            self.logger.log_warning("No Anthropic API key found - dual evaluation disabled")
        
        self.comparator = EvaluationComparator(logger=logger)
    
    def get_system_prompt(self) -> str:
        """Get system prompt (maintained for compatibility)."""
        from evaluation.prompts import EVALUATION_SYSTEM_PROMPT
        return EVALUATION_SYSTEM_PROMPT
    
    def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResponse:
        """
        Evaluate markdown output against original PDF content.
        
        Args:
            input_data: Dictionary containing markdown_content, pdf_images, original_text
            context: Additional context including document_name
            
        Returns:
            AgentResponse with evaluation results
        """
        start_time = time.time()
        context = context or {}
        
        try:
            # Extract inputs
            if isinstance(input_data, dict):
                markdown_content = input_data.get("markdown_content", "")
                pdf_images = input_data.get("pdf_images", [])
                original_text = input_data.get("original_text", "")
            else:
                markdown_content = str(input_data)
                pdf_images = []
                original_text = ""
            
            document_name = context.get("document_name", "Unknown Document")
            
            # Log evaluation request
            self.add_memory("evaluation_request", {
                "document_name": document_name,
                "markdown_length": len(markdown_content),
                "original_text_length": len(original_text),
                "pdf_pages": len(pdf_images)
            })
            
            # Run OpenAI evaluation (reduced logging)
            openai_result = self.openai_evaluator.evaluate(
                markdown_content=markdown_content,
                pdf_images=pdf_images,
                original_text=original_text,
                context=context
            )
            
            # Run Anthropic evaluation if available
            anthropic_result = None
            if self.anthropic_evaluator and config.compare_evaluation_methods:
                self.logger.log("Running Anthropic evaluation for comparison...")
                # Run Anthropic evaluation (reduced logging)
                anthropic_result = self.anthropic_evaluator.evaluate(
                    markdown_content=markdown_content,
                    pdf_images=pdf_images,
                    original_text=original_text,
                    context=context
                )
            else:
                if not self.anthropic_evaluator:
                    self.logger.log_warning("Anthropic evaluator not initialized - single evaluation mode")
                elif not config.compare_evaluation_methods:
                    self.logger.log("Dual evaluation disabled in config - single evaluation mode")
            
            # Compare evaluations
            comparison = self.comparator.compare(openai_result, anthropic_result)
            
            # Format evaluation report
            evaluation_report = self._format_evaluation_report(comparison, context)
            
            # Add to memory
            self.add_memory("evaluation_result", {
                "final_score": comparison.final_score,
                "final_recommendation": comparison.final_recommendation.value,
                "agreement_score": comparison.agreement_score,
                "openai_score": openai_result.overall_score,
                "anthropic_score": anthropic_result.overall_score if anthropic_result else None
            })
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create structured evaluation result
            structured_result = {
                "overall_score": comparison.final_score,
                "recommendation": comparison.final_recommendation.value,
                "evaluation_report": evaluation_report,
                "openai_evaluation": openai_result.to_dict(),
                "anthropic_evaluation": anthropic_result.to_dict() if anthropic_result else None,
                "agreement_score": comparison.agreement_score if anthropic_result else 100.0
            }
            
            return AgentResponse(
                success=True,
                content=structured_result,  # Return structured data as primary content
                confidence=comparison.final_score / 100.0,
                metadata={
                    "processing_time": processing_time,
                    "evaluators_used": ["OpenAI"] + (["Anthropic"] if anthropic_result else []),
                    "final_score": comparison.final_score,
                    "final_recommendation": comparison.final_recommendation.value
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.log_error(f"Evaluation failed: {str(e)}")
            return AgentResponse(
                success=False,
                content="",  # Changed from 'data=None'
                confidence=0.0,
                error_message=str(e),  # Changed from 'error'
                metadata={"processing_time": time.time() - start_time},
                processing_time=time.time() - start_time
            )
    
    def _format_evaluation_report(self, comparison, context=None) -> str:
        """Format evaluation report for display."""
        report = []
        report.append("=" * 80)
        report.append("📋 QUALITY EVALUATION REPORT")
        report.append("=" * 80)
        
        # Overall results
        report.append(f"\n📊 Final Score: {comparison.final_score:.1f}/100")
        report.append(f"✅ Recommendation: {comparison.final_recommendation.value}")
        
        if comparison.anthropic_result:
            report.append(f"🤝 Agreement Level: {comparison.agreement_score:.1f}%")
            report.append("\n" + "=" * 40)
            report.append("EVALUATOR COMPARISON")
            report.append("=" * 40)
            report.append(comparison.comparison_summary)
        
        # OpenAI Evaluation
        report.append("\n" + "=" * 40)
        report.append("OPENAI EVALUATION")
        report.append("=" * 40)
        report.append(f"Score: {comparison.openai_result.overall_score:.1f}/100")
        report.append(f"Recommendation: {comparison.openai_result.recommendation.value}")
        
        if comparison.openai_result.missing_items:
            report.append(f"\nMissing Items: {len(comparison.openai_result.missing_items)}")
            # Show all items, not just first 5
            for i, item in enumerate(comparison.openai_result.missing_items, 1):
                report.append(f"  {i}. {item.get('content', 'N/A')}")
        
        if comparison.openai_result.added_items:
            report.append(f"\n➕ Added Items: {len(comparison.openai_result.added_items)}")
            # Show all items, not just first 5
            for i, item in enumerate(comparison.openai_result.added_items, 1):
                report.append(f"  {i}. {item.get('content', 'N/A')}")
        
        report.append(f"\nSummary: {comparison.openai_result.summary}")
        
        # Anthropic Evaluation (if available)
        if comparison.anthropic_result:
            report.append("\n" + "=" * 40)
            report.append("ANTHROPIC EVALUATION")
            report.append("=" * 40)
            report.append(f"Score: {comparison.anthropic_result.overall_score:.1f}/100")
            report.append(f"Recommendation: {comparison.anthropic_result.recommendation.value}")
            
            if comparison.anthropic_result.missing_items:
                report.append(f"\nMissing Items: {len(comparison.anthropic_result.missing_items)}")
                # Show all items with full content
                for i, item in enumerate(comparison.anthropic_result.missing_items, 1):
                    report.append(f"  {i}. {item.get('content', 'N/A')}")
            
            if comparison.anthropic_result.added_items:
                report.append(f"\n➕ Added Items: {len(comparison.anthropic_result.added_items)}")
                # Show all items with full content
                for i, item in enumerate(comparison.anthropic_result.added_items, 1):
                    report.append(f"  {i}. {item.get('content', 'N/A')}")
            
            report.append(f"\nSummary: {comparison.anthropic_result.summary}")
        
        # Add debug information at the end
        report.append("\n" + "=" * 40)
        report.append("DEBUG INFORMATION")
        report.append("=" * 40)
        
        # Add evaluator timing info if available
        if hasattr(self.openai_evaluator, '_last_evaluation_time'):
            report.append(f"OpenAI Evaluation Time: {self.openai_evaluator._last_evaluation_time:.2f}s")
        if hasattr(self.anthropic_evaluator, '_last_evaluation_time') and self.anthropic_evaluator:
            report.append(f"Anthropic Evaluation Time: {self.anthropic_evaluator._last_evaluation_time:.2f}s")
        
        # Add system debug info from context
        if context and 'debug_info' in context:
            debug_info = context['debug_info']
            if 'parallel_workers' in debug_info:
                report.append(f"Parallel Workers: {debug_info['parallel_workers']}")
            if 'initialization_info' in debug_info:
                report.append(f"System: {debug_info['initialization_info']}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
"""
OpenAI-based document evaluator.
"""

import base64
import json
import time
from typing import Dict, Any, List, Optional
from PIL import Image
import io

from .base import BaseEvaluator, EvaluationResult, Recommendation
from .prompts import EVALUATION_SYSTEM_PROMPT

class OpenAIEvaluator(BaseEvaluator):
    """Document evaluator using OpenAI models."""
    
    def __init__(self, openai_client, model: str = "gpt-4o-mini", logger=None):
        """
        Initialize OpenAI evaluator.
        
        Args:
            openai_client: OpenAI client instance
            model: Model to use for evaluation
            logger: Optional logger
        """
        super().__init__("OpenAI", logger)
        self.client = openai_client
        self.model = model
        
    def evaluate(self,
                 markdown_content: str,
                 pdf_images: List[Any],
                 original_text: str = "",
                 context: Dict[str, Any] = None) -> EvaluationResult:
        """
        Evaluate document using OpenAI.
        
        Args:
            markdown_content: Processed markdown
            pdf_images: PDF page images
            original_text: Original text
            context: Additional context
            
        Returns:
            EvaluationResult
        """
        try:
            # Prepare evaluation messages
            messages = self._prepare_messages(markdown_content, pdf_images, original_text)
            
            # Call OpenAI API
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            elapsed = time.time() - start_time
            # Store timing info for final output only
            self._last_evaluation_time = elapsed
            
            # Parse response
            response_text = response.choices[0].message.content
            parsed = self.parse_evaluation_response(response_text)
            
            # Create result
            return EvaluationResult(
                missing_items=parsed.get("missing_items", []),
                added_items=parsed.get("added_items", []),
                overall_score=float(parsed.get("overall_score", 0.0)),
                recommendation=Recommendation[parsed.get("recommendation", "REVIEW")],
                summary=parsed.get("summary", "Evaluation completed"),
                raw_response=response_text,
                evaluator_name=self.name
            )
            
        except Exception as e:
            self.log(f"❌ OpenAI evaluation error: {str(e)}", "error")
            return EvaluationResult(
                missing_items=[],
                added_items=[],
                overall_score=0.0,
                recommendation=Recommendation.REVIEW,
                summary="Evaluation failed",
                evaluator_name=self.name,
                error=str(e)
            )
    
    def _prepare_messages(self, 
                         markdown_content: str,
                         pdf_images: List[Any],
                         original_text: str) -> List[Dict[str, Any]]:
        """Prepare messages for OpenAI API."""
        messages = [
            {"role": "system", "content": EVALUATION_SYSTEM_PROMPT}
        ]
        
        # Build user message content
        content = []
        
        # Add markdown content
        content.append({
            "type": "text",
            "text": f"## Processed Markdown Content\n\n{markdown_content[:50000]}"
        })
        
        # Add PDF images if available
        if pdf_images:
            content.append({
                "type": "text", 
                "text": "\n\n## Original PDF Pages\nCompare the following PDF pages against the markdown:"
            })
            
            for i, image in enumerate(pdf_images[:10], 1):  # Limit to 10 pages
                image_base64 = self._image_to_base64(image)
                if image_base64:
                    content.append({
                        "type": "text",
                        "text": f"\n### PDF Page {i}"
                    })
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64,  # Already in data URL format
                            "detail": "high"
                        }
                    })
        
        # Add original text for reference if available
        if original_text:
            content.append({
                "type": "text",
                "text": f"\n\n## Original Extracted Text (for reference)\n\n{original_text[:10000]}"
            })
        
        messages.append({"role": "user", "content": content})
        return messages
    
    def _image_to_base64(self, image: Any) -> Optional[str]:
        """Convert image to base64 string."""
        try:
            if isinstance(image, str):
                # Handle data URL format: "data:image/png;base64,{data}"
                if image.startswith('data:'):
                    return image  # Return as-is for OpenAI API
                else:
                    # Raw base64, convert to data URL
                    return f"data:image/png;base64,{image}"
            elif isinstance(image, Image.Image):
                # PIL Image
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode()
            elif isinstance(image, bytes):
                # Raw bytes
                return base64.b64encode(image).decode()
            else:
                return None
        except Exception as e:
            self.log(f"Error converting image: {e}", "error")
            return None
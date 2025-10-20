"""
Anthropic-based document evaluator.
"""

import base64
import time
from typing import Dict, Any, List, Optional
from PIL import Image
import io

from .base import BaseEvaluator, EvaluationResult, Recommendation
from .prompts import ANTHROPIC_EVALUATION_SYSTEM_PROMPT

class AnthropicEvaluator(BaseEvaluator):
    """Document evaluator using Anthropic Claude models."""
    
    def __init__(self, api_client, task: str = "anthropic_evaluation", logger=None):
        """
        Initialize Anthropic evaluator.

        Args:
            api_client: APIClient instance for making API calls
            task: Task name for APIClient routing (defaults to "anthropic_evaluation")
            logger: Optional logger
        """
        super().__init__("Anthropic", logger)
        self.api_client = api_client
        self.task = task
        
    def evaluate(self,
                 markdown_content: str,
                 pdf_images: List[Any],
                 original_text: str = "",
                 context: Dict[str, Any] = None) -> EvaluationResult:
        """
        Evaluate document using Anthropic Claude.
        
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
            
            # Call Anthropic API through api_client
            start_time = time.time()

            response_text, tokens_used = self.api_client.make_api_call(
                messages=messages,
                temperature=0.1,
                max_tokens=8192,  # Increased from 4000 to match config
                task=self.task
            )

            elapsed = time.time() - start_time
            # Store timing info for final output only
            self._last_evaluation_time = elapsed

            # Parse response
            parsed = self.parse_evaluation_response(response_text)

            # Log if parsing failed
            if parsed.get("summary") == "Unable to parse evaluation response":
                self.log(f"⚠️ Failed to parse response. Full text: {response_text}", "error")

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
            self.log(f"❌ Anthropic evaluation error: {str(e)}", "error")
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
        """Prepare messages for Anthropic API."""
        content = []

        # Add system prompt as first message
        content.append({
            "type": "text",
            "text": ANTHROPIC_EVALUATION_SYSTEM_PROMPT + "\n\n---\n\n"
        })

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
                image_data = self._prepare_image_for_anthropic(image)
                if image_data:
                    content.append({
                        "type": "text",
                        "text": f"\n### PDF Page {i}"
                    })
                    content.append({
                        "type": "image",
                        "source": image_data
                    })

        # Add original text for reference
        if original_text:
            content.append({
                "type": "text",
                "text": f"\n\n## Original Extracted Text (for reference)\n\n{original_text[:10000]}"
            })

        # Add explicit instruction to return JSON
        content.append({
            "type": "text",
            "text": "\n\n**IMPORTANT: You must respond with ONLY valid JSON in the exact format specified above. Do not include any explanatory text before or after the JSON.**"
        })

        return [{"role": "user", "content": content}]
    
    def _prepare_image_for_anthropic(self, image: Any) -> Optional[Dict[str, str]]:
        """Prepare image for Anthropic API (with compression)."""
        try:
            # Convert to PIL Image if needed
            if isinstance(image, str):
                # Handle data URL format: "data:image/png;base64,{data}"
                if image.startswith('data:'):
                    # Extract base64 data from data URL
                    base64_data = image.split(',', 1)[1]
                else:
                    # Raw base64 string
                    base64_data = image
                
                try:
                    image_bytes = base64.b64decode(base64_data)
                    pil_image = Image.open(io.BytesIO(image_bytes))
                except Exception as e:
                    self.log(f"Error decoding base64 image: {e}", "error")
                    return None
            elif isinstance(image, bytes):
                pil_image = Image.open(io.BytesIO(image))
            elif isinstance(image, Image.Image):
                pil_image = image
            else:
                return None
            
            # Compress if needed (Anthropic has token limits)
            max_size = (1024, 1024)
            if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to JPEG for better compression
            buffer = io.BytesIO()
            if pil_image.mode in ('RGBA', 'LA', 'P'):
                # Convert to RGB if has transparency
                rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                rgb_image.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
                pil_image = rgb_image
            
            pil_image.save(buffer, format="JPEG", quality=85, optimize=True)
            image_data = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": image_data
            }
            
        except Exception as e:
            self.log(f"Error preparing image for Anthropic: {e}", "error")
            return None
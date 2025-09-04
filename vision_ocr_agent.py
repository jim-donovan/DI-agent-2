"""
Vision OCR Agent
Specialized agent for extracting text from images using GPT-4 Vision API
"""

import io
import base64
import time
from typing import Dict, Any
from PIL import Image

from agent_base import BaseAgent, AgentResponse
from logger import ProcessingLogger
from config import config
from utils import image_to_base64 as util_image_to_base64


class VisionOCRAgent(BaseAgent):
    """Agent specialized for vision-based OCR extraction."""
    
    def __init__(self, logger: ProcessingLogger, api_key: str):
        super().__init__("vision_ocr_agent", logger, api_key)
        self.extraction_strategies = {
            "standard": self._standard_extraction,
            "table_focused": self._table_focused_extraction,
            "form_focused": self._form_focused_extraction,
            "technical_doc": self._technical_document_extraction
        }
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for vision OCR."""
        return """Extract all visible text from the image. Preserve layout, structure, and formatting. Return only the extracted content without commentary."""
        
    def process(self, input_data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResponse:
        """Process image input and extract text."""
        start_time = time.time()
        context = context or {}
        
        try:
            # Extract inputs
            image = input_data.get("image")
            page_number = input_data.get("page_number", 1)
            extraction_strategy = context.get("strategy", "standard")
            
            if not image:
                return AgentResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    error_message="No image provided for OCR processing"
                )
            
            # Add to memory
            self.add_memory("ocr_request", {
                "page_number": page_number,
                "strategy": extraction_strategy,
                "image_size": f"{image.width}x{image.height}" if hasattr(image, 'width') else "unknown"
            })
            
            # Choose extraction strategy
            extraction_func = self.extraction_strategies.get(extraction_strategy, self._standard_extraction)
            
            # Execute extraction
            result = extraction_func(image, page_number, context)
            
            # Calculate confidence
            confidence = self._calculate_ocr_confidence(result["content"], image, context)
            
            # Raw OCR output logging removed - content available through UI tabs
            
            # Update state
            self.update_state(f"page_{page_number}_extracted", True)
            self.state.confidence_scores[f"page_{page_number}"] = confidence
            
            processing_time = time.time() - start_time
            
            response = AgentResponse(
                success=result["success"],
                content=result["content"],
                confidence=confidence,
                metadata={
                    "page_number": page_number,
                    "extraction_strategy": extraction_strategy,
                    "image_dimensions": f"{image.width}x{image.height}" if hasattr(image, 'width') else "unknown",
                    "estimated_word_count": len(result["content"].split()) if result["content"] else 0
                },
                reasoning_steps=result.get("reasoning_steps", []),
                tokens_used=result.get("tokens_used", 0),
                processing_time=processing_time
            )
            
            self.logger.log_success(f"Vision OCR completed for page {page_number} (confidence: {confidence:.2f})")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.log_error(f"Vision OCR failed: {str(e)}")
            return AgentResponse(
                success=False,
                content="",
                confidence=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _standard_extraction(self, image: Image.Image, page_number: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Standard OCR extraction approach."""
        reasoning_steps = ["Analyzing image for standard text extraction"]
        
        # Prepare image
        img_base64 = self._image_to_base64(image)
        
        # Build dynamic prompt based on context
        extraction_prompt = self._build_extraction_prompt("standard", context)
        
        reasoning_steps.append("Calling Vision API with standard extraction prompt")
        
        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt()
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": extraction_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, model="gpt-4o")
            content = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted text from image")
            
            return {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            reasoning_steps.append(f"Vision API call failed: {str(e)}")
            return {
                "success": False,
                "content": "",
                "reasoning_steps": reasoning_steps,
                "tokens_used": 0
            }
    
    def _table_focused_extraction(self, image: Image.Image, page_number: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced extraction for table-heavy documents with nested headers."""
        reasoning_steps = ["Analyzing image with enhanced table-focused extraction for nested structures"]
        
        img_base64 = self._image_to_base64(image)
        
        table_prompt = """Extract table content preserving structure. Identify column headers including nested headers. Maintain data alignment. Return only extracted content."""

        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt()
            },
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": table_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, model="gpt-4o")
            content = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted table-focused content")
            
            return {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            reasoning_steps.append(f"Table-focused extraction failed: {str(e)}")
            return {
                "success": False,
                "content": "",
                "reasoning_steps": reasoning_steps,
                "tokens_used": 0
            }
    
    def _form_focused_extraction(self, image: Image.Image, page_number: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced extraction for forms with checkboxes and fields."""
        reasoning_steps = ["Analyzing image with form-focused extraction"]
        
        img_base64 = self._image_to_base64(image)
        
        form_prompt = """Extract text, checkboxes, and form fields. Use [x] for checked, [ ] for unchecked. Return only extracted content."""

        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt()
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": form_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, model="gpt-4o")
            content = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted form-focused content")
            
            return {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            reasoning_steps.append(f"Form-focused extraction failed: {str(e)}")
            return {
                "success": False,
                "content": "",
                "reasoning_steps": reasoning_steps,
                "tokens_used": 0
            }
    
    def _technical_document_extraction(self, image: Image.Image, page_number: int, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced extraction for technical documents with diagrams and formulas."""
        reasoning_steps = ["Analyzing image with technical document extraction"]
        
        img_base64 = self._image_to_base64(image)
        
        technical_prompt = """Extract text including technical symbols, formulas, diagrams. Preserve mathematical notation and formatting. Return only extracted content."""

        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt()
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": technical_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, model="gpt-4o")
            content = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted technical content")
            
            return {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            reasoning_steps.append(f"Technical extraction failed: {str(e)}")
            return {
                "success": False,
                "content": "",
                "reasoning_steps": reasoning_steps,
                "tokens_used": 0
            }
    
    def _build_extraction_prompt(self, strategy: str, context: Dict[str, Any]) -> str:
        """Build dynamic extraction prompt based on strategy and context."""
        base_prompt = config.vision_prompt
        
        # Simple contextual hints
        if context.get("has_tables", False) or strategy == "table_focused":
            base_prompt += " Focus on table structure and header relationships."
        
        if context.get("has_forms", False):
            base_prompt += " Include all form elements and checkboxes."
            
        if context.get("quality_issues", False):
            base_prompt += " Mark unclear text with [?]."
            
        return base_prompt
    
    def _calculate_ocr_confidence(self, extracted_text: str, image: Image.Image, context: Dict[str, Any]) -> float:
        """Calculate confidence score for OCR extraction."""
        base_confidence = 0.85
        
        # Text length indicators
        if len(extracted_text) < 10:
            base_confidence -= 0.4
        elif len(extracted_text) > 1000:
            base_confidence += 0.05
            
        # Image quality factors
        if hasattr(image, 'width') and hasattr(image, 'height'):
            pixel_count = image.width * image.height
            if pixel_count < 100000:  # Low resolution
                base_confidence -= 0.2
            elif pixel_count > 1000000:  # High resolution
                base_confidence += 0.1
        
        # Context factors
        retry_count = context.get("retry_count", 0)
        if retry_count > 0:
            base_confidence -= (retry_count * 0.15)
            
        # Strategy-specific adjustments
        strategy = context.get("strategy", "standard")
        if strategy == "table_focused" and "table" in extracted_text.lower():
            base_confidence += 0.05
        if strategy == "form_focused" and any(marker in extracted_text for marker in ["[", "☑", "☐"]):
            base_confidence += 0.05
            
        return max(0.0, min(1.0, base_confidence))
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        return util_image_to_base64(image, format="PNG")
    
    def _clean_ai_metadata(self, text: str) -> str:
        """Remove AI metadata, apologies, and commentary from OCR output."""
        if not text:
            return text
            
        import re
        
        # Remove common AI metadata patterns
        patterns_to_remove = [
            r"I'm unable to.*?(?:\.|$)",
            r"I cannot.*?(?:\.|$)",
            r"If you have any.*?(?:\.|$)",
            r"feel free to ask.*?(?:\.|$)",
            r"I apologize.*?(?:\.|$)",
            r"Please note.*?(?:\.|$)",
            r"It appears.*?(?:\.|$)",
            r"Based on.*?(?:\.|$)",
            r"Here is.*?(?:\.|$)",
            r"The following.*?(?:\.|$)",
            r"As requested.*?(?:\.|$)",
            r"I'll extract.*?(?:\.|$)",
        ]
        
        cleaned_text = text
        for pattern in patterns_to_remove:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean up extra whitespace and empty lines
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
        cleaned_text = re.sub(r'^\s*\n', '', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    

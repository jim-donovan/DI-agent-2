"""
Vision OCR Agent
Specialized agent for extracting text from images using GPT-4 Vision API
"""

import time
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image

from agent_base import BaseAgent, AgentResponse
from logger import ProcessingLogger
from api_client import APIClient
from utils import image_to_base64 as util_image_to_base64
from prompts import get_vision_ocr_prompt
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class VisionOCRAgent(BaseAgent):
    """Agent specialized for vision-based OCR extraction."""

    def __init__(self, logger: ProcessingLogger, api_client: Optional[APIClient] = None):
        """Initialize the Vision OCR Agent.

        Args:
            logger: Logger instance for recording activities
            api_client: Optional APIClient instance (will be created if not provided)
        """
        super().__init__("vision_ocr_agent", logger, api_client=api_client)
        self.extraction_strategies = {
            "standard": self._standard_extraction,
            "table_focused": self._table_focused_extraction,
            "form_focused": self._form_focused_extraction,
            "technical_doc": self._technical_document_extraction
        }

        # Initialize OCR cache
        self.cache_dir = ".ocr_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_lock = threading.Lock()

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._executor_shutdown = False  # Track cleanup state

    def get_system_prompt(self) -> str:
        """Get the system prompt for vision OCR."""
        return """Extract ALL visible text from the image with complete accuracy.

CRITICAL REQUIREMENTS:
1. Read EVERY word - do not skip or truncate any text, even in complex layouts
2. For multi-column layouts: Read left column top-to-bottom, then right column top-to-bottom
3. Preserve bullets, lists, and formatting exactly as shown
4. Include ALL content - headers, body text, footers, fine print, URLs, phone numbers
5. If a line is cut off or continues, include the COMPLETE text

Return ONLY the extracted text - no commentary, no explanations, no metadata."""
        
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
                    "estimated_word_count": len(result["content"].split()) if result["content"] else 0,
                    "removed_metadata": result.get("removed_metadata", [])
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

        # Check cache first
        cache_key = self._get_cache_key(image, "standard", page_number)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            reasoning_steps.append("Retrieved result from cache")
            return cached_result

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
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, task="vision")
            content, removed_metadata = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted text from image")

            if removed_metadata:
                reasoning_steps.append(f"Cleaned {len(removed_metadata)} AI metadata fragment(s)")

            result = {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used,
                "removed_metadata": removed_metadata
            }

            # Save to cache
            self._save_to_cache(cache_key, result)

            return result
            
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

        # Check cache first
        cache_key = self._get_cache_key(image, "table_focused", page_number)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            reasoning_steps.append("Retrieved result from cache")
            return cached_result

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
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, task="vision")
            content, removed_metadata = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted table-focused content")

            if removed_metadata:
                reasoning_steps.append(f"Cleaned {len(removed_metadata)} AI metadata fragment(s)")

            result = {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used,
                "removed_metadata": removed_metadata
            }

            # Save to cache
            self._save_to_cache(cache_key, result)

            return result
            
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

        # Check cache first
        cache_key = self._get_cache_key(image, "form_focused", page_number)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            reasoning_steps.append("Retrieved result from cache")
            return cached_result

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
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, task="vision")
            content, removed_metadata = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted form-focused content")

            if removed_metadata:
                reasoning_steps.append(f"Cleaned {len(removed_metadata)} AI metadata fragment(s)")

            result = {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used,
                "removed_metadata": removed_metadata
            }

            # Save to cache
            self._save_to_cache(cache_key, result)

            return result
            
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

        # Check cache first
        cache_key = self._get_cache_key(image, "technical_doc", page_number)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            reasoning_steps.append("Retrieved result from cache")
            return cached_result

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
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            }
        ]
        
        try:
            content, tokens_used = self.make_api_call(messages, task="vision")
            content, removed_metadata = self._clean_ai_metadata(content)
            reasoning_steps.append("Successfully extracted technical content")

            if removed_metadata:
                reasoning_steps.append(f"Cleaned {len(removed_metadata)} AI metadata fragment(s)")

            result = {
                "success": True,
                "content": content,
                "reasoning_steps": reasoning_steps,
                "tokens_used": tokens_used,
                "removed_metadata": removed_metadata
            }

            # Save to cache
            self._save_to_cache(cache_key, result)

            return result
            
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
        base_prompt = get_vision_ocr_prompt()
        
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
        """Convert PIL Image to base64 string with optimization."""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Optimize image size if too large
        optimized_image = self._optimize_image_for_api(image)

        # Use JPEG for better compression
        return util_image_to_base64(optimized_image, format="JPEG", quality=85)
    
    def _clean_ai_metadata(self, text: str) -> Tuple[str, List[str]]:
        """Remove AI metadata, apologies, and commentary from OCR output.

        Args:
            text: Raw text from AI model

        Returns:
            Tuple of (cleaned_text, list of removed fragments)
        """
        if not text:
            return text, []

        import re

        # Track what we remove
        removed_fragments = []

        # Remove common AI metadata patterns
        patterns_to_remove = [
            (r"I'm unable to.*?(?:\.|$)", "Unable statement"),
            (r"I cannot.*?(?:\.|$)", "Cannot statement"),
            (r"If you have any.*?(?:\.|$)", "Help offer"),
            (r"feel free to ask.*?(?:\.|$)", "Help offer"),
            (r"I apologize.*?(?:\.|$)", "Apology"),
            (r"Please note.*?(?:\.|$)", "Please note"),
            (r"It appears.*?(?:\.|$)", "It appears"),
            (r"Based on.*?(?:\.|$)", "Based on"),
            (r"Here is.*?(?:\.|$)", "Here is"),
            (r"The following.*?(?:\.|$)", "The following"),
            (r"As requested.*?(?:\.|$)", "As requested"),
            (r"I'll extract.*?(?:\.|$)", "I'll extract"),
        ]

        cleaned_text = text
        for pattern, label in patterns_to_remove:
            matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    removed_fragments.append(f"{label}: '{match.strip()}'")
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)

        # Clean up extra whitespace and empty lines
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
        cleaned_text = re.sub(r'^\s*\n', '', cleaned_text)
        cleaned_text = cleaned_text.strip()

        return cleaned_text, removed_fragments

    def _optimize_image_for_api(self, image: Image.Image, max_dimension: int = 2048) -> Image.Image:
        """Optimize image size for API processing while maintaining quality.

        Args:
            image: PIL Image to optimize
            max_dimension: Maximum width or height (default 2048 for good quality)

        Returns:
            Optimized PIL Image
        """
        # Get current dimensions
        width, height = image.size

        # Calculate if resizing is needed
        if width > max_dimension or height > max_dimension:
            # Calculate scaling factor
            scale = min(max_dimension / width, max_dimension / height)
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Use high-quality downsampling
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.logger.log_step(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            return resized_image

        return image

    def _get_cache_key(self, image: Image.Image, strategy: str, page_number: int) -> str:
        """Generate cache key for OCR results.

        Args:
            image: PIL Image
            strategy: Extraction strategy
            page_number: Page number

        Returns:
            Cache key string
        """
        # Create hash from image content
        import io
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        img_hash = hashlib.sha256(img_bytes.getvalue()).hexdigest()[:16]

        return f"{img_hash}_{strategy}_{page_number}"

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached OCR result if available.

        Args:
            cache_key: Cache key

        Returns:
            Cached result dictionary or None
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        with self.cache_lock:
            if os.path.exists(cache_file):
                try:
                    # Check if cache is recent (within 24 hours)
                    cache_age = time.time() - os.path.getmtime(cache_file)
                    if cache_age < 86400:  # 24 hours
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)
                            self.logger.log_step(f"Using cached OCR result for {cache_key}")
                            return cached_data
                except Exception as e:
                    self.logger.log_warning(f"Failed to load cache {cache_key}: {e}")

        return None

    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Save OCR result to cache.

        Args:
            cache_key: Cache key
            result: Result to cache
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        with self.cache_lock:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                self.logger.log_step(f"Cached OCR result as {cache_key}")
            except Exception as e:
                self.logger.log_warning(f"Failed to save cache {cache_key}: {e}")

    def process_pages_parallel(self, pages: List[Dict[str, Any]], context: Dict[str, Any] = None) -> List[AgentResponse]:
        """Process multiple pages in parallel for faster throughput.

        Args:
            pages: List of page dictionaries containing 'image' and 'page_number'
            context: Optional context dictionary

        Returns:
            List of AgentResponse objects
        """
        context = context or {}
        futures = []
        results = {}

        self.logger.log_step(f"Starting parallel processing of {len(pages)} pages")

        # Submit all pages for processing
        for page_data in pages:
            future = self.executor.submit(self.process, page_data, context)
            futures.append((future, page_data['page_number']))

        # Collect results as they complete
        for future, page_number in futures:
            try:
                result = future.result(timeout=120)  # 2 min timeout per page
                results[page_number] = result
                self.logger.log_success(f"Completed page {page_number}")
            except Exception as e:
                self.logger.log_error(f"Failed to process page {page_number}: {e}")
                results[page_number] = AgentResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    error_message=str(e)
                )

        # Return results in page order
        return [results[i] for i in sorted(results.keys())]

    def cleanup(self):
        """
        Explicitly cleanup resources (thread pool executor).

        Call this when the agent is no longer needed to immediately release
        resources and reduce latency. While Python's GC will eventually clean
        up, explicit cleanup is better for:
        - Reducing thread count immediately
        - Freeing memory faster
        - Better resource management in long-running services
        """
        # Call base class cleanup first
        super().cleanup()

        # Cleanup vision-specific resources
        if hasattr(self, 'executor') and self.executor and not self._executor_shutdown:
            self.logger.log_step("🧹 Shutting down vision agent thread pool")
            try:
                # Shutdown with wait=True to ensure all tasks complete
                self.executor.shutdown(wait=True)
                self._executor_shutdown = True
            except Exception as e:
                self.logger.log_warning(f"Error during executor shutdown: {e}")

    def __del__(self):
        """
        Ensure cleanup on deletion (defensive programming).

        This provides a safety net in case cleanup() wasn't called explicitly.
        Python's GC will call this when the object is garbage collected.
        """
        if hasattr(self, '_executor_shutdown') and not self._executor_shutdown:
            if hasattr(self, 'executor') and self.executor:
                try:
                    # Use wait=False in __del__ to avoid blocking GC
                    self.executor.shutdown(wait=False)
                    self._executor_shutdown = True
                except Exception:
                    # Silently fail in __del__ (don't use logger as it may be None)
                    pass


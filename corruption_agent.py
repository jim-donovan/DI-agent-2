"""
Corruption Agent
Intelligent agent for document evaluation and OCR method selection
Replaces rule-based corruption detection with AI-powered visual and content analysis
"""

import time
import re
from typing import Dict, Any, Tuple, Optional
from enum import Enum

from agent_base import BaseAgent, AgentResponse
from logger import ProcessingLogger
from config import config
from api_client import APIClient

class OCRMethod(Enum):
    """OCR processing methods."""
    VISION = "vision_ocr"
    TESSERACT = "tesseract"
    PDF_TEXT = "pdf_text"

class CorruptionAgent(BaseAgent):
    """Agent specialized for intelligent document evaluation and OCR routing."""
    
    def __init__(self, logger: ProcessingLogger, api_client: Optional[APIClient] = None):
        """Initialize the CorruptionAgent.
        
        Args:
            logger: Logger instance for recording activities
            api_client: Optional APIClient instance (will be created if not provided)
        """
        super().__init__("corruption_agent", logger, api_client=api_client)
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for corruption analysis."""
        return """You are a document analysis expert that determines the optimal OCR processing method.

## Your Task
Analyze document pages to route them to the appropriate OCR processing method:

1. **VISION_OCR** - For pages containing:
   - Tables (structured data in rows/columns)
   - Charts, graphs, or diagrams
   - Checkboxes, form fields, or selection elements
   - Complex layouts with mixed text and visual elements
   - Poor quality scans where text extraction failed

2. **TESSERACT** - For pages with:
   - Clean, readable text that extracted well from PDF
   - Simple layouts without complex visual elements
   - No tables, charts, or form elements
   - Good quality scans with clear text

3. **PDF_TEXT** - For pages where:
   - Text was successfully extracted from PDF
   - Content is clean and well-formatted
   - No visual processing is needed

## Analysis Criteria
- **Visual Elements**: Presence of tables, charts, graphs, diagrams
- **Form Elements**: Checkboxes, radio buttons, form fields
- **Text Quality**: Clarity, completeness, formatting integrity
- **Layout Complexity**: Simple text vs. complex structured layouts
- **Scan Quality**: Image clarity, text readability

## Response Format
Provide your analysis as:
{
    "recommended_method": "VISION_OCR|TESSERACT|PDF_TEXT",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation of decision",
    "detected_elements": ["table", "chart", "checkbox", "poor_text", etc.],
    "visual_complexity": "low|medium|high"
}

Be decisive and consistent. Prioritize accuracy over speed."""

    def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResponse:
        """Analyze page content and determine optimal OCR method."""
        start_time = time.time()
        context = context or {}
        
        try:
            # Extract page data
            page_text = input_data.get("text", "") if isinstance(input_data, dict) else str(input_data)
            page_image = input_data.get("image") if isinstance(input_data, dict) else None
            page_number = context.get("page_number", 1)
            
            self.add_memory("analysis_request", {
                "page_number": page_number,
                "text_length": len(page_text),
                "has_image": page_image is not None
            })
            
            # Perform hybrid analysis (text + visual if available)
            text_analysis = self._analyze_extracted_text(page_text)
            visual_analysis = self._analyze_visual_elements(page_image, page_text) if page_image else {}
            
            # Combine analyses to make routing decision
            recommendation = self._determine_ocr_method(text_analysis, visual_analysis, context)
            
            # Update state
            self.update_state("last_recommendation", recommendation)
            self.state.confidence_scores["corruption_analysis"] = recommendation["confidence"]
            
            processing_time = time.time() - start_time
            
            response = AgentResponse(
                success=True,
                content=recommendation,
                confidence=recommendation["confidence"],
                metadata={
                    "page_number": page_number,
                    "text_analysis": text_analysis,
                    "visual_analysis": visual_analysis,
                    "processing_method": "hybrid_analysis"
                },
                reasoning_steps=[
                    "Analyzed extracted text quality and patterns",
                    "Evaluated visual elements and complexity" if page_image else "No image available - text-only analysis",
                    f"Recommended {recommendation['recommended_method']} based on analysis"
                ],
                processing_time=processing_time
            )
            
            self.logger.log_success(
                f"Page {page_number} routing: {recommendation['recommended_method']} "
                f"(confidence: {recommendation['confidence']:.2f})"
            )
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.log_error(f"Corruption analysis failed: {str(e)}")
            
            # Fallback to conservative approach
            fallback_recommendation = {
                "recommended_method": OCRMethod.TESSERACT.value,
                "confidence": 0.3,
                "reasoning": f"Analysis failed, defaulting to Tesseract: {str(e)}",
                "detected_elements": [],
                "visual_complexity": "unknown"
            }
            
            return AgentResponse(
                success=False,
                content=fallback_recommendation,
                confidence=0.3,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _analyze_extracted_text(self, text: str) -> Dict[str, Any]:
        """Analyze extracted PDF text for quality and content patterns."""
        analysis = {
            "text_quality": "good",
            "has_tables": False,
            "has_checkboxes": False,
            "has_structured_data": False,
            "corruption_indicators": [],
            "quality_score": 1.0
        }
        
        if not text.strip():
            analysis.update({
                "text_quality": "missing",
                "quality_score": 0.0,
                "corruption_indicators": ["no_text_extracted"]
            })
            return analysis
        
        # Text corruption indicators
        corruption_score = 0.0
        
        # Check for table patterns
        table_indicators = ["|", "─", "┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼"]
        if any(indicator in text for indicator in table_indicators):
            analysis["has_tables"] = True
            analysis["corruption_indicators"].append("table_detected")
        
        # Multiple aligned spaces (table columns)
        if len(re.findall(r'\w\s{4,}\w', text)) > 3:
            analysis["has_tables"] = True
            analysis["corruption_indicators"].append("aligned_columns")
        
        # Checkbox patterns
        checkbox_patterns = [
            r'\[[ x✓✔]\]',  # [x], [ ], [✓]
            r'☐', r'☑', r'✓', r'✔',  # checkbox symbols
            r'^\s*[x✓✔¨]\s*\([a-z]+\)',  # x (a), ¨ (b)
        ]
        if any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in checkbox_patterns):
            analysis["has_checkboxes"] = True
            analysis["corruption_indicators"].append("checkboxes_detected")
        
        # Structured data patterns
        if re.search(r'^\s*[A-Z][^:]*:\s*\$?\d', text, re.MULTILINE):  # "Label: value" patterns
            analysis["has_structured_data"] = True
            analysis["corruption_indicators"].append("structured_data")
        
        # Text quality issues
        words = text.split()
        if words:
            # Excessive single character words
            single_chars = len([w for w in words if len(w) == 1 and w.isalpha()])
            if single_chars / len(words) > 0.1:
                corruption_score += 0.3
                analysis["corruption_indicators"].append("fragmented_words")
            
            # Very short average word length
            avg_word_length = sum(len(w) for w in words) / len(words)
            if avg_word_length < 2.5:
                corruption_score += 0.2
                analysis["corruption_indicators"].append("short_words")
            
            # Excessive spacing issues
            space_ratio = text.count(' ') / len(text.replace(' ', '').replace('\n', '')) if text.replace(' ', '').replace('\n', '') else 0
            if space_ratio > 0.5:
                corruption_score += 0.2
                analysis["corruption_indicators"].append("spacing_corruption")
        
        # Character encoding issues
        weird_chars = len(re.findall(r'[^\w\s.,!?;:()\-$%/€£¥\'"&@#*]', text))
        if weird_chars > len(text) * 0.01:
            corruption_score += 0.2
            analysis["corruption_indicators"].append("encoding_issues")
        
        # Update quality assessment
        analysis["quality_score"] = max(0.0, 1.0 - corruption_score)
        if corruption_score > 0.3:
            analysis["text_quality"] = "poor"
        elif corruption_score > 0.1:
            analysis["text_quality"] = "fair"
        
        return analysis

    def _optimize_image_for_visual_analysis(self, image, max_dimension: int = 1536):
        """Optimize image for visual analysis (layout detection doesn't need full resolution).

        Args:
            image: PIL Image to optimize
            max_dimension: Maximum width or height (default 1536 for visual analysis)

        Returns:
            Optimized PIL Image
        """
        from PIL import Image

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Calculate if resizing is needed
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            # Calculate scaling factor
            scale = min(max_dimension / width, max_dimension / height)
            new_width = int(width * scale)
            new_height = int(height * scale)

            # Use high-quality downsampling
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.logger.log_step(f"Optimized image for visual analysis: {width}x{height} → {new_width}x{new_height}")
            return resized_image

        return image

    def _analyze_visual_elements(self, page_image, extracted_text: str) -> Dict[str, Any]:
        """Use vision model to analyze visual elements in the page image."""
        if not page_image or not self.api_client:
            return {"visual_analysis_available": False}
        
        try:
            visual_prompt = """Analyze this document page image and identify visual elements:

1. **Tables**: Any structured data in rows/columns, even if text is corrupted
2. **Charts/Graphs**: Bar charts, pie charts, line graphs, diagrams
3. **Forms**: Checkboxes, radio buttons, form fields, selection elements
4. **Layout**: Simple text vs. complex multi-column or structured layout
5. **Image Quality**: Clear/blurry, readable/unreadable text

Respond with JSON:
{
    "has_tables": true/false,
    "has_charts": true/false,
    "has_forms": true/false,
    "layout_complexity": "simple|moderate|complex",
    "image_quality": "poor|fair|good|excellent",
    "visual_elements": ["table", "chart", "checkbox", "diagram", etc.],
    "text_readability": "poor|fair|good|excellent"
}"""

            # Convert PIL Image to base64 string with optimization
            import base64
            import io
            from PIL import Image

            if hasattr(page_image, 'save'):  # It's a PIL Image
                # Optimize image for visual analysis (layout detection doesn't need full resolution)
                optimized_image = self._optimize_image_for_visual_analysis(page_image)

                buffer = io.BytesIO()
                optimized_image.save(buffer, format='JPEG', quality=85)
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                image_url = f"data:image/jpeg;base64,{img_base64}"
            else:
                image_url = page_image  # Assume it's already a data URL
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert document analyzer. Provide accurate visual analysis in JSON format."
                },
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": visual_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
            
            response_text, tokens_used = self.make_api_call(
                messages,
                task="corruption"
            )
            
            # Parse JSON response - handle markdown code blocks
            import json
            
            try:
                # Clean up the response - remove markdown code blocks if present
                cleaned_response = response_text.strip()
                
                # Remove ```json and ``` if present
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                elif cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # Remove ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                
                cleaned_response = cleaned_response.strip()
                
                # Try to extract just the JSON part if there's extra content
                # Look for the main JSON object boundaries
                if cleaned_response.startswith('{'):
                    # Find the matching closing brace for the main JSON object
                    brace_count = 0
                    json_end = 0
                    for i, char in enumerate(cleaned_response):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > 0:
                        cleaned_response = cleaned_response[:json_end]
                
                # Try to fix common JSON issues
                # Check if response was truncated (doesn't end with })
                if not cleaned_response.endswith('}'):
                    # Handle unterminated strings
                    if cleaned_response.count('"') % 2 == 1:
                        # Odd number of quotes means unterminated string
                        cleaned_response += '"'
                    
                    # Try to close any open structures
                    open_brackets = cleaned_response.count('[') - cleaned_response.count(']')
                    open_braces = cleaned_response.count('{') - cleaned_response.count('}')
                    
                    # Add closing brackets/braces
                    cleaned_response += ']' * open_brackets
                    cleaned_response += '}' * open_braces
                
                visual_analysis = json.loads(cleaned_response)
                visual_analysis["tokens_used"] = tokens_used
                visual_analysis["visual_analysis_available"] = True
                return visual_analysis
                
            except json.JSONDecodeError as e:
                self.logger.log_warning(f"Failed to parse visual analysis JSON: {str(e)}")
                # Try to extract key information even if JSON is malformed
                has_tables = 'true' in response_text.lower() and 'has_tables' in response_text
                has_charts = 'true' in response_text.lower() and 'has_charts' in response_text
                has_forms = 'true' in response_text.lower() and 'has_forms' in response_text
                
                return {
                    "visual_analysis_available": False,
                    "has_tables": has_tables,
                    "has_charts": has_charts,
                    "has_forms": has_forms,
                    "error": f"JSON parse error: {str(e)}",
                    "fallback_parsing": True
                }
            
        except Exception as e:
            self.logger.log_error(f"Visual analysis failed: {str(e)}")
            return {
                "visual_analysis_available": False,
                "error": str(e)
            }
    
    def _determine_ocr_method(self, text_analysis: Dict[str, Any], 
                             visual_analysis: Dict[str, Any], 
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal OCR method based on combined analysis."""
        
        # Priority decision logic
        detected_elements = []
        reasoning_parts = []
        base_confidence = 0.8
        
        # Check vision limits first
        vision_calls_used = context.get("vision_calls_used", 0)
        if vision_calls_used >= config.max_vision_calls_per_doc:
            return {
                "recommended_method": OCRMethod.TESSERACT.value,
                "confidence": 0.9,
                "reasoning": f"Vision limit reached ({config.max_vision_calls_per_doc}), using Tesseract",
                "detected_elements": ["vision_limit_reached"],
                "visual_complexity": "unknown"
            }
        
        # Visual analysis takes precedence if available
        if visual_analysis.get("visual_analysis_available", False):
            if visual_analysis.get("has_tables", False):
                detected_elements.append("table")
                reasoning_parts.append("tables detected in image")
                
            if visual_analysis.get("has_charts", False):
                detected_elements.append("chart") 
                reasoning_parts.append("charts/graphs detected")
                
            if visual_analysis.get("has_forms", False):
                detected_elements.append("forms")
                reasoning_parts.append("form elements detected")
            
            # Visual complexity assessment
            layout_complexity = visual_analysis.get("layout_complexity", "simple")
            image_quality = visual_analysis.get("image_quality", "good")
            
            if layout_complexity in ["moderate", "complex"]:
                detected_elements.append("complex_layout")
                reasoning_parts.append(f"{layout_complexity} layout")
            
            if image_quality == "poor":
                detected_elements.append("poor_image_quality")
                reasoning_parts.append("poor image quality detected")
                base_confidence -= 0.1
        
        # Text analysis insights
        if text_analysis.get("has_tables", False):
            detected_elements.append("table_text")
            reasoning_parts.append("table patterns in extracted text")
            
        if text_analysis.get("has_checkboxes", False):
            detected_elements.append("checkbox")
            reasoning_parts.append("checkbox patterns detected")
            
        if text_analysis.get("text_quality") == "poor":
            detected_elements.append("poor_text")
            reasoning_parts.append("poor text extraction quality")
            
        # Decision logic
        visual_complexity = visual_analysis.get("layout_complexity", "simple")
        
        # High priority for vision OCR
        if any(element in detected_elements for element in ["table", "chart", "forms", "checkbox"]):
            return {
                "recommended_method": OCRMethod.VISION.value,
                "confidence": base_confidence,
                "reasoning": f"Visual elements require vision OCR: {', '.join(reasoning_parts)}",
                "detected_elements": detected_elements,
                "visual_complexity": visual_complexity
            }
        
        # Medium priority conditions
        if ("poor_text" in detected_elements or
            "poor_image_quality" in detected_elements or
            text_analysis.get("quality_score", 1.0) < 0.7 or
            text_analysis.get("text_quality") == "missing"):

            # Special case: if text is missing/minimal, this is likely an image-based PDF
            if text_analysis.get("text_quality") == "missing":
                reasoning_parts.append("minimal/no text extracted - likely image-based document")

            return {
                "recommended_method": OCRMethod.VISION.value,
                "confidence": base_confidence if text_analysis.get("text_quality") == "missing" else base_confidence - 0.1,
                "reasoning": f"Text quality issues detected: {', '.join(reasoning_parts)}",
                "detected_elements": detected_elements,
                "visual_complexity": visual_complexity
            }
        
        # Default to Tesseract for clean, simple text
        if text_analysis.get("text_quality") == "good" and not detected_elements:
            return {
                "recommended_method": OCRMethod.TESSERACT.value,
                "confidence": 0.9,
                "reasoning": "Clean text with no visual elements, optimal for Tesseract",
                "detected_elements": ["clean_text"],
                "visual_complexity": "low"
            }
        
        # Conservative fallback
        return {
            "recommended_method": OCRMethod.TESSERACT.value,
            "confidence": 0.7,
            "reasoning": f"Conservative routing to Tesseract: {', '.join(reasoning_parts) if reasoning_parts else 'standard processing'}",
            "detected_elements": detected_elements,
            "visual_complexity": visual_complexity
        }
    
    def should_use_vision(self, text: str, page_image=None, vision_calls_used: int = 0, 
                         page_number: int = 1) -> Tuple[bool, str]:
        """
        Compatibility method for existing code.
        
        Args:
            text: Extracted text from PDF
            page_image: Page image data (optional)
            vision_calls_used: Number of vision calls already made
            page_number: Current page number
            
        Returns:
            Tuple of (should_use_vision, reason)
        """
        input_data = {"text": text}
        if page_image:
            input_data["image"] = page_image
            
        context = {
            "vision_calls_used": vision_calls_used,
            "page_number": page_number
        }
        
        try:
            response = self.process(input_data, context)
            if response.success:
                recommendation = response.content
                should_use = recommendation["recommended_method"] == OCRMethod.VISION.value
                reason = recommendation["reasoning"]
                return should_use, reason
            else:
                # Fallback decision
                return False, f"Analysis failed: {response.error_message}"
                
        except Exception as e:
            # Ultra-conservative fallback
            return False, f"Agent processing failed: {str(e)}"
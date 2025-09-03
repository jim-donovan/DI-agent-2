"""
Checker Agent
Quality evaluation agent that compares final markdown output against original PDF
Uses a different model for independent validation
"""

import time
import json
import tempfile
import os
import base64
import io
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image

from agent_base import BaseAgent, AgentResponse
from logger import ProcessingLogger
from config import config
import anthropic

class CheckerAgent(BaseAgent):
    """Agent specialized for quality evaluation and validation of processed documents."""
    
    def __init__(self, logger: ProcessingLogger, openai_api_key: str = None):
        super().__init__("checker_agent", logger, openai_api_key or config.openai_api_key)
        # Use Anthropic for independent perspective
        self.use_anthropic = bool(config.anthropic_api_key)
        if self.use_anthropic:
            self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        
        # Always set evaluation model for OpenAI fallback/Files API
        self.evaluation_model = "gpt-4o-mini"  # Different from main processing model
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for quality evaluation."""
        return """You are a precise document comparison evaluator. Your task is to identify specific missing and added content between the original PDF and processed markdown.

## Your Task
Compare the original PDF pages with the processed markdown line-by-line to identify:

1. **MISSING ITEMS**: Content that appears in the PDF but is missing from the markdown
2. **ADDED ITEMS**: Content that appears in the markdown but was not in the original PDF

## Analysis Method
- Go through each PDF page systematically
- Compare against the markdown content
- Note specific locations (PDF page numbers, markdown line numbers)
- Focus on factual content, not formatting differences

## Response Format
Provide evaluation as JSON:
{
    "missing_items": [
        {
            "content": "exact text that is missing",
            "pdf_page": "page number in original PDF",
            "context": "surrounding context to help locate"
        }
    ],
    "added_items": [
        {
            "content": "exact text that was added",
            "markdown_line": "approximate line number in markdown",
            "context": "surrounding context"
        }
    ],
    "overall_score": 0.0-100.0,
    "recommendation": "ACCEPT|REVIEW|REJECT",
    "summary": "Brief assessment focusing on completeness and accuracy"
}

## Instructions
- Be precise and specific
- Only report significant missing content (not minor formatting differences)
- Include exact quotes when possible
- Focus on data, numbers, important details, and substantive text
- Ignore pure formatting artifacts
- Report missing tables, sections, or important details

Be factual and specific in your comparisons."""

    def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResponse:
        """Evaluate markdown output against original PDF content."""
        start_time = time.time()
        context = context or {}
        
        try:
            # Extract evaluation inputs
            markdown_content = input_data.get("markdown_content", "") if isinstance(input_data, dict) else str(input_data)
            pdf_images = input_data.get("pdf_images", []) if isinstance(input_data, dict) else []
            original_text = input_data.get("original_text", "") if isinstance(input_data, dict) else ""
            
            document_name = context.get("document_name", "Unknown Document")
            
            self.add_memory("evaluation_request", {
                "document_name": document_name,
                "markdown_length": len(markdown_content),
                "original_text_length": len(original_text),
                "pdf_pages": len(pdf_images)
            })
            
            # Perform comprehensive evaluation
            if pdf_images:
                # Visual comparison with PDF pages
                evaluation = self._evaluate_with_visual_comparison(
                    markdown_content, pdf_images, original_text, context
                )
            else:
                # Text-based evaluation only
                evaluation = self._evaluate_text_based(
                    markdown_content, original_text, context
                )
            
            # Calculate overall assessment
            final_assessment = self._calculate_final_assessment(evaluation, context)
            
            # Update state
            self.update_state("last_evaluation", final_assessment)
            self.state.confidence_scores["quality_evaluation"] = final_assessment["confidence"]
            
            processing_time = time.time() - start_time
            
            response = AgentResponse(
                success=True,
                content=final_assessment,
                confidence=final_assessment["confidence"],
                metadata={
                    "document_name": document_name,
                    "evaluation_type": "visual_comparison" if pdf_images else "text_based",
                    "pages_evaluated": len(pdf_images),
                    "evaluation_model": self.evaluation_model
                },
                reasoning_steps=[
                    "Analyzed markdown content structure and completeness",
                    "Evaluated formatting consistency and standards compliance",
                    "Assessed data integrity and accuracy" + (" using visual comparison" if pdf_images else ""),
                    f"Generated final quality score: {final_assessment['overall_score']:.1f}/100"
                ],
                processing_time=processing_time
            )
            
            self.logger.log_success(
                f"Quality evaluation completed: {final_assessment['overall_score']:.1f}/100 "
                f"({final_assessment['recommendation']})"
            )
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.log_error(f"Quality evaluation failed: {str(e)}")
            
            # Fallback evaluation
            fallback_assessment = {
                "overall_score": 50.0,
                "content_completeness": 50.0,
                "structural_accuracy": 50.0,
                "data_integrity": 50.0,
                "formatting_consistency": 50.0,
                "strengths": [],
                "issues_found": [f"Evaluation failed: {str(e)}"],
                "missing_content": [],
                "formatting_problems": [],
                "recommendation": "REVIEW",
                "confidence": 0.1,
                "summary": f"Evaluation failed, manual review required: {str(e)}"
            }
            
            return AgentResponse(
                success=False,
                content=fallback_assessment,
                confidence=0.1,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _make_anthropic_api_call(self, messages: List[Dict], temperature: float = 0.0, 
                                max_tokens: int = None) -> Tuple[str, int]:
        """Make API call to Anthropic."""
        # Use config default if max_tokens not specified
        if max_tokens is None:
            max_tokens = config.anthropic_max_tokens
        try:
            # Convert OpenAI format to Anthropic format
            system_message = None
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                elif msg["role"] == "user":
                    if isinstance(msg["content"], str):
                        user_messages.append({"role": "user", "content": msg["content"]})
                    elif isinstance(msg["content"], list):
                        # Handle vision messages - Anthropic supports vision in Claude 3.5 Sonnet
                        anthropic_content = []
                        for item in msg["content"]:
                            if item.get("type") == "text" and item.get("text", "").strip():
                                anthropic_content.append({"type": "text", "text": item["text"]})
                            elif item.get("type") == "image_url":
                                # Convert OpenAI format to Anthropic format
                                image_url = item["image_url"]["url"]
                                if image_url.startswith("data:image"):
                                    # Extract media type and base64 data
                                    media_type = image_url.split(";")[0].split(":")[1]
                                    base64_data = image_url.split("base64,")[1]
                                    anthropic_content.append({
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": media_type,
                                            "data": base64_data
                                        }
                                    })
                        if anthropic_content:
                            user_messages.append({"role": "user", "content": anthropic_content})
            
            # Make Anthropic API call with streaming for long requests
            response = self.anthropic_client.messages.create(
                model=config.anthropic_model,
                system=system_message or self.get_system_prompt(),
                messages=user_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True  # Enable streaming for long requests
            )
            
            # Collect streamed response
            response_text = ""
            input_tokens = 0
            output_tokens = 0
            
            try:
                for chunk in response:
                    if chunk.type == "content_block_delta":
                        if hasattr(chunk.delta, 'text'):
                            response_text += chunk.delta.text
                    elif chunk.type == "message_start":
                        if hasattr(chunk.message, 'usage') and chunk.message.usage:
                            input_tokens = chunk.message.usage.input_tokens
                    elif chunk.type == "message_delta":
                        if hasattr(chunk, 'usage') and chunk.usage and hasattr(chunk.usage, 'output_tokens'):
                            output_tokens = chunk.usage.output_tokens
            except Exception as stream_error:
                self.logger.log_error(f"Error processing Anthropic stream: {str(stream_error)}")
                raise Exception(f"Anthropic streaming failed: {str(stream_error)}") from stream_error
            
            tokens_used = input_tokens + output_tokens
            
            return response_text, tokens_used
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Enhanced error detection for different Anthropic API issues
            is_overloaded = False
            is_rate_limited = False
            is_token_limit = False
            
            try:
                # Check for rate limiting errors
                if any(phrase in error_str for phrase in [
                    'rate limit', 'rate_limit', 'too many requests', 'requests per', 
                    'quota exceeded', 'usage limit'
                ]):
                    is_rate_limited = True
                    self.logger.log_warning(f"🚨 RATE LIMITING DETECTED: {str(e)}")
                
                # Check for token limit errors  
                elif any(phrase in error_str for phrase in [
                    'token limit', 'context length', 'maximum context', 'input too long',
                    'exceeds maximum', 'token count'
                ]):
                    is_token_limit = True
                    self.logger.log_warning(f"📏 TOKEN LIMIT EXCEEDED: {str(e)}")
                
                # Check for overloaded/capacity errors
                elif any(phrase in error_str for phrase in [
                    'overloaded', 'capacity', 'server overloaded', 'service unavailable',
                    'temporarily unavailable', 'high demand'
                ]):
                    is_overloaded = True
                    self.logger.log_warning(f"⚠️ API OVERLOADED: {str(e)}")
                
                else:
                    # Log the full error for unknown issues
                    self.logger.log_error(f"🔍 UNKNOWN ANTHROPIC ERROR: {str(e)}")
                    
            except:
                pass
            
            # Handle rate limiting specifically
            if is_rate_limited:
                self.logger.log_warning(f"⚠️ Anthropic API rate limit exceeded, falling back to OpenAI evaluation")
                raise Exception("anthropic_overloaded") from e
            
            # Handle any capacity issues (overloaded, token limits, etc.)
            if is_overloaded or is_token_limit:
                self.logger.log_warning(f"⚠️ Anthropic API capacity issue, falling back to OpenAI evaluation")
                raise Exception("anthropic_overloaded") from e
            
            # Log detailed error info for debugging
            self.logger.log_error(f"Anthropic API call failed: {str(e)}")
            self.logger.log_error(f"Anthropic model: {config.anthropic_model}")
            self.logger.log_error(f"Message count: {len(user_messages)}")
            self.logger.log_error(f"Max tokens: {max_tokens}")
            # Log first message structure for debugging
            if user_messages:
                first_msg = user_messages[0]
                if isinstance(first_msg.get("content"), list):
                    content_types = [item.get("type") for item in first_msg["content"]]
                    self.logger.log_error(f"First message content types: {content_types}")
            raise
    
    def _compress_image_for_anthropic(self, data_url: str, max_size: int = 1024) -> str:
        """Compress image for Anthropic to reduce token usage."""
        try:
            # Extract base64 data
            if 'base64,' in data_url:
                base64_data = data_url.split('base64,')[1]
            else:
                return data_url  # Return as-is if not base64
            
            # Decode image
            image_data = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_data))
            
            # Calculate compression ratio to target max_size KB
            current_size = len(base64_data) * 3 / 4 / 1024  # Rough size in KB
            if current_size <= max_size:
                return data_url  # Already small enough
            
            # Resize image to reduce size
            ratio = (max_size / current_size) ** 0.5
            new_width = int(image.width * ratio)
            new_height = int(image.height * ratio)
            
            # Resize and compress
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert back to base64 with JPEG compression
            buffer = io.BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(buffer, format='JPEG', quality=75, optimize=True)
            
            compressed_data = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{compressed_data}"
            
        except Exception as e:
            self.logger.log_warning(f"Image compression failed: {str(e)}, using original")
            return data_url
    
    def _upload_pdf_to_openai(self, pdf_path: str) -> str:
        """Upload PDF to OpenAI Files API and return file ID."""
        try:
            with open(pdf_path, "rb") as file:
                response = self.client.files.create(
                    file=file,
                    purpose="vision"  # For vision analysis
                )
            self.logger.log_step(f"Uploaded PDF to OpenAI Files API: {response.id}")
            return response.id
        except Exception as e:
            self.logger.log_error(f"Failed to upload PDF to OpenAI: {str(e)}")
            raise
    
    def _delete_openai_file(self, file_id: str) -> bool:
        """Delete file from OpenAI Files API."""
        try:
            self.client.files.delete(file_id)
            self.logger.log_step(f"Deleted OpenAI file: {file_id}")
            return True
        except Exception as e:
            self.logger.log_error(f"Failed to delete OpenAI file {file_id}: {str(e)}")
            return False
    
    def _create_temp_pdf_from_images(self, pdf_images: List[str]) -> str:
        """Create temporary PDF from base64 image list for Files API upload."""
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io
            import base64
            
            # Create temporary PDF file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='checker_eval_')
            os.close(temp_fd)  # Close the file descriptor
            
            # Create PDF document
            pdf_doc = fitz.open()
            
            for i, img_data_url in enumerate(pdf_images):
                try:
                    # Extract base64 data from data URL
                    if img_data_url.startswith('data:image'):
                        base64_data = img_data_url.split(',')[1]
                    else:
                        base64_data = img_data_url
                    
                    # Decode image
                    img_bytes = base64.b64decode(base64_data)
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    
                    # Convert to RGB if necessary
                    if pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                    
                    # Save as temporary image for PyMuPDF
                    img_temp_fd, img_temp_path = tempfile.mkstemp(suffix='.png')
                    os.close(img_temp_fd)
                    pil_img.save(img_temp_path, format='PNG')
                    
                    # Add page to PDF (without transform parameter for newer PyMuPDF)
                    page = pdf_doc.new_page(width=pil_img.width * 0.75, height=pil_img.height * 0.75)
                    page.insert_image(page.rect, filename=img_temp_path)
                    # Note: transform parameter removed as it's not supported in newer PyMuPDF versions
                    
                    # Clean up temp image
                    os.unlink(img_temp_path)
                    
                except Exception as e:
                    self.logger.log_error(f"Failed to process image {i}: {str(e)}")
                    continue
            
            # Save PDF
            pdf_doc.save(temp_path)
            pdf_doc.close()
            
            self.logger.log_step(f"Created temporary PDF with {len(pdf_images)} pages: {temp_path}")
            return temp_path
            
        except Exception as e:
            # Clean up on error
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            self.logger.log_error(f"Failed to create temporary PDF: {str(e)}")
            raise
    
    def _evaluate_with_visual_comparison(self, markdown_content: str, pdf_images: List, 
                                       original_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate markdown against PDF images using vision model."""
        temp_pdf_path = None
        uploaded_file_id = None
        
        try:
            # Comparison mode: run both OpenAI and Anthropic if both available
            if config.compare_evaluation_methods and self.use_anthropic:
                self.logger.log_step("🔬 Running dual evaluation comparison (OpenAI vs Anthropic)")
                
                openai_result = None
                anthropic_result = None
                
                # Run OpenAI evaluation with base64
                try:
                    openai_result = self._run_base64_evaluation(
                        markdown_content, pdf_images, original_text, context, use_anthropic=False
                    )
                    openai_result["evaluation_method"] = "visual_comparison_openai"
                    self.logger.log_success("✅ OpenAI evaluation completed")
                except Exception as e:
                    self.logger.log_warning(f"OpenAI evaluation failed: {str(e)}")
                
                # Run Anthropic evaluation with base64
                try:
                    anthropic_result = self._run_base64_evaluation(
                        markdown_content, pdf_images, original_text, context, use_anthropic=True
                    )
                    anthropic_result["evaluation_method"] = "visual_comparison_anthropic"
                    self.logger.log_success("✅ Anthropic evaluation completed")
                except Exception as e:
                    error_msg = str(e)
                    if "anthropic_overloaded" in error_msg:
                        self.logger.log_warning("⚠️ Anthropic API overloaded, continuing with OpenAI-only evaluation")
                    else:
                        self.logger.log_warning(f"Anthropic evaluation failed: {error_msg}")
                
                # Return comparison result
                comparison_result = {
                    "comparison_mode": True,
                    "openai_result": openai_result,
                    "anthropic_result": anthropic_result,
                    "primary_result": anthropic_result or openai_result,  # Prefer Anthropic
                    "evaluation_method": "dual_comparison"
                }
                
                # Include primary result fields at top level for compatibility
                if comparison_result["primary_result"]:
                    comparison_result.update(comparison_result["primary_result"])
                    comparison_result["evaluation_method"] = "dual_comparison"
                
                return comparison_result
            
            # Single evaluation mode (original logic)
            elif config.use_files_api_for_evaluation and not self.use_anthropic:
                try:
                    # Create temporary PDF from images
                    temp_pdf_path = self._create_temp_pdf_from_images(pdf_images)
                    
                    # Upload to OpenAI Files API
                    uploaded_file_id = self._upload_pdf_to_openai(temp_pdf_path)
                    
                    # Use Files API evaluation
                    result = self._evaluate_with_files_api(
                        markdown_content, uploaded_file_id, original_text, context
                    )
                    
                    # Mark evaluation method
                    result["evaluation_method"] = "files_api_openai"
                    return result
                    
                except Exception as e:
                    self.logger.log_warning(f"Files API evaluation failed: {str(e)}, falling back to base64")
                    # Continue to base64 fallback
            
            # Base64 method (original approach or Anthropic)
            return self._run_base64_evaluation(markdown_content, pdf_images, original_text, context, use_anthropic=self.use_anthropic)
            
        finally:
            # Clean up Files API resources
            if uploaded_file_id:
                try:
                    self._delete_file_from_openai(uploaded_file_id)
                except:
                    pass
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass
    
    def _run_base64_evaluation(self, markdown_content: str, pdf_images: List, 
                              original_text: str, context: Dict[str, Any], use_anthropic: bool = None) -> Dict[str, Any]:
        """Run evaluation using base64 image encoding."""
        if use_anthropic is None:
            use_anthropic = self.use_anthropic
            
        # Sample key pages for evaluation (first, middle, last + any with tables/forms)  
        pages_to_evaluate = self._select_evaluation_pages(pdf_images, markdown_content)
        
        evaluation_prompt = f"""Compare this markdown output against the original PDF pages to evaluate quality:

## Markdown Content to Evaluate:
{markdown_content}

## SEMANTIC EVALUATION PRINCIPLES:
**Focus on information completeness, not formatting exactness.**

1. **Critical Content Completeness** (HEAVILY WEIGHTED): Are ALL essential details, values, and options captured?
   
2. **Table Structure Validation** (CRITICAL): For tables with multiple columns/plans:
   - Verify ALL column headers are represented in some form
   - Check that each service/row has values for EVERY plan/column shown in original
   - Missing entire column data = MAJOR penalty (score below 70)

3. **Data Integrity**: Are ALL numbers, dates, values, and rates accurate?

4. **Structure Preservation**: Is document hierarchy maintained logically?

## FORMATTING EQUIVALENCE PRINCIPLE:
**Information presented in different but valid markdown formats should be considered equivalent.** 
Evaluate based on semantic meaning, not syntactic matching.

## CONTENT MISSING vs FORMAT DIFFERENT:
**Missing Content (penalize):**
- Information completely absent from markdown
- Entire sections or services not mentioned
- Values omitted entirely 
- Entire table columns with no corresponding data

**Format Different (do NOT penalize):**
- Same information presented using different markdown syntax
- Headers, lists, or tables formatted differently but containing same data
- Alternative but valid ways of structuring the same content

## SCORING GUIDELINES:
- **90-100**: All critical content captured (regardless of formatting approach)
- **70-89**: Minor content gaps but core information present  
- **50-69**: Significant information actually missing (not just formatted differently)
- **Below 50**: Major content gaps, critical details completely absent

**PRINCIPLE: Semantic completeness over syntactic conformity.**
Provide detailed JSON evaluation focusing on actual information gaps, not formatting variations."""

        # Prepare messages for vision analysis
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        
        # Add images for comparison (use all selected pages up to reasonable limit)
        max_eval_pages = min(len(pages_to_evaluate), 8)  # Match _select_evaluation_pages limit
        for i, page_image in enumerate(pages_to_evaluate[:max_eval_pages]):
            # Compress images consistently for both evaluators for fair comparison
            image_url = self._compress_image_for_anthropic(page_image, max_size=800)
            
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": f"PDF Page {i+1}:" if i == 0 else ""},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ] + ([{"type": "text", "text": evaluation_prompt}] if i == max_eval_pages - 1 else [])
            })
        
        if not any("text" in msg.get("content", []) for msg in messages if isinstance(msg.get("content"), list)):
            messages[-1]["content"].append({"type": "text", "text": evaluation_prompt})
        
        try:
            # Use specified method (Anthropic or OpenAI)
            if use_anthropic:
                response_text, tokens_used = self._make_anthropic_api_call(
                    messages,
                    temperature=config.anthropic_temperature,
                    max_tokens=config.anthropic_max_tokens
                )
            else:
                response_text, tokens_used = self.make_api_call(
                    messages,
                    model=self.evaluation_model,
                    temperature=0.1,
                    max_tokens=config.anthropic_max_tokens
                )
            
            # Parse JSON response - handle markdown code blocks
            evaluation_result = self._parse_json_response(response_text)
            evaluation_result["tokens_used"] = tokens_used
            evaluation_result["evaluation_method"] = f"visual_comparison_{'anthropic' if use_anthropic else 'openai'}"
            
            # Debug logging for Anthropic responses
            if use_anthropic:
                missing_count = len(evaluation_result.get('missing_items', []))
                added_count = len(evaluation_result.get('added_items', []))
                score = evaluation_result.get('overall_score', 0)
                self.logger.log_step(f"🔍 Anthropic Debug - Score: {score}, Missing: {missing_count}, Added: {added_count}")
                
                # Log raw response for debugging if score/items seem inconsistent
                if score < 95 and missing_count == 0 and added_count == 0:
                    summary = evaluation_result.get('summary', 'No summary provided')
                    self.logger.log_warning(f"⚠️ Anthropic inconsistent: Low score ({score}) but no specific issues found")
                    self.logger.log_step(f"Anthropic summary: {summary}")
                    # Only log raw response if summary is also empty/unhelpful
                    if len(summary) < 10 or 'no summary' in summary.lower():
                        self.logger.log_step(f"Raw response sample: {response_text[:300]}...")
            
            return evaluation_result
            
        except Exception as e:
            provider = "Anthropic" if use_anthropic else "OpenAI"
            self.logger.log_error(f"{provider} visual evaluation failed: {str(e)}")
            self.logger.log_warning(f"⚠️ Falling back to heuristic evaluation for {provider}")
            fallback_result = self._fallback_text_evaluation(markdown_content, original_text)
            fallback_result["evaluation_method"] = f"fallback_heuristic_{'anthropic' if use_anthropic else 'openai'}"
            return fallback_result
    
    def _evaluate_with_files_api(self, markdown_content: str, file_id: str, 
                                original_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate markdown against uploaded PDF using Files API."""
        evaluation_prompt = f"""Compare this markdown output against the original PDF to evaluate quality:

## Markdown Content to Evaluate:
{markdown_content}

## STRICT EVALUATION CRITERIA:
1. **Critical Content Completeness** (HEAVILY WEIGHTED): Are ALL benefit details, coverage amounts, deductibles, coinsurance rates, and plan options captured? Missing any benefits/financial data should result in major point deduction.
2. **Table Structure Validation** (CRITICAL): For tables with multiple columns/plans:
   - Verify ALL column headers are represented in the flattened format
   - Check that each service/row has values for EVERY plan/column shown in original
   - Missing entire column data = MAJOR penalty (score below 70)
   - Example: If original shows "FlexFit Select" and "iDirect Series 1" columns, markdown must contain values for BOTH plans
3. **Data Integrity**: Are ALL numbers, dates, coverage amounts, and financial values accurate? Any missing financial data = major penalty.
4. **Structure Preservation**: Is document hierarchy maintained?
5. **Form Elements**: Are checkboxes and form elements correctly represented?

## TABLE VALIDATION CHECKLIST:
- Count original table columns vs. flattened representation coverage
- Verify each row/service has data for all plan types shown in original
- Flag when entire columns of data are missing from flattened format

## SCORING GUIDELINES:
- **90-100**: All critical benefits/financial content captured with minor cosmetic issues only (footers, page numbers, hyphenation)
- **70-89**: Some benefits content missing but core plan information present  
- **50-69**: Significant benefits/financial data missing or incorrect, OR entire table columns missing
- **Below 50**: Major content gaps, missing critical benefit details, OR most table data missing

PRIORITIZE CONTENT COMPLETENESS OVER FORMATTING. Missing benefits information, deductibles, coinsurance rates, coverage amounts, or entire table columns should heavily penalize the score.
Provide detailed JSON evaluation covering all criteria."""

        # Build message with file reference
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": evaluation_prompt},
                    {"type": "file", "file": {"file_id": file_id}}
                ]
            }
        ]
        
        # Make API call (only OpenAI for Files API)
        response_text, tokens_used = self.make_api_call(
            messages,
            model=self.evaluation_model,
            temperature=0.1,
            max_tokens=config.anthropic_max_tokens
        )
        
        # Parse JSON response
        evaluation_result = self._parse_json_response(response_text)
        evaluation_result["tokens_used"] = tokens_used
        
        return evaluation_result
    
    def _evaluate_text_based(self, markdown_content: str, original_text: str, 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate markdown against original text extraction."""
        try:
            evaluation_prompt = f"""Evaluate this markdown output for quality and accuracy:

## Original Extracted Text:
{original_text}

## Processed Markdown Output:
{markdown_content}

## Evaluation Focus:
1. **Content Preservation**: Is original content maintained in markdown?
2. **Structure Enhancement**: Are headers and formatting improvements appropriate?
3. **Data Formatting**: Are tables and structured data properly formatted?
4. **Consistency**: Is formatting consistent throughout?
5. **Completeness**: Is any important content missing or corrupted?

Provide comprehensive JSON evaluation."""

            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": evaluation_prompt}
            ]
            
            # Use Anthropic if available, otherwise OpenAI
            if self.use_anthropic:
                response_text, tokens_used = self._make_anthropic_api_call(
                    messages,
                    temperature=config.anthropic_temperature,
                    max_tokens=config.anthropic_max_tokens
                )
            else:
                response_text, tokens_used = self.make_api_call(
                    messages,
                    model=self.evaluation_model,
                    temperature=0.1,
                    max_tokens=config.anthropic_max_tokens
                )
            
            # Parse JSON response - handle markdown code blocks
            evaluation_result = self._parse_json_response(response_text)
            evaluation_result["tokens_used"] = tokens_used
            evaluation_result["evaluation_method"] = f"text_based_{'anthropic' if self.use_anthropic else 'openai'}"
            
            return evaluation_result
            
        except Exception as e:
            self.logger.log_error(f"Text-based evaluation failed: {str(e)}")
            return self._fallback_text_evaluation(markdown_content, original_text)
    
    def _fallback_text_evaluation(self, markdown_content: str, original_text: str) -> Dict[str, Any]:
        """Fallback evaluation using basic heuristics."""
        try:
            # Basic heuristic evaluation
            markdown_words = len(markdown_content.split())
            original_words = len(original_text.split()) if original_text else 0
            
            # Content completeness estimate
            if original_words > 0:
                completeness_ratio = min(1.0, markdown_words / original_words)
                content_score = completeness_ratio * 100
            else:
                content_score = 80.0 if markdown_words > 100 else 40.0
            
            # Structure score based on headers
            header_count = len([line for line in markdown_content.split('\n') if line.startswith('#')])
            structure_score = min(100.0, 60.0 + (header_count * 10))
            
            # Formatting score based on markdown elements
            has_bold = '**' in markdown_content
            has_bullets = any(line.strip().startswith('-') for line in markdown_content.split('\n'))
            has_tables = '|' in markdown_content or 'SELECTED' in markdown_content
            formatting_elements = sum([has_bold, has_bullets, has_tables])
            formatting_score = 60.0 + (formatting_elements * 13.3)
            
            # Data integrity (conservative estimate)
            data_score = 75.0
            
            overall_score = (content_score * 0.3 + structure_score * 0.25 + 
                           data_score * 0.25 + formatting_score * 0.2)
            
            # Determine recommendation based on score
            if overall_score >= 95:
                recommendation = "ACCEPT"
            elif overall_score >= 80:
                recommendation = "REVIEW"
            else:
                recommendation = "REJECT"
            
            # Create issues list based on heuristic analysis
            issues_found = []
            if content_score < 90:
                issues_found.append(f"Content may be incomplete (estimated {content_score:.0f}% complete)")
            if structure_score < 80:
                issues_found.append(f"Limited document structure detected ({header_count} headers)")
            if formatting_score < 80:
                issues_found.append("Formatting elements may be missing")
            if not issues_found:
                issues_found.append("No major issues detected by heuristic analysis")
            
            return {
                "overall_score": round(overall_score, 1),
                "missing_items": [],  # Fixed field name to match expected format
                "added_items": [],    # Fixed field name to match expected format
                "recommendation": recommendation,
                "summary": f"Heuristic evaluation only (visual analysis failed). Score: {overall_score:.1f}/100. " + 
                          f"Word count ratio: {completeness_ratio:.2f}. Issues: {'; '.join(issues_found)}",
                "evaluation_method": "fallback_heuristic",
                "confidence": 0.4,
                "content_completeness": round(content_score, 1),
                "structural_accuracy": round(structure_score, 1),
                "data_integrity": round(data_score, 1),
                "formatting_consistency": round(formatting_score, 1),
                "tokens_used": 0
            }
            
        except Exception as e:
            # Ultimate fallback
            return {
                "overall_score": 50.0,
                "content_completeness": 50.0,
                "structural_accuracy": 50.0,
                "data_integrity": 50.0,
                "formatting_consistency": 50.0,
                "strengths": [],
                "issues_found": [f"Complete evaluation failure: {str(e)}"],
                "missing_content": [],
                "formatting_problems": [],
                "recommendation": "REVIEW",
                "confidence": 0.1,
                "summary": "Evaluation failed completely, requires manual inspection",
                "evaluation_method": "emergency_fallback"
            }
    
    def _select_evaluation_pages(self, pdf_images: List, markdown_content: str) -> List:
        """Select pages for evaluation - use all pages that were actually processed."""
        if not pdf_images:
            return []
        
        # Use ALL pages that were processed by OCR to ensure fair comparison
        # This fixes the evaluation mismatch where OCR processes all pages
        # but evaluation only sees a subset
        total_pages = len(pdf_images)
        
        # For small documents (≤5 pages), use all pages
        if total_pages <= 5:
            return pdf_images
        
        # For larger documents, use a representative sample but ensure
        # we don't miss critical content by being too selective
        key_pages = []
        
        # Always include first 2 pages (often contain most important content)
        key_pages.extend(pdf_images[:2])
        
        # Include middle pages
        if total_pages > 4:
            middle_start = total_pages // 3
            middle_end = (2 * total_pages) // 3
            key_pages.extend(pdf_images[middle_start:middle_end])
        
        # Always include last page
        if total_pages > 2:
            key_pages.append(pdf_images[-1])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_pages = []
        for page in key_pages:
            page_id = id(page)  # Use object identity
            if page_id not in seen:
                seen.add(page_id)
                unique_pages.append(page)
        
        # Limit to 8 pages maximum to prevent token overflow
        return unique_pages[:8]
    
    def _calculate_final_assessment(self, evaluation: Dict[str, Any], 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final assessment and recommendation."""
        overall_score = evaluation.get("overall_score", 50.0)
        
        # Calculate confidence based on evaluation quality
        missing_items = evaluation.get("missing_items", [])
        added_items = evaluation.get("added_items", [])
        
        # Higher confidence if we have specific findings
        if missing_items or added_items:
            confidence = 0.8
        else:
            confidence = 0.9 if overall_score >= 80 else 0.7
        
        evaluation["confidence"] = confidence
        
        # Determine recommendation based on score
        if overall_score >= 90:
            recommendation = "ACCEPT"
        elif overall_score >= 70:
            recommendation = "REVIEW"
        else:
            recommendation = "REJECT"
        
        # Enhanced summary
        quality_level = "Excellent" if overall_score >= 90 else \
                       "Good" if overall_score >= 80 else \
                       "Acceptable" if overall_score >= 70 else \
                       "Poor" if overall_score >= 60 else "Unacceptable"
        
        evaluation["recommendation"] = recommendation
        evaluation["quality_level"] = quality_level
        evaluation["pinecone_ready"] = overall_score >= 80  # Threshold for Pinecone ingestion
        
        return evaluation
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response, handling markdown code blocks and extra content."""
        import json
        import re
        
        # Clean up the response - remove markdown code blocks if present
        cleaned_response = response_text.strip()
        
        # Remove ```json and ``` if present
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]  # Remove ```json
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]   # Remove ```
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]  # Remove trailing ```
        
        cleaned_response = cleaned_response.strip()
        
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            # Try to extract just the JSON portion if there's extra content
            try:
                # Find JSON object boundaries
                json_start = cleaned_response.find('{')
                if json_start == -1:
                    raise ValueError("No JSON object found")
                
                # Find the matching closing brace
                brace_count = 0
                json_end = json_start
                for i, char in enumerate(cleaned_response[json_start:], json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                # Extract just the JSON portion
                json_only = cleaned_response[json_start:json_end]
                return json.loads(json_only)
                
            except (ValueError, json.JSONDecodeError) as e2:
                self.logger.log_error(f"Failed to parse JSON response: {response_text[:500]}...")
                self.logger.log_error(f"Original error: {str(e)}")
                self.logger.log_error(f"Extraction error: {str(e2)}")
                
                # Return a fallback structure matching new format
                return {
                    "missing_items": [{"content": f"Evaluation failed: {str(e)}", "pdf_page": "unknown", "context": "system error"}],
                    "added_items": [],
                    "overall_score": 50.0,
                    "recommendation": "REVIEW",
                    "summary": f"Failed to parse evaluation response: {str(e)}"
                }
    
    def generate_evaluation_report(self, evaluation_data: Dict[str, Any]) -> str:
        """Generate a formatted evaluation report for logging/output."""
        try:
            # Handle comparison mode
            if evaluation_data.get("comparison_mode"):
                return self._generate_comparison_report(evaluation_data)
            
            # Standard single evaluation report
            report_lines = [
                "# Document Processing Quality Report",
                "",
                f"**Overall Score:** {evaluation_data.get('overall_score', 0):.1f}/100",
                f"**Recommendation:** {evaluation_data.get('recommendation', 'UNKNOWN')}",
                f"**Pinecone Ready:** {'✅' if evaluation_data.get('overall_score', 0) >= 80 else '❌'}",
                ""
            ]
            
            # Missing items
            missing_items = evaluation_data.get('missing_items', [])
            if missing_items:
                report_lines.extend(["## Missing Items (from original PDF)", ""])
                for item in missing_items:
                    content = item.get('content', 'Unknown content')
                    pdf_page = item.get('pdf_page', 'Unknown page')
                    context = item.get('context', '')
                    report_lines.append(f"- **Page {pdf_page}**: {content}")
                    if context:
                        report_lines.append(f"  *Context: {context}*")
                report_lines.append("")
            
            # Added items
            added_items = evaluation_data.get('added_items', [])
            if added_items:
                report_lines.extend(["## Added Items (not in original PDF)", ""])
                for item in added_items:
                    content = item.get('content', 'Unknown content')
                    markdown_line = item.get('markdown_line', 'Unknown line')
                    context = item.get('context', '')
                    report_lines.append(f"- **Line ~{markdown_line}**: {content}")
                    if context:
                        report_lines.append(f"  *Context: {context}*")
                report_lines.append("")
            
            # Summary
            summary = evaluation_data.get('summary', 'No summary available')
            report_lines.extend(["## Summary", "", summary])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"Error generating evaluation report: {str(e)}"
    
    def _generate_comparison_report(self, comparison_data: Dict[str, Any]) -> str:
        """Generate a comparison report between OpenAI and Anthropic evaluations."""
        try:
            openai_result = comparison_data.get("openai_result")
            anthropic_result = comparison_data.get("anthropic_result")
            
            report_lines = [
                "# Dual Evaluation Comparison Report",
                "",
                "## Evaluation Method Comparison",
                ""
            ]
            
            # OpenAI Results
            if openai_result:
                method = openai_result.get('evaluation_method', 'visual_comparison_openai')
                is_fallback = 'fallback' in method
                warning = " ⚠️ **FALLBACK MODE**" if is_fallback else ""
                
                report_lines.extend([
                    f"### 🤖 OpenAI GPT-4V Evaluation{warning}",
                    f"**Score:** {openai_result.get('overall_score', 0):.1f}/100",
                    f"**Recommendation:** {openai_result.get('recommendation', 'UNKNOWN')}",
                    f"**Method:** {method}",
                    ""
                ])
            else:
                report_lines.extend(["### 🤖 OpenAI GPT-4V Evaluation", "❌ Failed to complete", ""])
            
            # Anthropic Results  
            if anthropic_result:
                method = anthropic_result.get('evaluation_method', 'visual_comparison_anthropic')
                is_fallback = 'fallback' in method
                warning = " ⚠️ **FALLBACK MODE**" if is_fallback else ""
                
                report_lines.extend([
                    f"### 🧠 Anthropic Claude Evaluation{warning}",
                    f"**Score:** {anthropic_result.get('overall_score', 0):.1f}/100", 
                    f"**Recommendation:** {anthropic_result.get('recommendation', 'UNKNOWN')}",
                    f"**Method:** {method}",
                    ""
                ])
            else:
                report_lines.extend(["### 🧠 Anthropic Claude Evaluation", "❌ Failed to complete", ""])
            
            # Comparison Summary
            if openai_result and anthropic_result:
                openai_score = openai_result.get('overall_score', 0)
                anthropic_score = anthropic_result.get('overall_score', 0)
                score_diff = abs(openai_score - anthropic_score)
                
                report_lines.extend([
                    "## Comparison Summary", 
                    "",
                    f"**Score Difference:** {score_diff:.1f} points",
                    f"**Agreement Level:** {'High' if score_diff < 10 else 'Medium' if score_diff < 20 else 'Low'}",
                    f"**Primary Recommendation:** {anthropic_result.get('recommendation', 'UNKNOWN')} (Anthropic)",
                    ""
                ])
                
                # Show differences in findings
                openai_missing = len(openai_result.get('missing_items', []))
                anthropic_missing = len(anthropic_result.get('missing_items', []))
                openai_added = len(openai_result.get('added_items', []))
                anthropic_added = len(anthropic_result.get('added_items', []))
                
                report_lines.extend([
                    "### Finding Differences",
                    f"**Missing Items:** OpenAI found {openai_missing}, Anthropic found {anthropic_missing}",
                    f"**Added Items:** OpenAI found {openai_added}, Anthropic found {anthropic_added}",
                    ""
                ])
            
            # Include detailed findings from BOTH evaluations
            primary_result = comparison_data.get("primary_result")  
            
            # Show both OpenAI and Anthropic findings
            if openai_result or anthropic_result:
                report_lines.extend(["## Detailed Findings from Both Evaluations", ""])
                
                # OpenAI findings first
                if openai_result:
                    openai_missing = openai_result.get('missing_items', [])
                    openai_added = openai_result.get('added_items', [])
                    openai_method = openai_result.get('evaluation_method', '')
                    is_openai_fallback = 'fallback' in openai_method
                    fallback_note = " (Fallback Mode)" if is_openai_fallback else ""
                    
                    report_lines.extend([f"### 🤖 OpenAI GPT-4V Findings{fallback_note}", ""])
                    
                    if openai_missing:
                        report_lines.extend(["#### Missing Items", ""])
                        for item in openai_missing:
                            content = item.get('content', 'Unknown content')
                            pdf_page = item.get('pdf_page', 'Unknown page')
                            context = item.get('context', '')
                            report_lines.append(f"- **Page {pdf_page}**: {content}")
                            if context:
                                report_lines.append(f"  *Context: {context}*")
                        report_lines.append("")
                    else:
                        report_lines.extend(["#### Missing Items", "✅ No missing items found", ""])
                    
                    if openai_added:
                        report_lines.extend(["#### Added Items", ""])
                        for item in openai_added:
                            content = item.get('content', 'Unknown content')
                            markdown_line = item.get('markdown_line', '')
                            context = item.get('context', '')
                            if markdown_line:
                                report_lines.append(f"- **Line ~{markdown_line}**: {content}")
                            else:
                                report_lines.append(f"- {content}")
                            if context:
                                report_lines.append(f"  *Context: {context}*")
                        report_lines.append("")
                    else:
                        report_lines.extend(["#### Added Items", "✅ No added items found", ""])
                
                # Anthropic findings second  
                if anthropic_result:
                    anthropic_missing = anthropic_result.get('missing_items', [])
                    anthropic_added = anthropic_result.get('added_items', [])
                    anthropic_method = anthropic_result.get('evaluation_method', '')
                    is_anthropic_fallback = 'fallback' in anthropic_method
                    fallback_note = " (Fallback Mode)" if is_anthropic_fallback else ""
                    
                    report_lines.extend([f"### 🧠 Anthropic Claude Findings{fallback_note}", ""])
                    
                    # Add Anthropic's reasoning summary
                    summary = anthropic_result.get('summary', '')
                    if summary:
                        report_lines.extend([
                            "#### Assessment Summary",
                            f"{summary}",
                            ""
                        ])
                    
                    if anthropic_missing:
                        report_lines.extend(["#### Missing Items", ""])
                        for item in anthropic_missing:
                            content = item.get('content', 'Unknown content')
                            pdf_page = item.get('pdf_page', 'Unknown page')
                            context = item.get('context', '')
                            report_lines.append(f"- **Page {pdf_page}**: {content}")
                            if context:
                                report_lines.append(f"  *Context: {context}*")
                        report_lines.append("")
                    else:
                        report_lines.extend(["#### Missing Items", "✅ No missing items found", ""])
                    
                    if anthropic_added:
                        report_lines.extend(["#### Added Items", ""])
                        for item in anthropic_added:
                            content = item.get('content', 'Unknown content')
                            markdown_line = item.get('markdown_line', '')
                            context = item.get('context', '')
                            if markdown_line:
                                report_lines.append(f"- **Line ~{markdown_line}**: {content}")
                            else:
                                report_lines.append(f"- {content}")
                            if context:
                                report_lines.append(f"  *Context: {context}*")
                        report_lines.append("")
                    else:
                        report_lines.extend(["#### Added Items", "✅ No added items found", ""])
            
            # Add final recommendation note
            if primary_result:
                primary_rec = primary_result.get('recommendation', 'UNKNOWN')
                report_lines.extend([
                    "## Final Recommendation",
                    f"**Primary (Anthropic):** {primary_rec}",
                    "*Both evaluations are shown above for comparison*",
                    ""
                ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            return f"Error generating comparison report: {str(e)}"
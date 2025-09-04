"""
Agent-Based OCR Engine
Replacement for direct API calls using intelligent agents
"""

import time
from typing import Dict, Any, Tuple, List
from PIL import Image

from agent_base import AgentOrchestrator
from vision_ocr_agent import VisionOCRAgent
from content_formatting_agent import ContentFormattingAgent
from corruption_agent import CorruptionAgent
from checker_agent import CheckerAgent
from logger import ProcessingLogger
from config import config


class AgentBasedOCREngine:
    """OCR Engine using intelligent agents instead of direct API calls."""
    
    def __init__(self, logger: ProcessingLogger):
        self.logger = logger
        self.api_key = config.openai_api_key
        self.vision_enabled = bool(self.api_key)
        
        # Initialize orchestrator
        self.orchestrator = AgentOrchestrator(logger)
        
        # Initialize all agents
        self.agents = {}
        
        # Corruption Agent (always enabled for intelligent routing)
        if self.vision_enabled:
            self.corruption_agent = CorruptionAgent(logger, config.openai_api_key)
            self.orchestrator.register_agent(self.corruption_agent)
            self.agents["corruption"] = self.corruption_agent
        
        # Vision OCR Agent
        if self.vision_enabled:
            self.vision_agent = VisionOCRAgent(logger, config.openai_api_key)
            self.orchestrator.register_agent(self.vision_agent)
            self.agents["vision"] = self.vision_agent
        
        # Content Formatting Agent (always enabled for consistent output)
        self.formatting_agent = None  # Initialize to None first
        if self.vision_enabled:
            self.formatting_agent = ContentFormattingAgent(logger, config.openai_api_key)
            self.orchestrator.register_agent(self.formatting_agent)
            self.agents["formatting"] = self.formatting_agent
        
        # Checker Agent (always enabled for quality evaluation)
        if self.vision_enabled:
            self.checker_agent = CheckerAgent(logger, config.openai_api_key)
            self.orchestrator.register_agent(self.checker_agent)
            self.agents["checker"] = self.checker_agent
        
        # Track usage
        self.vision_calls_used = 0
        self.total_tokens_used = 0
        
        # Debug data storage for UI tabs
        self.debug_raw_ocr_content = []
        
        # Track text extraction quality metrics
        self.total_word_count = 0
        self.total_char_count = 0
        self.total_line_count = 0
        
        # Debug info stored for final output only
        self.initialization_info = f"Agent-based OCR engine initialized (Agents: {len(self.agents)})"
    
    def process_document_systematically(self, pdf_document, page_ranges: str = "all", 
                                      document_name: str = "Unknown Document") -> Dict[str, Any]:
        """
        Process entire document systematically through all agents in proper sequence.
        
        This is the main entry point for the systematic PDF-to-markdown transformation.
        
        Args:
            pdf_document: PyMuPDF document object
            page_ranges: Page ranges to process (e.g., "1-5, 10, 15-20")
            document_name: Name of the document for reference
            
        Returns:
            Dict containing processed content, evaluation results, and metadata
        """
        start_time = time.time()
        self.logger.log_step(f"🚀 Starting systematic processing: {document_name}")
        
        try:
            # Step 1: Parse page ranges and collect document pages
            pages_to_process = self._parse_page_ranges(pdf_document, page_ranges)
            total_pages = len(pages_to_process)
            
            self.logger.log_step(f"📄 Processing {total_pages} pages")
            
            # Step 2: Process each page through corruption agent and appropriate OCR
            processed_pages = []
            pdf_images = []  # For checker agent
            
            for page_idx, page_num in enumerate(pages_to_process, 1):
                # Check for abort before processing each page
                if hasattr(self, 'is_abort_requested') and self.is_abort_requested():
                    self.logger.log_step("🛑 Systematic processing aborted by user")
                    return {
                        "success": False,
                        "status": "Aborted", 
                        "markdown_content": "",
                        "evaluation": None,
                        "processing_time": time.time() - start_time,
                        "metadata": {
                            "vision_calls_used": 0,
                            "pages_processed": 0
                        }
                    }
                
                self.logger.log_step(f"Processing page {page_idx}/{total_pages} (PDF page {page_num})")
                
                page = pdf_document.load_page(page_num - 1)  # PyMuPDF uses 0-based indexing
                
                # Extract page image for corruption analysis
                pix = page.get_pixmap(dpi=config.dpi)
                img_data = pix.tobytes("png")
                # Convert to base64 for storage
                import base64
                img_base64 = base64.b64encode(img_data).decode()
                pdf_images.append(f"data:image/png;base64,{img_base64}")  # Store for checker
                
                # Convert to PIL Image
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data))
                
                # Step 2a: Use corruption agent to determine OCR method
                page_text = page.get_text()
                
                corruption_input = {
                    "text": page_text,
                    "image": img if self.vision_enabled else None
                }
                
                corruption_context = {
                    "page_number": page_num,
                    "vision_calls_used": self.vision_calls_used,
                    "document_name": document_name
                }
                
                if "corruption" in self.agents:
                    corruption_response = self.corruption_agent.process(corruption_input, corruption_context)
                    
                    if corruption_response.success:
                        recommendation = corruption_response.content
                        method = recommendation["recommended_method"]
                        
                        self.logger.log_step(f"Page {page_num}: {method} recommended (confidence: {recommendation['confidence']:.2f})")
                    else:
                        # Fallback to Tesseract
                        method = "tesseract"
                        self.logger.log_warning(f"Page {page_num}: Corruption analysis failed, using Tesseract")
                else:
                    # Fallback to existing logic
                    method = "tesseract"
                
                # Step 2b: Extract text based on corruption agent recommendation
                if method == "vision_ocr" and "vision" in self.agents:
                    page_content, success = self.extract_with_vision_agent(img, page_num)
                    if success:
                        self.vision_calls_used += 1
                    else:
                        # Fallback to Tesseract
                        page_content = self._extract_with_tesseract(img, page_num)
                elif method == "tesseract":
                    page_content = self._extract_with_tesseract(img, page_num)
                else:
                    # Use PDF text directly
                    page_content = page_text if page_text.strip() else self._extract_with_tesseract(img, page_num)
                
                processed_pages.append(page_content)
            
            # Step 3: Use content formatting agent to process entire document consistently
            if "formatting" in self.agents and processed_pages:
                self.logger.log_step("🎨 Applying consistent formatting across all pages")
                
                formatting_response = self.formatting_agent.process_entire_document(
                    processed_pages,
                    context={
                        "document_name": document_name,
                        "total_pages": total_pages,
                        "processing_mode": "systematic"
                    }
                )
                
                if formatting_response.success:
                    final_markdown = formatting_response.content
                    formatting_confidence = formatting_response.confidence
                    self.total_tokens_used += formatting_response.tokens_used
                    
                    self.logger.log_success(f"✅ Document formatting completed (confidence: {formatting_confidence:.2f})")
                else:
                    # Fallback: join pages with basic formatting
                    final_markdown = "\n\n---\n\n".join(processed_pages)
                    formatting_confidence = 0.5
                    self.logger.log_warning("⚠️ Document formatting failed, using basic joining")
            else:
                # No formatting agent available
                final_markdown = "\n\n---\n\n".join(processed_pages)
                formatting_confidence = 0.5
            
            # Step 4: Use checker agent to evaluate final result against original PDF
            evaluation_result = None
            if "checker" in self.agents:
                self.logger.log_step("🔍 Evaluating final result against original PDF")
                
                checker_input = {
                    "markdown_content": final_markdown,
                    "pdf_images": pdf_images[:5],  # Limit to first 5 pages for evaluation
                    "original_text": "\n".join([pdf_document.load_page(p-1).get_text() for p in pages_to_process[:5]])
                }
                
                checker_context = {
                    "document_name": document_name,
                    "total_pages": total_pages,
                    "debug_info": {
                        "initialization_info": getattr(self, 'initialization_info', 'Agent-based OCR engine')
                    }
                }
                
                evaluation_response = self.checker_agent.process(checker_input, checker_context)
                
                if evaluation_response.success:
                    evaluation_result = evaluation_response.content
                    self.total_tokens_used += evaluation_response.tokens_used
                    
                    score = evaluation_result["overall_score"]
                    recommendation = evaluation_result["recommendation"]
                    
                    self.logger.log_success(f"✅ Quality evaluation completed: {score:.1f}/100 ({recommendation})")
                else:
                    self.logger.log_warning("⚠️ Quality evaluation failed")
            
            processing_time = time.time() - start_time
            
            # Compile final result
            result = {
                "success": True,
                "markdown_content": final_markdown,
                "evaluation": evaluation_result,
                "metadata": {
                    "document_name": document_name,
                    "pages_processed": total_pages,
                    "vision_calls_used": self.vision_calls_used,
                    "total_tokens_used": self.total_tokens_used,
                    "processing_time": processing_time,
                    "formatting_confidence": formatting_confidence,
                    "agents_used": list(self.agents.keys()),
                    "systematic_processing": True
                }
            }
            
            self.logger.log_success(
                f"🎉 Systematic processing completed: {document_name} "
                f"({total_pages} pages, {processing_time:.1f}s)"
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.log_error(f"❌ Systematic processing failed: {str(e)}")
            
            return {
                "success": False,
                "error_message": str(e),
                "metadata": {
                    "document_name": document_name,
                    "processing_time": processing_time,
                    "systematic_processing": True
                }
            }
    
    def _parse_page_ranges(self, pdf_document, page_ranges: str) -> List[int]:
        """Parse page ranges and return list of page numbers to process."""
        if page_ranges == "all" or not page_ranges:
            return list(range(1, len(pdf_document) + 1))
        
        # Use existing utils function if available
        try:
            from utils import validate_page_ranges
            is_valid, error_msg, parsed_pages = validate_page_ranges(page_ranges, len(pdf_document))
            if not is_valid:
                raise ValueError(error_msg)
            # Convert 0-indexed pages back to 1-indexed for processing
            return [p + 1 for p in parsed_pages]
        except ImportError:
            # Simple fallback implementation
            pages = []
            for part in page_ranges.split(","):
                part = part.strip()
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    pages.extend(range(start, end + 1))
                else:
                    pages.append(int(part))
            return sorted(list(set(pages)))
    
    def _extract_with_tesseract(self, img: Image.Image, page_num: int) -> str:
        """Extract text using Tesseract OCR (fallback method)."""
        try:
            import pytesseract
            from PIL import ImageEnhance
            
            self.logger.log_step(f"Page {page_num}: Using Tesseract OCR")
            
            # Basic image preprocessing for better OCR
            img_gray = img.convert('L')
            enhancer = ImageEnhance.Contrast(img_gray)
            img_enhanced = enhancer.enhance(1.5)
            
            # Perform OCR with optimized config
            custom_config = r'--oem 3 --psm 3'
            text = pytesseract.image_to_string(img_enhanced, config=custom_config)
            
            if text.strip():
                self.logger.log_success(f"Page {page_num}: Tesseract extraction successful ({len(text)} chars)")
                
                # Capture Tesseract output for debug tab
                debug_entry = f"Page {page_num} - Tesseract fallback extraction:\n{text}"
                self.debug_raw_ocr_content.append(debug_entry)
                # Debug logging removed - content available through UI tabs
                
                return text
            else:
                self.logger.log_warning(f"Page {page_num}: Tesseract extraction returned no text")
                return f"[Page {page_num}: No text could be extracted]"
                
        except ImportError:
            self.logger.log_error(f"Page {page_num}: Tesseract not available")
            return f"[Page {page_num}: OCR not available]"
        except Exception as e:
            self.logger.log_error(f"Page {page_num}: Tesseract extraction failed: {str(e)}")
            return f"[Page {page_num}: OCR extraction failed: {str(e)}]"
    
    def extract_with_vision_agent(self, img: Image.Image, page_num: int, 
                                 strategy: str = "standard") -> Tuple[str, bool]:
        """Extract text using Vision OCR Agent."""
        if not self.vision_enabled:
            return "", False
        
        try:
            # Prepare input for agent
            input_data = {
                "image": img,
                "page_number": page_num
            }
            
            context = {
                "strategy": strategy,
                "retry_count": 0,
                "quality_issues": False  # Could be determined by image analysis
            }
            
            # Execute agent
            response = self.vision_agent.process(input_data, context)
            
            # Track Vision API call
            # Analytics removed - can be added back later if needed
            
            # Track agent performance
            # Analytics removed - can be added back later if needed
            
            # Track usage
            if response.success:
                self.vision_calls_used += 1
                self.total_tokens_used += (response.tokens_used or 0)
                # Reduced logging for clean output
                
                # Track text extraction quality
                self.total_word_count += len(response.content.split()) if response.content else 0
                self.total_char_count += len(response.content) if response.content else 0
                self.total_line_count += len(response.content.split('\n')) if response.content else 0
                
                # Store confidence for potential fallback decisions
                if response.confidence < 0.6:
                    self.logger.log_warning(f"Low confidence vision extraction: {response.confidence:.2f}")
                
                # Capture raw OCR content for debug tab
                if response.content and response.content.strip():
                    debug_entry = f"Page {page_num} - {strategy} extraction:\n{response.content}"
                    self.debug_raw_ocr_content.append(debug_entry)
                    # Debug logging removed - content available through UI tabs
                
                return response.content, True
            else:
                self.logger.log_error(f"Vision agent failed: {response.error_message}")
                
                return "", False
                
        except Exception as e:
            self.logger.log_error(f"Vision agent execution error: {str(e)}")
            return "", False
    
    def format_content_with_agent(self, text: str, page_num: int, 
                                 filename: str = "", document_title: str = "") -> str:
        """Format content using Content Formatting Agent."""
        if not text or not text.strip():
            return text
        if not self.formatting_agent:
            # Formatting agent disabled; return text as-is
            return text
        
        try:
            # Determine a document title: use provided title or derive from filename
            title_to_use = document_title
            if not title_to_use and filename:
                base = filename.rsplit('/', 1)[-1]  # strip directories
                stem = base.rsplit('.', 1)[0]       # remove extension
                # Clean to a readable title
                title_to_use = stem.replace('-', ' ').replace('_', ' ').strip().title()

            # Prepare input for agent
            input_data = {
                "text": text,
                "page_number": page_num,
                "document_title": title_to_use
            }
            
            context = {
                "page_number": page_num,
                "document_title": title_to_use,
                "pipeline_stage": "content_formatting"
            }
            
            # Execute agent
            start_agent_time = time.time()
            response = self.formatting_agent.process(input_data, context)
            self.response_processing_time = time.time() - start_agent_time
            
            # Track usage
            if response.success:
                self.total_tokens_used += response.tokens_used
                self.logger.log_success(f"Content formatting completed ({response.confidence:.2f} confidence)")
                return response.content
            else:
                self.logger.log_error(f"Content formatting failed: {response.error_message}")
                return text  # Return original text if formatting fails
                
        except Exception as e:
            self.logger.log_error(f"Content formatting agent error: {str(e)}")
            return text
    
    def extract_page_text_with_agents(self, page, img: Image.Image, page_num: int, filename: str = "") -> str:
        """
        Complete page text extraction using agent pipeline.
        Replacement for the original extract_page_text method.
        """
        start_time = time.time()
        
        # Try to extract PDF text first (non-agent)
        pdf_text = page.get_text()
        
        if pdf_text and pdf_text.strip():
            # Use existing corruption detection logic
            from corruption_detector import CorruptionDetector
            detector = CorruptionDetector()
            
            corruption_score, detailed_scores = detector.calculate_corruption_score_detailed(pdf_text)
            is_corrupted = corruption_score > config.vision_corruption_threshold
            has_table_patterns = detailed_scores.get('table_patterns', 0) > 0
            
            # Track corruption detection results
            
            # Decision logic for agent usage - ALWAYS use agent for consistency
            if not is_corrupted and not has_table_patterns:
                if self.formatting_agent:
                    self.logger.info(f"Page {page_num}: Clean PDF text detected, using formatting agent")
                    method_start_time = time.time()
                    formatted_text = self.format_content_with_agent(pdf_text, page_num, filename=filename)
                    self.formatting_processing_time = time.time() - method_start_time
                    return formatted_text
                else:
                    self.logger.info(f"Page {page_num}: Clean PDF text detected, formatting agent disabled; returning raw PDF text")
                    return pdf_text
            
            # Determine optimal strategy based on content analysis
            strategy = self._determine_extraction_strategy(detailed_scores, pdf_text)
            
            if has_table_patterns:
                self.logger.info(f"Page {page_num}: Table patterns detected, using agent pipeline")
            else:
                self.logger.info(f"Page {page_num}: Corruption detected, using vision agent")
            
            # Use Vision Agent for corrupted/complex content
            if self.vision_enabled:
                method_start_time = time.time()
                vision_text, success = self.extract_with_vision_agent(img, page_num, strategy)
                self.vision_processing_time = time.time() - method_start_time
                
                if success and vision_text:
                    if self.formatting_agent:
                        # Format the vision-extracted text
                        formatted_text = self.format_content_with_agent(vision_text, page_num, filename=filename)
                        return formatted_text
                    else:
                        # No formatting agent; return raw vision text
                        return vision_text
                else:
                    pass
        
        # Fallback to Tesseract (non-agent) if PDF text unavailable
        self.logger.info(f"Page {page_num}: Using Tesseract OCR fallback")
        
        # Track method timing
        method_start_time = time.time()
        tesseract_text = self._extract_with_tesseract(img, page_num)  # This now captures debug data
        self.tesseract_processing_time = time.time() - method_start_time
        
        # Format Tesseract output with agent if available
        if tesseract_text:
            if self.formatting_agent:
                formatted_text = self.format_content_with_agent(tesseract_text, page_num, filename=filename)
                return formatted_text
            else:
                return tesseract_text
        
        # Track page processing completion
        self.page_processing_time = time.time() - start_time
        
        return f"## Page {page_num}\n\n[No text extracted]"
    
    def batch_process_with_agents(self, pages_data: list) -> Dict[int, str]:
        """Process multiple pages using agent pipeline."""
        results = {}
        
        for page_data in pages_data:
            page_num = page_data["page_number"]
            page = page_data["page"]
            img = page_data["image"]
            
            try:
                extracted_text = self.extract_page_text_with_agents(page, img, page_num)
                results[page_num] = extracted_text
                
            except Exception as e:
                self.logger.log_error(f"Batch processing failed for page {page_num}: {e}")
                results[page_num] = f"## Page {page_num}\n\n[Error: {str(e)}]"
        
        return results
    
    def execute_full_pipeline(self, pages_data: list, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute complete agent pipeline for multiple pages."""
        context = context or {}
        
        # Define agent sequence dynamically based on available agents and context
        wants_vision = context.get("has_complex_content", False)
        agent_sequence = []
        if wants_vision and self.vision_enabled:
            agent_sequence.append("vision_ocr_agent")
        if self.formatting_agent:
            agent_sequence.append("content_formatting_agent")
        
        pipeline_results = {}
        total_tokens = 0
        total_time = 0
        
        for page_data in pages_data:
            page_num = page_data["page_number"]
            
            if "vision_ocr_agent" in agent_sequence:
                # Full pipeline with vision extraction
                # Debug logging removed - verbose output moved to UI only
                
                input_data = {
                    "image": page_data["image"],
                    "page_number": page_num
                }
                
                stage_context = {
                    **context,
                    "current_page": page_num,
                    "total_pages": len(pages_data)
                }
                
                results = self.orchestrator.execute_pipeline(
                    input_data, agent_sequence, stage_context
                )
                
            else:
                # Format-only pipeline
                pdf_text = page_data["page"].get_text()
                if self.formatting_agent:
                    input_data = {"text": pdf_text, "page_number": page_num}
                    results = self.orchestrator.execute_pipeline(
                        input_data, ["content_formatting_agent"], context
                    )
                else:
                    # No formatting agent; synthesize a minimal results dict
                    class _SimpleResult:
                        def __init__(self, content: str):
                            self.success = True
                            self.content = content
                            self.confidence = 1.0
                            self.tokens_used = 0
                            self.processing_time = 0.0
                    results = {"raw_text": _SimpleResult(pdf_text or "")}
            
            # Collect results
            pipeline_results[page_num] = results
            
            # Track totals
            for agent_result in results.values():
                total_tokens += getattr(agent_result, 'tokens_used', 0) or 0
                total_time += getattr(agent_result, 'processing_time', 0.0) or 0.0
        
        # Get pipeline summary
        summary = self.orchestrator.get_pipeline_summary()
        summary.update({
            "total_tokens_used": total_tokens,
            "total_processing_time": total_time,
            "pages_processed": len(pages_data)
        })
        
        return {
            "results": pipeline_results,
            "summary": summary
        }
    
    def _determine_extraction_strategy(self, detailed_scores: Dict[str, float], text: str) -> str:
        """Determine optimal extraction strategy based on content analysis."""
        if detailed_scores.get('table_patterns', 0) > 0.3:
            return "table_focused"
        elif any(pattern in text.lower() for pattern in ['form', 'checkbox', '☐', '☑','x']):
            return "form_focused"
        elif any(pattern in text for pattern in ['def ', 'class ', 'import ', '$']):
            return "technical_doc"
        else:
            return "standard"
    
    # REMOVED DUPLICATE METHOD - Using the first _extract_with_tesseract at line 304
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics from all agents."""
        stats = {
            "vision_calls_used": self.vision_calls_used,
            "total_tokens_used": self.total_tokens_used,
            "vision_enabled": self.vision_enabled,
            "formatting_enabled": bool(self.formatting_agent),
            "agents_registered": len(self.orchestrator.agents)
        }
        
        # Add agent-specific stats
        for agent_id, agent in self.orchestrator.agents.items():
            stats[f"{agent_id}_confidence_scores"] = agent.state.confidence_scores
            stats[f"{agent_id}_memory_entries"] = len(agent.state.memory)
            
        return stats
    
    def get_debug_raw_ocr_content(self) -> str:
        """Get captured raw OCR content for debugging."""
        if self.debug_raw_ocr_content:
            return '\n\n' + ('='*100 + '\n\n').join(self.debug_raw_ocr_content)
        return "No raw OCR content captured yet. Process a document to see raw vision extraction results."
    
    def clear_debug_data(self):
        """Clear captured debug data."""
        self.debug_raw_ocr_content.clear()
    
    def reset_agents(self) -> None:
        """Reset all agents to initial state."""
        self.clear_debug_data()  # Clear debug data when resetting
        for agent in self.orchestrator.agents.values():
            agent.state.memory.clear()
            agent.state.confidence_scores.clear()
            agent.state.error_history.clear()
            
        self.vision_calls_used = 0
        self.total_tokens_used = 0
        
        self.logger.log_step("All agents reset to initial state")
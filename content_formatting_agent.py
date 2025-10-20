"""
Content Formatting Agent
Specialized agent for transforming raw OCR text into structured, formatted content
"""

import time
import re
from typing import Dict, Any, List, Tuple, Optional

from agent_base import BaseAgent, AgentResponse
from logger import ProcessingLogger
from config import config
from prompts import get_content_formatting_prompt
from api_client import APIClient



class ContentFormattingAgent(BaseAgent):
    """Agent specialized for content formatting and structuring."""
    
    def __init__(self, logger: ProcessingLogger, api_client: Optional[APIClient] = None):
        """Initialize the ContentFormattingAgent.
        
        Args:
            logger: Logger instance for recording activities
            api_client: Optional APIClient instance (will be created if not provided)
        """
        super().__init__("content_formatting_agent", logger, api_client=api_client)
        # Formatting modules removed - using strategy-based approach instead
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for content formatting."""
        return get_content_formatting_prompt()
    
    def process(self, input_data: Any, context: Dict[str, Any] = None) -> AgentResponse:
        """Process raw text and apply intelligent formatting."""
        start_time = time.time()
        context = context or {}
        
        try:
            # Handle different input types
            if isinstance(input_data, str):
                raw_text = input_data
            elif isinstance(input_data, dict):
                raw_text = input_data.get("text", "")
            else:
                raw_text = str(input_data)

            # Check for empty or error text
            if not raw_text.strip():
                return AgentResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    error_message="No text provided for formatting"
                )

            # Check if text is an OCR error message
            if raw_text.strip().startswith("[Page") and "No text could be extracted" in raw_text:
                return AgentResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    error_message="OCR extraction failed - no text was extracted from the document"
                )

            # Check for suspiciously short text that's likely just URLs or metadata
            if len(raw_text.strip()) < 200:
                # Check if it's mostly URLs
                import re
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, raw_text)
                if urls and len(''.join(urls)) > len(raw_text.strip()) * 0.7:
                    return AgentResponse(
                        success=False,
                        content="",
                        confidence=0.0,
                        error_message=f"Document appears to be image-based with minimal extractable text (only {len(raw_text.strip())} chars: '{raw_text.strip()[:100]}'). Please use Vision OCR instead."
                    )
            
            # Analyze content and determine formatting approach
            content_analysis = self._analyze_content(raw_text)
            formatting_strategy = self._determine_strategy(content_analysis, context)
            
            # Debug logging removed - verbose output moved to UI only
            
            self.add_memory("formatting_request", {
                "text_length": len(raw_text),
                "strategy": formatting_strategy,
                "detected_elements": content_analysis
            })
            
            # Execute multi-stage formatting
            formatted_content, reasoning_steps, tokens_used = self._execute_formatting_pipeline(
                raw_text, formatting_strategy, content_analysis, context
            )

            # Clean up any problematic markdown tables that may have been generated
            cleaned_content = self._clean_markdown_tables(formatted_content)
            if cleaned_content != formatted_content:
                reasoning_steps.append("Applied post-processing cleanup to remove problematic markdown tables")
                formatted_content = cleaned_content

            # Convert footnotes to inline format if requested
            if context.get("convert_footnotes", False):
                footnote_processor = self._FootnoteProcessor(context)
                footnote_processed = footnote_processor.convert_footnotes_to_inline(formatted_content)
                if footnote_processed != formatted_content:
                    reasoning_steps.append("Converted footnotes to inline parenthetical format")
                    formatted_content = footnote_processed

            # Debug logging removed - verbose output moved to UI only
            
            # Calculate confidence
            confidence = self._calculate_formatting_confidence(
                raw_text, formatted_content, content_analysis
            )
            
            # Update state
            self.update_state("last_formatting_strategy", formatting_strategy)
            self.state.confidence_scores["formatting"] = confidence
            
            processing_time = time.time() - start_time
            
            response = AgentResponse(
                success=True,
                content=formatted_content,
                confidence=confidence,
                metadata={
                    "formatting_strategy": formatting_strategy,
                    "content_analysis": content_analysis,
                    "original_length": len(raw_text),
                    "formatted_length": len(formatted_content),
                    "compression_ratio": len(formatted_content) / len(raw_text) if raw_text else 1.0
                },
                reasoning_steps=reasoning_steps,
                tokens_used=tokens_used,
                processing_time=processing_time
            )
            
            self.logger.log_success(f"Content formatting completed (confidence: {confidence:.2f})")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.log_error(f"Content formatting failed: {str(e)}")
            return AgentResponse(
                success=False,
                content="",
                confidence=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _analyze_content(self, text: str) -> Dict[str, Any]:
        """Analyze text content to determine formatting needs."""
        analysis = {
            "has_tables": False,
            "has_checkboxes": False,
            "has_lists": False,
            "has_technical_content": False,
            "structure_complexity": "simple",
            "estimated_sections": 1,
            "line_count": len(text.split('\n')),
            "word_count": len(text.split())
        }
        
        # Table detection
        table_indicators = ["|", "─", "┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼"]
        if any(indicator in text for indicator in table_indicators) or \
           len(re.findall(r'\s{4,}', text)) > 5:  # Multiple large spaces (column alignment)
            analysis["has_tables"] = True
        
        # Enhanced checkbox detection - look for common patterns
        checkbox_patterns = [
            r'\[[ x✓]\]',  # [x], [ ], [✓]
            r'☐', r'☑',    # checkbox symbols
            r'✓', r'✔',    # checkmarks
            r'^\s*[x✓✔]\s+\([a-z]\)',  # x (a), ✓ (b) at start of line
            r'^\s*¨\s+\([a-z]\)',      # ¨ (a) unchecked at start of line
            r'^\s*[x✓✔]\s+\([a-z][a-z]?\)',  # x (ii), ✓ (iii) at start of line
        ]
        if any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in checkbox_patterns):
            analysis["has_checkboxes"] = True
        
        # List detection
        if re.search(r'^\s*[-•*]\s', text, re.MULTILINE) or \
           re.search(r'^\s*\d+\.\s', text, re.MULTILINE):
            analysis["has_lists"] = True
        
        # Technical content detection
        technical_patterns = [
            r'\$[^$]+\$',  # LaTeX math
            r'[A-Z][a-z]*\d+',  # Chemical formulas
            r'def\s+\w+\(',  # Function definitions
            r'class\s+\w+',  # Class definitions
            r'import\s+\w+',  # Import statements
        ]
        if any(re.search(pattern, text) for pattern in technical_patterns):
            analysis["has_technical_content"] = True
        
        # Structure complexity
        section_headers = len(re.findall(r'^[A-Z][^.!?]*:?\s*$', text, re.MULTILINE))
        if section_headers > 5:
            analysis["structure_complexity"] = "complex"
        elif section_headers > 2:
            analysis["structure_complexity"] = "moderate"
        
        analysis["estimated_sections"] = max(1, section_headers)
        
        return analysis
    
    def _determine_strategy(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determine optimal formatting strategy based on content analysis."""
        # Priority-based strategy selection - CHECKBOX FORMATTING HAS HIGHEST PRIORITY
        if analysis["has_checkboxes"] and analysis["has_tables"]:
            return "comprehensive"
        elif analysis["has_checkboxes"]:
            return "form_focused"  # Checkboxes get priority over tables
        elif analysis["has_tables"]:
            return "table_focused"
        elif analysis["has_technical_content"]:
            return "technical"
        elif analysis["structure_complexity"] == "complex":
            return "structure_focused"
        else:
            return "standard"
    
    def _execute_formatting_pipeline(self, text: str, strategy: str, analysis: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Tuple[str, List[str], int]:
        """Execute the formatting pipeline based on strategy."""
        reasoning_steps = [f"Executing {strategy} formatting strategy"]
        
        if strategy == "comprehensive":
            # Multi-stage processing for complex documents
            return self._comprehensive_formatting(text, analysis, context, reasoning_steps)
        
        elif strategy == "table_focused":
            return self._table_focused_formatting(text, analysis, context, reasoning_steps)
        
        elif strategy == "form_focused":
            return self._form_focused_formatting(text, analysis, context, reasoning_steps)
        
        elif strategy == "technical":
            return self._technical_formatting(text, analysis, context, reasoning_steps)
        
        else:
            return self._standard_formatting(text, analysis, context, reasoning_steps)
    
    def _comprehensive_formatting(self, text: str, analysis: Dict[str, Any], 
                                 context: Dict[str, Any], reasoning_steps: List[str]) -> Tuple[str, List[str], int]:
        """Comprehensive formatting for complex documents."""
        reasoning_steps.append("Applying comprehensive multi-stage formatting")
        
        comprehensive_prompt = f"""Format this document applying the system rules consistently:

{text}"""

        messages = [
            {
                "role": "system",
                "content": self.get_system_prompt()
            },
            {
                "role": "user",
                "content": comprehensive_prompt
            }
        ]
        
        try:
            formatted_text, tokens_used = self.make_api_call(
                messages,
                model=config.openai_model,
                temperature=0.1,
                max_tokens=config.max_output_tokens
            )
            # Clean AI metadata from output
            formatted_text, removed_metadata = self._clean_ai_metadata(formatted_text)
            if removed_metadata:
                reasoning_steps.append(f"Cleaned {len(removed_metadata)} AI metadata fragment(s) from formatting output")
            reasoning_steps.append("Successfully applied comprehensive formatting")
            return formatted_text, reasoning_steps, tokens_used
            
        except Exception as e:
            reasoning_steps.append(f"Comprehensive formatting failed: {str(e)}")
            return text, reasoning_steps, 0
    
    def _table_focused_formatting(self, text: str, analysis: Dict[str, Any], 
                                 context: Dict[str, Any], reasoning_steps: List[str]) -> Tuple[str, List[str], int]:
        """Formatting focused on table processing."""
        reasoning_steps.append("Applying table-focused formatting with consistent rules")
        
        table_prompt = f"""Format this content with focus on table structure:

{text}"""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": table_prompt}
        ]
        
        try:
            formatted_text, tokens_used = self.make_api_call(messages)
            formatted_text, removed_metadata = self._clean_ai_metadata(formatted_text)
            if removed_metadata:
                reasoning_steps.append(f"Cleaned {len(removed_metadata)} AI metadata fragment(s) from formatting output")
            reasoning_steps.append("Successfully applied table-focused formatting")
            return formatted_text, reasoning_steps, tokens_used
        except Exception as e:
            reasoning_steps.append(f"Table formatting failed: {str(e)}")
            return text, reasoning_steps, 0
    
    def _form_focused_formatting(self, text: str, analysis: Dict[str, Any], 
                                context: Dict[str, Any], reasoning_steps: List[str]) -> Tuple[str, List[str], int]:
        """Formatting focused on form elements and checkboxes."""
        reasoning_steps.append("Applying form-focused formatting with table consistency")
        
        form_prompt = f"""Format this content with focus on form elements and checkboxes:

{text}"""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": form_prompt}
        ]
        
        try:
            formatted_text, tokens_used = self.make_api_call(messages)
            reasoning_steps.append("Successfully applied form-focused formatting")
            return formatted_text, reasoning_steps, tokens_used
        except Exception as e:
            reasoning_steps.append(f"Form formatting failed: {str(e)}")
            return text, reasoning_steps, 0
    
    def _technical_formatting(self, text: str, analysis: Dict[str, Any], 
                             context: Dict[str, Any], reasoning_steps: List[str]) -> Tuple[str, List[str], int]:
        """Formatting for technical documents with code, formulas, etc."""
        reasoning_steps.append("Applying technical document formatting")
        
        technical_prompt = f"""Format this technical document preserving formulas, notation, and technical terms:

{text}"""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": technical_prompt}
        ]
        
        try:
            formatted_text, tokens_used = self.make_api_call(messages)
            reasoning_steps.append("Successfully applied technical formatting")
            return formatted_text, reasoning_steps, tokens_used
        except Exception as e:
            reasoning_steps.append(f"Technical formatting failed: {str(e)}")
            return text, reasoning_steps, 0
    
    def _standard_formatting(self, text: str, analysis: Dict[str, Any], 
                            context: Dict[str, Any], reasoning_steps: List[str]) -> Tuple[str, List[str], int]:
        """Standard formatting for general documents."""
        reasoning_steps.append("Applying standard document formatting with consistent rules")
        
        standard_prompt = f"""Format this content according to the system rules:

{text}"""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": standard_prompt}
        ]
        
        try:
            formatted_text, tokens_used = self.make_api_call(messages)
            formatted_text, removed_metadata = self._clean_ai_metadata(formatted_text)
            if removed_metadata:
                reasoning_steps.append(f"Cleaned {len(removed_metadata)} AI metadata fragment(s) from formatting output")
            reasoning_steps.append("Successfully applied standard formatting")
            return formatted_text, reasoning_steps, tokens_used
        except Exception as e:
            reasoning_steps.append(f"Standard formatting failed: {str(e)}")
            return text, reasoning_steps, 0
    
    def _calculate_formatting_confidence(self, original_text: str, formatted_text: str, 
                                        analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for formatting quality."""
        base_confidence = 0.85
        
        # Length comparison
        length_ratio = len(formatted_text) / len(original_text) if original_text else 1.0
        if length_ratio < 0.5:  # Too much content lost
            base_confidence -= 0.3
        elif length_ratio > 2.0:  # Too much content added
            base_confidence -= 0.2
        elif 0.8 <= length_ratio <= 1.2:  # Good balance
            base_confidence += 0.05
        
        # Structure indicators
        markdown_headers = len(re.findall(r'^#{2,3}\s', formatted_text, re.MULTILINE))
        if analysis.get("estimated_sections", 1) > 1 and markdown_headers > 0:
            base_confidence += 0.05
        
        # Special element handling
        if analysis.get("has_tables", False) and "**" in formatted_text:
            base_confidence += 0.05
        if analysis.get("has_checkboxes", False) and "[SELECTED]" in formatted_text:
            base_confidence += 0.05
        
        # Quality indicators
        if len(formatted_text.split('\n')) > len(original_text.split('\n')) * 0.5:
            base_confidence += 0.05  # Good paragraph structure
        
        return max(0.0, min(1.0, base_confidence))
    
    def process_entire_document(self, document_pages: List[str], context: Dict[str, Any] = None) -> AgentResponse:
        """Process entire document with consistent formatting across all pages."""
        start_time = time.time()
        context = context or {}

        try:
            # Combine all pages for analysis
            full_document = "\n\n---PAGE BREAK---\n\n".join(document_pages)

            # Check for empty or minimal content
            if not full_document.strip():
                return AgentResponse(
                    success=False,
                    content="",
                    confidence=0.0,
                    error_message="No text provided for formatting"
                )

            # Check for suspiciously short text that's likely just URLs or metadata
            if len(full_document.strip()) < 200:
                # Check if it's mostly URLs
                import re
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, full_document)
                if urls and len(''.join(urls)) > len(full_document.strip()) * 0.7:
                    return AgentResponse(
                        success=False,
                        content="",
                        confidence=0.0,
                        error_message=f"Document appears to be image-based with minimal extractable text (only {len(full_document.strip())} chars: '{full_document.strip()[:100]}'). Please use Vision OCR instead."
                    )
            
            self.add_memory("document_formatting_request", {
                "total_pages": len(document_pages),
                "total_length": len(full_document),
                "processing_mode": "complete_document"
            })

            # Check if this is a simple text document that doesn't need formatting
            if self._is_simple_text_document(document_pages, full_document):
                self.logger.log_step("📝 Simple text document detected, skipping formatting for speed")
                processing_time = time.time() - start_time
                return AgentResponse(
                    success=True,
                    content="\n\n".join(document_pages),  # Just join with paragraph breaks
                    confidence=0.9,
                    metadata={
                        "total_pages": len(document_pages),
                        "formatting_strategy": "simple_text_skip",
                        "processing_mode": "fast_path",
                        "skipped_reason": "No complex formatting needed"
                    },
                    reasoning_steps=["Detected simple text document", "Skipped formatting for performance"],
                    tokens_used=0,
                    processing_time=processing_time
                )

            # Analyze entire document structure
            document_analysis = self._analyze_document_structure(document_pages)
            formatting_strategy = self._determine_document_strategy(document_analysis, context)
            
            # Execute document-wide formatting
            formatted_content, reasoning_steps, tokens_used = self._execute_document_formatting(
                full_document, document_pages, formatting_strategy, document_analysis, context
            )
            
            # Post-processing: ensure no pipe-style markdown tables remain
            cleaned_doc_content = self._clean_markdown_tables(formatted_content)
            if cleaned_doc_content != formatted_content:
                reasoning_steps.append("Applied document-level cleanup to remove markdown pipe tables")
                formatted_content = cleaned_doc_content
            
            # Calculate confidence based on document coherence
            confidence = self._calculate_document_formatting_confidence(
                document_pages, formatted_content, document_analysis
            )
            
            processing_time = time.time() - start_time
            
            response = AgentResponse(
                success=True,
                content=formatted_content,
                confidence=confidence,
                metadata={
                    "total_pages": len(document_pages),
                    "formatting_strategy": formatting_strategy,
                    "document_analysis": document_analysis,
                    "processing_mode": "complete_document",
                    "consistency_score": self._calculate_consistency_score(formatted_content)
                },
                reasoning_steps=reasoning_steps,
                tokens_used=tokens_used,
                processing_time=processing_time
            )
            
            self.logger.log_success(
                f"Document formatting completed: {len(document_pages)} pages "
                f"(confidence: {confidence:.2f}, strategy: {formatting_strategy})"
            )
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.log_error(f"Document formatting failed: {str(e)}")
            return AgentResponse(
                success=False,
                content="",
                confidence=0.0,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _is_simple_text_document(self, document_pages: List[str], full_document: str) -> bool:
        """Detect simple text-only documents that don't need complex formatting.

        Returns True if document is simple text (plain prose, no tables/forms/structure)
        Returns False if document needs formatting (has tables, forms, complex structure)
        """
        # Quick check: if very short, always format
        if len(document_pages) <= 3:
            return False

        # Check for complexity indicators
        has_tables = any(indicator in full_document for indicator in ["|", "─", "┌", "┐", "└", "┘"])
        has_checkboxes = bool(re.search(r'\[[ x✓✔]\]|☐|☑|✓|✔', full_document))

        # Check for structured data patterns (many aligned spaces = likely tabular)
        aligned_spaces = len(re.findall(r'\w\s{4,}\w', full_document))
        has_aligned_columns = aligned_spaces > len(document_pages) * 3  # 3+ per page avg

        # Check for structural headers
        headers = len(re.findall(r'^[A-Z][^.!?]*:?\s*$', full_document, re.MULTILINE))
        has_structure = headers > len(document_pages) * 2  # 2+ headers per page avg

        # Check for lists (more than simple occasional bullets)
        bullet_lines = len(re.findall(r'^\s*[-•*]\s', full_document, re.MULTILINE))
        numbered_lines = len(re.findall(r'^\s*\d+\.\s', full_document, re.MULTILINE))
        has_lists = (bullet_lines + numbered_lines) > len(document_pages) * 3  # 3+ list items per page

        # Simple text = no tables, no forms, minimal structure, not heavily listed
        is_simple = (
            not has_tables and
            not has_checkboxes and
            not has_aligned_columns and
            not has_structure and
            not has_lists
        )

        if is_simple:
            self.logger.log_step(
                f"✅ Simple text detected: no tables, forms, or complex structure "
                f"(headers: {headers}, bullets: {bullet_lines}, numbered: {numbered_lines})"
            )

        return is_simple

    def _analyze_document_structure(self, document_pages: List[str]) -> Dict[str, Any]:
        """Analyze entire document structure for consistent formatting."""
        analysis = {
            "total_pages": len(document_pages),
            "has_tables": False,
            "has_forms": False,
            "has_complex_structure": False,
            "consistent_elements": [],
            "formatting_challenges": [],
            "section_structure": "simple"
        }
        
        table_pages = 0
        form_pages = 0
        
        for page_num, page_text in enumerate(document_pages, 1):
            # Table detection across pages
            if any(indicator in page_text for indicator in ["|", "─", "┌", "┐"]) or \
               len(re.findall(r'\w\s{4,}\w', page_text)) > 3:
                table_pages += 1
                analysis["has_tables"] = True
            
            # Form detection across pages
            checkbox_patterns = [r'\[[ x✓✔]\]', r'☐', r'☑', r'✓', r'✔', r'^\s*[x✓✔¨]\s*\([a-z]+\)']
            if any(re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE) for pattern in checkbox_patterns):
                form_pages += 1
                analysis["has_forms"] = True
        
        # Document complexity assessment
        if table_pages > len(document_pages) * 0.3:  # 30%+ pages have tables
            analysis["consistent_elements"].append("tables_throughout")
            analysis["formatting_challenges"].append("consistent_table_formatting")
        
        if form_pages > 0:
            analysis["consistent_elements"].append("form_elements")
            analysis["formatting_challenges"].append("checkbox_standardization")
        
        # Section structure analysis
        total_headers = 0
        for page_text in document_pages:
            headers = len(re.findall(r'^[A-Z][^.!?]*:?\s*$', page_text, re.MULTILINE))
            total_headers += headers
        
        if total_headers > len(document_pages) * 2:  # More than 2 headers per page average
            analysis["section_structure"] = "complex"
            analysis["has_complex_structure"] = True
        elif total_headers > len(document_pages):
            analysis["section_structure"] = "moderate"
        
        return analysis
    
    def _determine_document_strategy(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determine document-wide formatting strategy."""
        if analysis.get("has_tables") and analysis.get("has_forms"):
            return "comprehensive_document"
        elif analysis.get("has_tables") and "tables_throughout" in analysis.get("consistent_elements", []):
            return "table_heavy_document"
        elif analysis.get("has_forms"):
            return "form_document"
        elif analysis.get("has_complex_structure"):
            return "structured_document"
        else:
            return "standard_document"
    
    def _execute_document_formatting(self, full_document: str, document_pages: List[str],
                                   strategy: str, analysis: Dict[str, Any],
                                   context: Dict[str, Any]) -> Tuple[str, List[str], int]:
        """Execute document-wide formatting with consistency enforcement."""
        reasoning_steps = [f"Processing {len(document_pages)} pages with {strategy} strategy"]

        # Check document size - if too large (>5 pages or >50k chars), use chunked processing
        total_chars = len(full_document)
        page_count = len(document_pages)

        if page_count > 5 or total_chars > 50000:
            reasoning_steps.append(f"Document too large ({page_count} pages, {total_chars} chars) - using chunked processing")
            return self._chunked_document_formatting(document_pages, strategy, reasoning_steps)

        document_prompt = f"""Format this complete document with strict consistency across all pages.

DOCUMENT ANALYSIS:
- Total Pages: {len(document_pages)}
- Structure: {analysis.get('section_structure', 'simple')}
- Contains Tables: {analysis.get('has_tables', False)}
- Contains Forms: {analysis.get('has_forms', False)}
- Strategy: {strategy}

CONSISTENCY REQUIREMENTS:
1. **Uniform Table Formatting**: All tables must use identical flattened format
2. **Header Hierarchy**: Consistent ## and ### usage throughout
3. **Form Element Standards**: All checkboxes formatted identically
4. **Terminology Consistency**: Same terms used throughout document
5. **Vector Store Optimization**: Structure for optimal search and retrieval

COMPLETE DOCUMENT TO FORMAT:
{full_document}"""

        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": document_prompt}
        ]

        try:
            formatted_text, tokens_used = self.make_api_call(
                messages,
                model=config.openai_model,
                temperature=0.05,  # Lower temperature for consistency
                max_tokens=config.max_output_tokens
            )

            reasoning_steps.append("Applied document-wide consistent formatting")
            reasoning_steps.append("Enforced cross-page formatting standards")

            return formatted_text, reasoning_steps, tokens_used

        except Exception as e:
            reasoning_steps.append(f"Document formatting failed: {str(e)}")
            # Fallback: process pages individually with consistency notes
            return self._fallback_document_formatting(document_pages, strategy, reasoning_steps)
    
    def _chunked_document_formatting(self, document_pages: List[str], strategy: str,
                                    reasoning_steps: List[str]) -> Tuple[str, List[str], int]:
        """Process document in chunks with parallel API calls for better performance."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import threading

        # Smaller chunks for better performance and faster feedback
        # 3 pages per chunk = faster per-chunk processing + better parallelism
        chunk_size = 3  # Optimized from 5 to 3 for faster processing
        total_chunks = (len(document_pages) + chunk_size - 1) // chunk_size  # Ceiling division

        reasoning_steps.append(f"Processing document in {total_chunks} chunks of {chunk_size} pages (parallel)")
        self.logger.log_step(f"📊 Processing {len(document_pages)} pages in {total_chunks} chunks IN PARALLEL 🚀")

        # Create chunks
        chunks = []
        for chunk_idx, chunk_start in enumerate(range(0, len(document_pages), chunk_size), 1):
            chunk_end = min(chunk_start + chunk_size, len(document_pages))
            chunk_pages = document_pages[chunk_start:chunk_end]
            chunks.append({
                'idx': chunk_idx,
                'start': chunk_start,
                'end': chunk_end,
                'pages': chunk_pages
            })

        # Process chunks in parallel
        formatted_chunks = [None] * len(chunks)  # Preserve order
        total_tokens = 0
        tokens_lock = threading.Lock()

        def format_chunk(chunk_info):
            """Format a single chunk (runs in parallel)."""
            chunk_idx = chunk_info['idx']
            chunk_start = chunk_info['start']
            chunk_end = chunk_info['end']
            chunk_pages = chunk_info['pages']

            try:
                # Combine chunk pages
                chunk_text = "\n\n---PAGE BREAK---\n\n".join(chunk_pages)
                chunk_char_count = len(chunk_text)

                self.logger.log_step(
                    f"📝 Processing chunk {chunk_idx}/{total_chunks}: "
                    f"Pages {chunk_start+1}-{chunk_end} ({chunk_char_count:,} chars)..."
                )

                chunk_prompt = f"""Format pages {chunk_start+1}-{chunk_end} of {len(document_pages)} with consistent formatting:

{chunk_text}"""

                messages = [
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": chunk_prompt}
                ]

                self.logger.log_step(f"  📡 Calling API for pages {chunk_start+1}-{chunk_end}...")
                formatted_chunk, tokens = self.make_api_call(messages, temperature=0.05)

                # Thread-safe token counting
                with tokens_lock:
                    nonlocal total_tokens
                    total_tokens += tokens

                self.logger.log_success(f"✅ Formatted pages {chunk_start+1}-{chunk_end} ({tokens:,} tokens)")
                return {'index': chunk_idx - 1, 'content': formatted_chunk, 'success': True}

            except Exception as e:
                self.logger.log_error(f"❌ Chunk {chunk_start+1}-{chunk_end} formatting failed: {str(e)}")
                reasoning_steps.append(f"Chunk {chunk_start+1}-{chunk_end} formatting failed: {str(e)}")
                # Fall back to original pages for this chunk
                fallback_content = "\n\n".join(chunk_pages)
                return {'index': chunk_idx - 1, 'content': fallback_content, 'success': False}

        # Execute in parallel with limited workers (to avoid rate limits)
        # Anthropic allows 50 req/min, so 8 concurrent is safe (well under limit)
        max_workers = min(8, total_chunks)  # Max 8 concurrent API calls (increased from 4)
        self.logger.log_step(f"🔧 Using {max_workers} parallel workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunks
            future_to_chunk = {executor.submit(format_chunk, chunk): chunk for chunk in chunks}

            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                result = future.result()
                formatted_chunks[result['index']] = result['content']

        return "\n\n".join(formatted_chunks), reasoning_steps, total_tokens

    def _fallback_document_formatting(self, document_pages: List[str], strategy: str,
                                    reasoning_steps: List[str]) -> Tuple[str, List[str], int]:
        """Fallback document formatting by processing pages individually."""
        reasoning_steps.append("Using fallback page-by-page processing")
        formatted_pages = []
        total_tokens = 0

        for i, page_text in enumerate(document_pages):
            try:
                # Process each page with consistency context
                page_prompt = f"""Format page {i+1}/{len(document_pages)} consistently:

{page_text}"""

                messages = [
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": page_prompt}
                ]

                formatted_page, tokens = self.make_api_call(messages, temperature=0.1)
                formatted_pages.append(formatted_page)
                total_tokens += tokens

            except Exception as e:
                reasoning_steps.append(f"Page {i+1} formatting failed: {str(e)}")
                formatted_pages.append(page_text)  # Keep original if formatting fails

        return "\n\n".join(formatted_pages), reasoning_steps, total_tokens
    
    def _calculate_document_formatting_confidence(self, original_pages: List[str], 
                                                 formatted_content: str, 
                                                 analysis: Dict[str, Any]) -> float:
        """Calculate confidence for document-wide formatting consistency."""
        base_confidence = 0.8
        
        # Consistency indicators
        formatted_lines = formatted_content.split('\n')
        
        # Header consistency
        h2_headers = len([line for line in formatted_lines if line.startswith('## ')])
        h3_headers = len([line for line in formatted_lines if line.startswith('### ')])
        if h2_headers > 0 and h3_headers > 0:
            base_confidence += 0.05
        
        # Table formatting consistency
        if analysis.get("has_tables", False):
            flattened_entries = len(re.findall(r'\*\*[^*]+\*\*\s*-\s*\*\*[^*]+\*\*:', formatted_content))
            if flattened_entries > 0:
                base_confidence += 0.1
            else:
                base_confidence -= 0.2
        
        # Form element consistency
        if analysis.get("has_forms", False):
            selected_pattern = len(re.findall(r'\[SELECTED\]', formatted_content))
            unselected_pattern = len(re.findall(r'\[ \]', formatted_content))
            if selected_pattern > 0 or unselected_pattern > 0:
                base_confidence += 0.05
        
        # Content preservation
        original_length = sum(len(page) for page in original_pages)
        formatted_length = len(formatted_content)
        if original_length > 0:
            length_ratio = formatted_length / original_length
            if 0.7 <= length_ratio <= 1.3:  # Reasonable content preservation
                base_confidence += 0.05
            elif length_ratio < 0.5:  # Too much content lost
                base_confidence -= 0.2
        
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_consistency_score(self, formatted_content: str) -> float:
        """Calculate consistency score for the formatted document."""
        try:
            lines = formatted_content.split('\n')
            
            # Check for consistent header formatting
            headers = [line for line in lines if line.startswith('#')]
            consistent_headers = all(h.startswith('## ') or h.startswith('### ') or h.startswith('#### ') for h in headers)
            
            # Check for consistent table formatting
            table_entries = re.findall(r'\*\*[^*]+\*\*\s*-\s*\*\*[^*]+\*\*:', formatted_content)
            has_consistent_tables = len(table_entries) > 0 if '**' in formatted_content else True
            
            # Check for consistent checkbox formatting
            checkbox_patterns = [r'\[SELECTED\]', r'\[ \]']
            has_checkboxes = any(re.search(pattern, formatted_content) for pattern in checkbox_patterns)
            inconsistent_checkboxes = bool(re.search(r'\[x\]|\[X\]|☑|☐|✓|✔', formatted_content))
            
            consistency_factors = [
                consistent_headers,
                has_consistent_tables,
                not inconsistent_checkboxes if has_checkboxes else True
            ]
            
            return sum(consistency_factors) / len(consistency_factors)
            
        except Exception:
            return 0.5  # Default moderate score if calculation fails
    
    def _clean_markdown_tables(self, content: str) -> str:
        """Clean up problematic markdown tables that the AI may have generated despite instructions."""
        if not content or '|' not in content:
            return content

        lines = content.split('\n')
        cleaned_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this line starts a markdown table
            if '|' in line and self._is_table_row(line):
                # Extract the table
                table_lines, table_end = self._extract_table_from_lines(lines, i)

                if len(table_lines) >= 2:  # Valid table (header + at least one row)
                    # Convert table to flattened format
                    flattened_entries = self._convert_table_to_flattened(table_lines)
                    cleaned_lines.extend(flattened_entries)
                else:
                    # Not a valid table, keep original lines
                    cleaned_lines.extend(table_lines)

                i = table_end
            else:
                cleaned_lines.append(line)
                i += 1

        return '\n'.join(cleaned_lines)

    def _is_table_row(self, line: str) -> bool:
        """Check if a line appears to be a markdown table row."""
        stripped = line.strip()
        # Ignore code fence lines
        if re.match(r'^```', stripped):
            return False

        # Count pipes present
        pipe_count = stripped.count('|')
        if pipe_count < 2:
            return False

        # Consider as table row if:
        # - Starts with '|' (classic pipe table)
        # - OR contains a pipe between non-space tokens (no need for trailing '|')
        if stripped.startswith('|') or re.search(r'\S\s*\|\s*\S', stripped):
            return True

        # Also treat header separator lines like:
        # |----|----|, :---|:---, ----|---- (with or without edge pipes)
        if re.match(r'^\|?\s*:?\-\-+\s*(\|\s*:?\-\-+\s*)+\|?$', stripped):
            return True

        return False

    def _extract_table_from_lines(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Extract a complete markdown table starting from start_idx."""
        table_lines = []
        i = start_idx

        # Collect all consecutive table rows
        while i < len(lines) and self._is_table_row(lines[i]):
            table_lines.append(lines[i])
            i += 1

        return table_lines, i

    def _convert_table_to_flattened(self, table_lines: List[str]) -> List[str]:
        """Convert markdown table to flattened format per prompt instructions."""
        if len(table_lines) < 2:
            return table_lines

        flattened_entries = []

        # Parse header row
        header_line = table_lines[0].strip()
        # Split on '|' and drop empty edge cells if present (to support both styles)
        header_parts = [cell.strip() for cell in header_line.split('|')]
        if header_parts and header_parts[0] == '':
            header_parts = header_parts[1:]
        if header_parts and header_parts[-1] == '':
            header_parts = header_parts[:-1]
        headers = [cell for cell in header_parts if cell]
        # Clean headers by removing bold formatting if present
        headers = [re.sub(r'\*\*(.*?)\*\*', r'\1', h) for h in headers if h]  # Remove empty headers and bold formatting

        # Skip separator row if present (usually second row with dashes)
        data_start_idx = 1
        if len(table_lines) > 1:
            separator_line = table_lines[1].strip()
            # Accept separators with or without edge pipes
            if re.match(r'^\|?\s*[-:]+\s*(\|\s*[-:]+\s*)*\|?$', separator_line):
                data_start_idx = 2

        # Process data rows
        for i in range(data_start_idx, len(table_lines)):
            row_line = table_lines[i].strip()
            row_parts = [cell.strip() for cell in row_line.split('|')]
            if row_parts and row_parts[0] == '':
                row_parts = row_parts[1:]
            if row_parts and row_parts[-1] == '':
                row_parts = row_parts[:-1]
            cells = row_parts

            # Remove empty first cell if present (common issue you mentioned)
            if cells and not cells[0]:
                cells = cells[1:]

            # Match cells to headers
            for j, cell_value in enumerate(cells):
                if j < len(headers) and cell_value:
                    # Clean cell value (remove bold formatting)
                    clean_value = re.sub(r'\*\*(.*?)\*\*', r'\1', cell_value)

                    # Create flattened entry based on column position
                    if j == 0:
                        # First column becomes row identifier, skip creating entry
                        continue
                    elif len(headers) > j:
                        # Format: **Column** - **Row**: Value
                        header = headers[j]
                        if j > 0 and cells[0]:  # Use first cell as row identifier if available
                            row_id = re.sub(r'\*\*(.*?)\*\*', r'\1', cells[0])
                            entry = f"**{header}** - **{row_id}**: {clean_value}"
                        else:
                            entry = f"**{header}**: {clean_value}"

                        flattened_entries.append(entry)

        return flattened_entries if flattened_entries else table_lines

    def _clean_ai_metadata(self, text: str) -> Tuple[str, List[str]]:
        """Remove AI metadata, apologies, and commentary from output.

        Args:
            text: Raw text from AI model

        Returns:
            Tuple of (cleaned_text, list of removed fragments)
        """
        if not text:
            return text, []

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
            (r"\[.*?including wrapped cell content.*?\]", "Cell content note"),
            (r"Here is.*?(?:\.|$)", "Here is"),
            (r"The following.*?(?:\.|$)", "The following"),
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

    class _FootnoteProcessor:
        """Modular footnote processing for converting citations to inline format."""

        def __init__(self, context: Dict[str, Any]):
            """Initialize processor with configuration options."""
            self.style = context.get("footnote_style", "inline")  # "inline", "minimal", "preserve"
            self.max_length = context.get("max_footnote_length", 200)
            self.preserve_references = context.get("preserve_references", False)

            # Citation pattern definitions
            self.citation_patterns = [
                # Superscript numbers: ⁰¹²³⁴⁵⁶⁷⁸⁹
                r'([⁰¹²³⁴⁵⁶⁷⁸⁹]+)',
                # Bracketed numbers: [1], [2], etc.
                r'\[(\d+)\]',
                # Parenthetical numbers: (1), (2), etc.
                r'\((\d+)\)',
                # Plain superscript-like numbers at end of words
                r'(\d+)(?=\s|$|[.,;:])',
            ]

        def convert_footnotes_to_inline(self, content: str) -> str:
            """Convert footnotes to inline parenthetical format."""
            if not content or not content.strip():
                return content

            # Find all citation markers and their corresponding footnotes
            citations_and_footnotes = self._extract_citations_and_footnotes(content)

            if not citations_and_footnotes:
                return content  # No footnotes found

            # Convert based on selected style
            if self.style == "inline":
                return self._convert_to_inline(content, citations_and_footnotes)
            elif self.style == "minimal":
                return self._convert_to_minimal(content, citations_and_footnotes)
            else:  # preserve
                return self._preserve_with_cleanup(content, citations_and_footnotes)

        def _extract_citations_and_footnotes(self, content: str) -> List[Tuple[str, str, str]]:
            """Extract citation markers and their corresponding footnotes."""
            citations_and_footnotes = []
            lines = content.split('\n')

            # First, identify footnote lines to exclude from citation search
            footnote_lines = set()
            for line_num, line in enumerate(lines):
                line_stripped = line.strip()
                # Check if this line starts with a footnote marker
                for pattern in self.citation_patterns:
                    # Modified pattern to only match at start of line
                    start_pattern = f"^\\s*{pattern.replace('([', '([').replace('])', '])')}"
                    if re.match(start_pattern, line_stripped):
                        footnote_lines.add(line_num)
                        break

            # Find citation markers in text (excluding footnote lines)
            citation_markers = []
            for line_num, line in enumerate(lines):
                if line_num in footnote_lines:
                    continue  # Skip footnote lines

                for pattern in self.citation_patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        marker = match.group(1) if match.group(1) else match.group(0)
                        citation_markers.append({
                            'marker': marker,
                            'full_match': match.group(0),
                            'line_num': line_num,
                            'position': match.start()
                        })

            # Find corresponding footnotes and deduplicate
            seen_markers = set()
            for citation in citation_markers:
                marker = citation['marker']
                if marker in seen_markers:
                    continue  # Skip duplicate markers

                footnote_text = self._find_footnote_text(lines, marker)
                if footnote_text:
                    citations_and_footnotes.append((
                        citation['full_match'],
                        marker,
                        footnote_text
                    ))
                    seen_markers.add(marker)

            return citations_and_footnotes

        def _find_footnote_text(self, lines: List[str], marker: str) -> Optional[str]:
            """Find footnote text that corresponds to a citation marker."""
            # Convert superscript to normal numbers for matching
            normal_marker = self._normalize_marker(marker)

            # Look for footnote patterns
            footnote_patterns = [
                rf'^{re.escape(marker)}\s+(.+)$',  # Exact marker match
                rf'^{re.escape(normal_marker)}\s+(.+)$',  # Normalized number match
                rf'^{re.escape(marker)}\.?\s+(.+)$',  # With optional period
                rf'^{re.escape(normal_marker)}\.?\s+(.+)$',  # Normalized with period
            ]

            for line in lines:
                line = line.strip()
                for pattern in footnote_patterns:
                    match = re.match(pattern, line)
                    if match:
                        return match.group(1).strip()

            return None

        def _normalize_marker(self, marker: str) -> str:
            """Convert superscript markers to normal numbers."""
            superscript_map = {
                '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
                '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
            }

            normalized = marker
            for super_char, normal_char in superscript_map.items():
                normalized = normalized.replace(super_char, normal_char)

            return normalized

        def _convert_to_inline(self, content: str, citations_and_footnotes: List[Tuple[str, str, str]]) -> str:
            """Convert to full inline parenthetical format."""
            result = content

            # First, remove all footnote lines to avoid duplication
            for full_match, marker, footnote_text in citations_and_footnotes:
                footnote_patterns = [
                    rf'^{re.escape(marker)}\s+.*$',  # Exact marker
                    rf'^{re.escape(marker)}\.?\s+.*$',  # Marker with optional period
                    rf'^{re.escape(self._normalize_marker(marker))}\s+.*$',  # Normalized marker
                    rf'^{re.escape(self._normalize_marker(marker))}\.?\s+.*$',  # Normalized with period
                ]

                for pattern in footnote_patterns:
                    result = re.sub(pattern, '', result, flags=re.MULTILINE)

            # Then replace citations with inline versions
            # Sort by length of full_match to handle longer patterns first
            citations_and_footnotes.sort(key=lambda x: len(x[0]), reverse=True)

            for full_match, marker, footnote_text in citations_and_footnotes:
                # Truncate if too long for display
                if len(footnote_text) > self.max_length:
                    footnote_text = footnote_text[:self.max_length-3] + "..."

                # Create replacement
                if self.preserve_references:
                    replacement = f"{full_match} ({footnote_text})"
                else:
                    replacement = f" ({footnote_text})"

                # Replace citation with inline version
                result = result.replace(full_match, replacement)

            # Clean up extra whitespace and empty lines
            result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
            result = re.sub(r'\n\s*\n$', '', result)  # Remove trailing empty lines
            return result.strip()

        def _convert_to_minimal(self, content: str, citations_and_footnotes: List[Tuple[str, str, str]]) -> str:
            """Convert to minimal inline format with key information only."""
            result = content

            for full_match, marker, footnote_text in citations_and_footnotes:
                # Extract key information (first sentence or up to first comma)
                key_info = footnote_text.split('.')[0].split(',')[0].strip()

                # Limit length
                if len(key_info) > 100:
                    key_info = key_info[:97] + "..."

                replacement = f" ({key_info})" if not self.preserve_references else f"{full_match} ({key_info})"
                result = result.replace(full_match, replacement)

                # Remove footnote lines
                footnote_line_pattern = rf'^{re.escape(marker)}\.?\s+{re.escape(footnote_text)}'
                result = re.sub(footnote_line_pattern, '', result, flags=re.MULTILINE)

            return result.strip()

        def _preserve_with_cleanup(self, content: str, citations_and_footnotes: List[Tuple[str, str, str]]) -> str:
            """Preserve original format but clean up positioning."""
            # For now, just return original content
            # This mode could be enhanced to improve footnote positioning without conversion
            _ = citations_and_footnotes  # Suppress unused parameter warning
            return content


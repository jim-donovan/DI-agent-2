"""
Optimized Document Processor with Parallel Processing
"""

import time
import traceback
import io
import re
from datetime import datetime
import tempfile
import os
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
import threading
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from logger import ProcessingLogger
from agent_ocr_engine import AgentBasedOCREngine
from utils import validate_page_ranges, extract_document_title


@dataclass
class ProcessingResult:
    """Result from document processing."""
    content: str
    output_file: Optional[str]
    status: str
    logs: str
    success: bool = True
    vision_calls_used: int = 0
    processing_time: float = 0.0
    pages_processed: int = 0
    evaluation_report: Optional[str] = None  # Separate evaluation for UI display


class OptimizedDocumentProcessor:
    """Optimized document processor with parallel page processing."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize with configurable worker threads.
        
        Args:
            max_workers: Max parallel workers. None = CPU count.
        """
        self.logger = ProcessingLogger()
        self.abort_event = threading.Event()
        self.ocr_engine = AgentBasedOCREngine(self.logger)
        # Give OCR engine access to abort checking
        self.ocr_engine.is_abort_requested = self.is_abort_requested
        self.use_systematic_processing = True  # Enable new systematic pipeline
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())
        # Store debug info for final output
        self.debug_info = {"parallel_workers": self.max_workers}
        self.total_vision_calls = 0
    
    def abort_processing(self) -> None:
        """Request processing abort."""
        self.abort_event.set()
        self.logger.log_step("🛑 Abort requested by user")
    
    def clear_abort(self) -> None:
        """Clear abort flag."""
        self.abort_event.clear()
    
    def is_abort_requested(self) -> bool:
        """Check if abort was requested."""
        return self.abort_event.is_set()
    
    def _process_single_page(self, args: tuple) -> tuple:
        """Process a single page (for parallel execution).
        
        Args:
            args: Tuple of (doc_path, page_no, dpi)
            
        Returns:
            Tuple of (page_no, text, success)
        """
        doc_path, page_no, dpi = args
        
        try:
            # Each worker opens its own document instance (thread-safe)
            with fitz.open(doc_path) as doc:
                page = doc[page_no - 1]  # fitz is 0-indexed
                
                # Convert page to image for OCR
                pix = page.get_pixmap(dpi=dpi)
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                # Use shared OCR engine to avoid duplicate agent registrations
                # The shared engine is thread-safe for extraction calls
                text = self.ocr_engine.extract_page_text_with_agents(page, img, page_no, filename=str(doc_path))
                stats = self.ocr_engine.get_agent_stats()
                vision_calls = stats.get("vision_calls_used", 0)
                return (page_no, text, True, vision_calls)
                
        except Exception as e:
            self.logger.log_error(f"Page {page_no} failed: {e}")
            return (page_no, "", False, 0)
    
    def process_document(self, uploaded_file, page_ranges_str: Optional[str] = None, 
                        progress_callback: Optional[Callable] = None) -> ProcessingResult:
        """Process document with parallel page processing."""
        
        start_time = time.time()
        self.clear_abort()
        self.logger.clear()
        self.total_vision_calls = 0
        
        try:
            # Check for null file first
            if not uploaded_file:
                return ProcessingResult(
                    content="Please upload a PDF, Markdown, or TXT file.",
                    output_file=None,
                    status="No file",
                    logs=self.logger.get_logs(),
                    success=False,
                    evaluation_report=None
                )
            file_path = Path(uploaded_file.name)
            file_size = os.path.getsize(file_path)
            file_type = file_path.suffix.lower()
            
            # Analytics removed - can be added back later if needed
            
            # Handle markdown and text files
            if file_type in ['.md', '.markdown', '.txt']:
                # For non-PDF files, use simple processing
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Format content if needed
                if file_type == '.txt':
                    final_content = f"# {self._extract_document_title(file_path.name)}\n\n{content}"
                else:
                    final_content = content
                
                output_file = self.save_output(file_path, final_content)
                processing_time = time.time() - start_time
                
                return ProcessingResult(
                    content=final_content,
                    output_file=output_file,
                    status=f"✅ Processed in {processing_time:.1f}s",
                    logs=self.logger.get_logs(),
                    success=True,
                    vision_calls_used=0,
                    processing_time=processing_time,
                    pages_processed=1,
                    evaluation_report=None
                )
            
            # PDF processing with systematic agent pipeline
            with fitz.open(file_path) as doc:
                total_pages = len(doc)
                
                # Update file upload tracking with page count
                # Analytics removed - can be added back later if needed
                
                # Check if systematic processing is enabled
                if self.use_systematic_processing and hasattr(self.ocr_engine, 'process_document_systematically'):
                    self.logger.log_step("🚀 Using systematic processing pipeline")
                    
                    # Use systematic processing
                    result = self.ocr_engine.process_document_systematically(
                        pdf_document=doc,
                        page_ranges=page_ranges_str or "all",
                        document_name=file_path.stem
                    )
                    
                    if result["success"]:
                        # Generate output file with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_file = Path(tempfile.gettempdir()) / f"{file_path.stem}_processed_{timestamp}.md"
                        
                        # Generate evaluation report separately
                        evaluation_report = None
                        if result.get("evaluation"):
                            # Extract evaluation report from the structured result
                            evaluation = result["evaluation"]
                            evaluation_report = evaluation.get("evaluation_report", "")
                            
                            # If no report found, create fallback
                            if not evaluation_report:
                                evaluation_report = "# Processing Quality Report\n\n"
                                evaluation_report += f"**Overall Score:** {evaluation.get('overall_score', 0):.1f}/100\n"
                                evaluation_report += f"**Recommendation:** {evaluation.get('recommendation', 'UNKNOWN')}\n\n"
                                evaluation_report += f"**Summary:** {evaluation.get('summary', 'No summary available')}\n"
                        
                        # Build complete content for file (includes both markdown and evaluation)
                        complete_content = result["markdown_content"]
                        if evaluation_report:
                            complete_content += "\n\n---\n\n" + evaluation_report
                        
                        # Write complete content to file
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(complete_content)
                        
                        processing_time = time.time() - start_time
                        
                        # Track successful processing
                        # Analytics removed - can be added back later if needed
                        
                        return ProcessingResult(
                            content=result["markdown_content"],  # Return just the markdown content
                            output_file=str(output_file),
                            status="Systematic processing completed",
                            logs=self.logger.get_logs(),
                            success=True,
                            vision_calls_used=result["metadata"]["vision_calls_used"],
                            processing_time=processing_time,
                            pages_processed=result["metadata"]["pages_processed"],
                            evaluation_report=evaluation_report  # Separate evaluation report
                        )
                    else:
                        # Systematic processing failed, fall back to traditional method
                        self.logger.log_warning("Systematic processing failed, falling back to traditional method")
                        self.use_systematic_processing = False  # Disable for this run
                
                # Check for abort before falling back to traditional processing
                if self.is_abort_requested():
                    processing_time = time.time() - start_time
                    return ProcessingResult(
                        content="Processing aborted",
                        output_file=None,
                        status="Aborted",
                        logs=self.logger.get_logs(),
                        success=False,
                        processing_time=processing_time,
                        pages_processed=0,
                        evaluation_report=None
                    )
                
                # Traditional processing (fallback)
                self.logger.log_step("📄 Using traditional parallel processing")
                
                # Determine pages to process
                if page_ranges_str and page_ranges_str.strip():
                    is_valid, error_msg, page_numbers = validate_page_ranges(page_ranges_str, total_pages)
                    if not is_valid:
                        # Analytics removed - can be added back later if needed
                        return ProcessingResult(
                            content=f"Invalid page ranges: {error_msg}",
                            output_file=None,
                            status="Invalid page ranges",
                            logs=self.logger.get_logs(),
                            success=False,
                            evaluation_report=None
                        )
                else:
                    page_numbers = list(range(1, total_pages + 1))
            
            # Track processing start
            # Analytics removed - can be added back later if needed
            
            # Prepare arguments for parallel processing
            dpi = 300
            # Convert 0-based page_numbers to 1-based for processing (only for parsed ranges)
            if page_ranges_str and page_ranges_str.strip():
                # Page numbers from parser are 0-based, convert to 1-based
                process_args = [(str(file_path), page_no + 1, dpi) for page_no in page_numbers]
            else:
                # Page numbers for "all pages" are already 1-based
                process_args = [(str(file_path), page_no, dpi) for page_no in page_numbers]
            
            # Check for abort before starting parallel processing
            if self.is_abort_requested():
                processing_time = time.time() - start_time
                return ProcessingResult(
                    content="Processing aborted",
                    output_file=None,
                    status="Aborted",
                    logs=self.logger.get_logs(),
                    success=False,
                    processing_time=processing_time,
                    pages_processed=0,
                    evaluation_report=None
                )
            
            # Process pages in parallel
            page_texts = {}
            completed = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all page processing tasks
                future_to_page = {
                    executor.submit(self._process_single_page, args): args[1] 
                    for args in process_args
                }
                
                # Process completed pages as they finish
                for future in as_completed(future_to_page):
                    if self.is_abort_requested():
                        executor.shutdown(wait=False)
                        return ProcessingResult(
                            content="Processing aborted",
                            output_file=None,
                            status="Aborted",
                            logs=self.logger.get_logs(),
                            success=False,
                            evaluation_report=None
                        )
                    
                    page_no = future_to_page[future]
                    try:
                        result_page_no, text, success, vision_calls = future.result()
                        if success:
                            page_texts[result_page_no] = text
                            self.total_vision_calls += vision_calls
                            completed += 1
                            
                            if progress_callback:
                                progress_callback(f"📖 Processed page {result_page_no} ({completed}/{len(page_numbers)})")
                        else:
                            self.logger.log_error(f"❌ Page {result_page_no} processing failed silently (success=False)")
                                
                    except Exception as e:
                        self.logger.log_error(f"❌ Page {page_no} processing failed with exception: {e}")
            
            # Format all pages at once (batch processing)
            if progress_callback:
                progress_callback("📝 Formatting all pages...")
            
            formatted_pages = []
            for page_no in sorted(page_texts.keys()):
                formatted_pages.append(page_texts[page_no])
            
            # Add document header and join all pages
            document_title = self._extract_document_title(file_path.name)
            header = f"# {document_title}\n\n**Processed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            if page_ranges_str and page_ranges_str.strip():
                header += f"\n\n**Pages Processed:** {page_ranges_str}"
            final_content = f"{header}\n\n---\n\n" + "\n\n---\n\n".join(formatted_pages)
            
            # Save output
            output_file = self.save_output(file_path, final_content)
            
            processing_time = time.time() - start_time
            self.logger.log_success(f"✅ Completed in {processing_time:.1f}s")
            
            # Track successful completion
            # Analytics removed(success=True)
            
            return ProcessingResult(
                content=final_content,
                output_file=output_file,
                status=f"✅ Processed {len(page_texts)} pages in {processing_time:.1f}s",
                logs=self.logger.get_logs(),
                success=True,
                vision_calls_used=self.total_vision_calls,
                processing_time=processing_time,
                pages_processed=len(page_texts),
                evaluation_report=None  # Traditional processing doesn't generate evaluation
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Processing failed: {str(e)}"
            
            # Track error
            # Analytics removed - can be added back later if needed
            
            self.logger.log_error(error_msg)
            return ProcessingResult(
                content=error_msg,
                output_file=None,
                status="Failed",
                logs=self.logger.get_logs(),
                success=False,
                vision_calls_used=self.total_vision_calls,
                processing_time=processing_time,
                pages_processed=0,
                evaluation_report=None
            )
    
    def save_output(self, pdf_path: Path, content: str) -> Optional[str]:
        """Save processed content to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{pdf_path.stem}_{timestamp}.md"
            
            # Save to temp directory for cross-platform compatibility
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            output_path = temp_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.log_success(f"📁 Output saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.log_error(f"Failed to save output: {e}")
            return None
    
    
    def clear_logs(self) -> None:
        """Clear all logs."""
        self.logger.clear()
    
    def add_log_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback for real-time log updates."""
        self.logger.add_callback(callback)
    
    def _extract_document_title(self, filename: str) -> str:
        """Extract a clean document title from filename."""
        # Use the centralized utility, but add timestamp removal first
        title = Path(filename).stem
        # Remove timestamp patterns (YYYYMMDD_HHMMSS) from the end
        title = re.sub(r'_\d{8}_\d{6}$', '', title)  # Remove _20250831_123456
        title = re.sub(r'_\d{14}$', '', title)       # Remove _20250831123456
        # Now use the utility for final formatting
        return extract_document_title(title)
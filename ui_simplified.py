"""
Simplified Gradio User Interface
Cleaned up UI with simplified evaluation handling and loading messages
"""

import gradio as gr
import random
from pathlib import Path
from datetime import datetime
import tempfile
from processor_optimized import OptimizedDocumentProcessor as DocumentProcessor
from config import config
from summary_generator import SummaryGenerator
from utils import extract_document_title, get_recommendation_color


class SimplifiedOCRInterface:
    """Simplified Gradio interface for OCR processing."""
    
    # Simplified loading messages - keep the fun but reduce complexity
    LOADING_MESSAGES = [
        "Reticulating splines...",
        "Generating witty dialog...",
        "Spinning violently around the y-axis...",
        "Tokenizing real life...",
        "Bending the spoon...",
        "We need a new fuse...",
        "640K ought to be enough for anybody",
        "The bits are breeding...",
        "Please wait while the little elves draw your map...",
        "Checking the gravitational constant in your locale...",
        "Follow the white rabbit...",
        "The bits are flowing slowly today...",
        "Testing on Timmy... We're going to need another Timmy.",
        "Are we there yet?",
        "Don't panic...",
        "Computing chance of success...",
        "Looking for exact change...",
        "Adjusting flux capacitor...",
        "We need more dilithium crystals...",
        "Spinning the hamster wheel...",
        "Your left thumb prints are being processed...",
        "Downloading more RAM...",
        "Kindly hold on as our intern quits vim...",
        "Installing dependencies...",
        "Let's hope it's worth the wait...",
        "Constructing additional pylons..."
    ]
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.summary_generator = SummaryGenerator(self.processor.logger)
        self.current_summary = ""
        self.current_document_title = ""
        self.current_evaluation = ""
        self.raw_ocr_output = ""
    
    def _get_loading_html(self):
        """Get simplified loading animation HTML."""
        # Select 5 random messages for this load
        messages = random.sample(self.LOADING_MESSAGES, min(5, len(self.LOADING_MESSAGES)))
        
        return f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px;">
            <style>
                @keyframes spin {{
                    from {{ transform: rotate(0deg); }}
                    to {{ transform: rotate(360deg); }}
                }}
                @keyframes pulse {{
                    0%, 100% {{ opacity: 0.8; transform: scale(1); }}
                    50% {{ opacity: 1; transform: scale(1.1); }}
                }}
                .loading-spinner {{
                    width: 80px;
                    height: 80px;
                    border: 8px solid rgba(6, 182, 212, 0.2);
                    border-top: 8px solid #06b6d4;
                    border-radius: 50%;
                    animation: spin 2s linear infinite;
                }}
                .loading-text {{
                    margin-top: 20px;
                    color: #06b6d4;
                    font-size: 1.2em;
                    font-weight: 500;
                    animation: pulse 2s ease-in-out infinite;
                }}
                .loading-message {{
                    margin-top: 10px;
                    color: #94a3b8;
                    font-style: italic;
                }}
            </style>
            <div class="loading-spinner"></div>
            <div class="loading-text">Processing your document...</div>
            <div class="loading-message" id="loading-msg">{random.choice(messages)}</div>
        </div>
        """
    
    def _parse_evaluation_simple(self, evaluation_content: str):
        """Simplified evaluation parsing - just extract key metrics."""
        if not evaluation_content or evaluation_content.strip() == "*No evaluation report available*":
            return {
                "summary": "No evaluation available",
                "score": "N/A",
                "recommendation": "N/A",
                "details": evaluation_content
            }
        
        # Extract score and recommendation from the content
        score = "N/A"
        recommendation = "UNKNOWN"
        
        lines = evaluation_content.split('\n')
        for line in lines:
            if "Overall Score:" in line or "Score:" in line:
                try:
                    # Extract number from line
                    import re
                    numbers = re.findall(r'\d+\.?\d*', line)
                    if numbers:
                        score = f"{float(numbers[0]):.1f}/100"
                except:
                    pass
            
            if "Recommendation:" in line:
                if "ACCEPT" in line.upper():
                    recommendation = "ACCEPT"
                elif "REVIEW" in line.upper():
                    recommendation = "REVIEW"
                elif "REJECT" in line.upper():
                    recommendation = "REJECT"
        
        # Create simple summary HTML
        color = get_recommendation_color(recommendation)
        summary_html = f"""
        <div class='status-box' style='text-align: center; padding: 20px;'>
            <h3>📊 Quality Evaluation</h3>
            <div style='font-size: 2em; font-weight: bold; margin: 10px 0;'>{score}</div>
            <div style='color: {color}; font-size: 1.2em;'>{recommendation}</div>
        </div>
        """
        
        return {
            "summary": summary_html,
            "score": score,
            "recommendation": recommendation,
            "details": evaluation_content
        }
    
    def process_wrapper(self, uploaded_file, page_ranges_str):
        """Simplified processing wrapper."""
        # Clear abort flag
        self.processor.clear_abort()
        
        if not uploaded_file:
            yield self._create_response(
                content="*Please upload a PDF file to begin processing.*",
                status="<div class='status-box status-error'>❌ No file uploaded</div>"
            )
            return
        
        # Show processing state
        yield self._create_response(
            content="*🚀 Processing started...*",
            status="<div class='status-box status-processing'>⏳ Processing document...</div>",
            loading_html=self._get_loading_html()
        )
        
        try:
            # Process document
            result = self.processor.process_document(
                uploaded_file,
                page_ranges_str if page_ranges_str and page_ranges_str.strip() else None
            )
            
            if result.status == "Aborted":
                yield self._create_response(
                    content="**⚠️ Processing was aborted by user.**",
                    status="<div class='status-box status-error'>⚠️ Processing aborted</div>"
                )
                return
            
            # Generate summary
            self.current_document_title = extract_document_title(uploaded_file.name)
            summary_content, summary_success = self.summary_generator.generate_summary(
                result.content, 
                self.current_document_title
            )
            self.current_summary = summary_content
            
            # Parse evaluation
            evaluation = self._parse_evaluation_simple(
                result.evaluation_report if hasattr(result, 'evaluation_report') else ""
            )
            self.current_evaluation = evaluation["details"]
            
            # Get raw OCR output
            raw_ocr = self._get_raw_ocr_output()
            
            # Create metrics
            metrics_html = f"""
            <div class='status-box'>
                <h4>📊 Processing Metrics</h4>
                <p><strong>Time:</strong> {result.processing_time:.1f}s</p>
                <p><strong>Pages:</strong> {result.pages_processed}</p>
                <p><strong>Vision Calls:</strong> {result.vision_calls_used}</p>
                <p><strong>Words:</strong> {len(result.content.split()) if result.content else 0}</p>
            </div>
            """
            
            # Create final response
            yield self._create_response(
                content=result.content,
                summary=summary_content,
                evaluation_summary=evaluation["summary"],
                evaluation_details=evaluation["details"],
                status="<div class='status-box status-success'>✅ Processing completed!</div>" if result.success else 
                       f"<div class='status-box status-error'>❌ Processing failed: {result.status}</div>",
                metrics=metrics_html,
                file_output=result.output_file,
                raw_ocr=raw_ocr
            )
            
        except Exception as e:
            yield self._create_response(
                content=f"*❌ Processing Error: {e}*",
                status=f"<div class='status-box status-error'>❌ Error: {e}</div>"
            )
    
    def _create_response(self, content="", summary="", evaluation_summary="", 
                        evaluation_details="", status="", metrics="", 
                        file_output=None, raw_ocr="", loading_html=""):
        """Create a response tuple for the interface."""
        return (
            content or "*Processed content will appear here...*",
            summary or "*Summary will appear here...*",
            evaluation_summary or "<div class='status-box'>Evaluation will appear here...</div>",
            evaluation_details or "*Detailed evaluation will appear here...*",
            status or "<div class='status-box'>Ready to process...</div>",
            metrics or "<div class='status-box'>Metrics will appear here...</div>",
            gr.update(value=file_output),
            raw_ocr or "Raw OCR output will appear here...",
            gr.update(value=loading_html, visible=bool(loading_html)),
            gr.update(visible=not bool(loading_html)),  # Clear button
            gr.update(visible=bool(loading_html))  # Abort button
        )
    
    def _get_raw_ocr_output(self):
        """Get raw OCR content from OCR engine."""
        if hasattr(self.processor, 'ocr_engine') and self.processor.ocr_engine:
            return self.processor.ocr_engine.get_debug_raw_ocr_content()
        return "No raw OCR content available."
    
    def clear_all(self):
        """Clear all interface elements."""
        self.processor.clear_abort()
        self.processor.clear_logs()
        if hasattr(self.processor, 'ocr_engine') and self.processor.ocr_engine:
            self.processor.ocr_engine.clear_debug_data()
        self.current_summary = ""
        self.current_document_title = ""
        self.current_evaluation = ""
        
        return self._create_response()
    
    def abort_processing(self):
        """Abort current processing."""
        self.processor.abort_processing()
        return (
            gr.update(),  # Keep current content
            gr.update(),  # Keep current summary
            gr.update(),  # Keep current evaluation summary
            gr.update(),  # Keep current evaluation details
            "<div class='status-box status-error'>🛑 Abort requested...</div>",
            gr.update(),  # Keep current metrics
            gr.update(),  # Keep current file
            gr.update(),  # Keep current raw OCR
            gr.update(visible=False),  # Hide loading
            gr.update(visible=True),   # Show clear
            gr.update(visible=False)   # Hide abort
        )
    
    def download_summary(self):
        """Download summary as markdown."""
        if not self.current_summary:
            return gr.update(value=None, visible=False)
        
        try:
            md_path = self.summary_generator.save_summary_markdown(
                self.current_summary,
                self.current_document_title or "document"
            )
            return gr.update(value=md_path, visible=True) if md_path else gr.update(value=None, visible=False)
        except:
            return gr.update(value=None, visible=False)
    
    def download_evaluation(self):
        """Download evaluation report."""
        if not self.current_evaluation:
            return gr.update(value=None, visible=False)
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.current_document_title or 'document'}_evaluation_{timestamp}.md"
            path = Path(tempfile.gettempdir()) / filename
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.current_evaluation)
            
            return gr.update(value=str(path), visible=True)
        except:
            return gr.update(value=None, visible=False)
    
    def get_css(self):
        """Get simplified CSS for the interface."""
        return """
        /* Simplified CSS - Clean and Modern */
        .gradio-container {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
            min-height: 100vh !important;
        }
        
        .main-header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 16px;
            color: #f0f9ff;
            text-align: center;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .main-header h1 {
            margin: 0 0 0.5rem 0;
            font-size: 2.5rem;
            background: linear-gradient(135deg, #06b6d4, #22d3ee);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .left-panel {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        .status-box {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            color: #f0f9ff;
        }
        
        .status-success {
            background: rgba(16, 185, 129, 0.1);
            border-color: rgba(16, 185, 129, 0.3);
            color: #6ee7b7;
        }
        
        .status-error {
            background: rgba(239, 68, 68, 0.1);
            border-color: rgba(239, 68, 68, 0.3);
            color: #fca5a5;
        }
        
        .status-processing {
            background: rgba(6, 182, 212, 0.1);
            border-color: rgba(6, 182, 212, 0.3);
            color: #67e8f9;
        }
        
        /* Buttons */
        .primary-btn {
            background: linear-gradient(135deg, #06b6d4, #22d3ee) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: transform 0.2s !important;
        }
        
        .primary-btn:hover {
            transform: translateY(-2px) !important;
        }
        
        .secondary-btn {
            background: rgba(255, 255, 255, 0.1) !important;
            color: #67e8f9 !important;
            border: 1px solid rgba(6, 182, 212, 0.3) !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            cursor: pointer !important;
            transition: all 0.2s !important;
        }
        
        .secondary-btn:hover {
            background: rgba(255, 255, 255, 0.15) !important;
        }
        
        /* Input fields */
        input, textarea, select {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #f0f9ff !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
        }
        
        input:focus, textarea:focus, select:focus {
            background: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(6, 182, 212, 0.4) !important;
            outline: none !important;
        }
        
        /* Tabs */
        .tabs {
            background: rgba(255, 255, 255, 0.02) !important;
            border-radius: 12px !important;
            padding: 4px !important;
        }
        
        /* Markdown areas */
        .markdown {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            color: #f0f9ff !important;
        }
        """
    
    def create_interface(self):
        """Create simplified Gradio interface."""
        with gr.Blocks(title="OCR Processor", css=self.get_css()) as demo:
            
            # Header
            gr.HTML("""
                <div class="main-header">
                    <h1>Document Ingestion</h1>
                    <p>Simplified & Optimized OCR Processing</p>
                </div>
            """)
            
            with gr.Row():
                # Left Panel - Controls
                with gr.Column(scale=1, elem_classes="left-panel"):
                    pdf_input = gr.File(
                        label="Upload Document", 
                        file_types=[".pdf", ".md", ".txt"]
                    )
                    
                    page_ranges_input = gr.Textbox(
                        label="Page Ranges (Optional)",
                        placeholder="e.g., 1-5, 10, 15-20",
                        info="Leave blank for all pages"
                    )
                    
                    with gr.Row():
                        process_btn = gr.Button("🚀 Process", variant="primary", elem_classes="primary-btn")
                        clear_btn = gr.Button("🗑️ Clear", variant="secondary", visible=False, elem_classes="secondary-btn")
                        abort_btn = gr.Button("🛑 Abort", variant="secondary", visible=False, elem_classes="secondary-btn")
                    
                    status_output = gr.HTML(value="<div class='status-box'>⏳ Ready to process...</div>")
                    metrics_output = gr.HTML(value="<div class='status-box'>Metrics will appear here...</div>")
                
                # Right Panel - Results
                with gr.Column(scale=2):
                    loading_animation = gr.HTML(value="", visible=False)
                    
                    with gr.Tabs():
                        with gr.Tab("📄 Document"):
                            content_output = gr.Markdown(
                                value="*Processed content will appear here...*",
                                show_copy_button=True
                            )
                        
                        with gr.Tab("📋 Summary"):
                            summary_output = gr.Markdown(
                                value="*Summary will appear here...*",
                                show_copy_button=True
                            )
                            download_summary_btn = gr.Button("💾 Download", size="sm")
                            summary_file = gr.File(visible=False)
                        
                        with gr.Tab("🔍 Quality Report"):
                            evaluation_summary = gr.HTML(
                                value="<div class='status-box'>Evaluation will appear here...</div>"
                            )
                            evaluation_details = gr.Markdown(
                                value="*Detailed evaluation will appear here...*",
                                show_copy_button=True
                            )
                            download_eval_btn = gr.Button("💾 Download", size="sm")
                            eval_file = gr.File(visible=False)
                        
                        with gr.Tab("🔬 Raw OCR"):
                            raw_ocr_output = gr.Textbox(
                                label="Raw Vision OCR Output",
                                lines=20,
                                value="Raw OCR will appear here...",
                                interactive=False
                            )
                        
                        with gr.Tab("💾 Download"):
                            file_output = gr.File(label="Processed File", interactive=False)
            
            # Event handlers
            process_btn.click(
                fn=self.process_wrapper,
                inputs=[pdf_input, page_ranges_input],
                outputs=[
                    content_output, summary_output, evaluation_summary,
                    evaluation_details, status_output, metrics_output,
                    file_output, raw_ocr_output, loading_animation,
                    clear_btn, abort_btn
                ]
            )
            
            clear_btn.click(
                fn=self.clear_all,
                outputs=[
                    content_output, summary_output, evaluation_summary,
                    evaluation_details, status_output, metrics_output,
                    file_output, raw_ocr_output, loading_animation,
                    clear_btn, abort_btn
                ]
            )
            
            abort_btn.click(
                fn=self.abort_processing,
                outputs=[
                    content_output, summary_output, evaluation_summary,
                    evaluation_details, status_output, metrics_output,
                    file_output, raw_ocr_output, loading_animation,
                    clear_btn, abort_btn
                ]
            )
            
            download_summary_btn.click(
                fn=self.download_summary,
                outputs=[summary_file]
            )
            
            download_eval_btn.click(
                fn=self.download_evaluation,
                outputs=[eval_file]
            )
        
        return demo

def create_ui():
    """Factory function to create the simplified UI."""
    interface = SimplifiedOCRInterface()
    return interface.create_interface()

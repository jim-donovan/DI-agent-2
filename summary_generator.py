"""
Summary Generator
Handles creation of benefits/eligibility summaries with export functionality
"""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from logger import ProcessingLogger
from summary_agent import SummaryAgent
from config import config
from api_client import APIClient

class SummaryGenerator:
    """Generates and manages document summaries with export capabilities."""
    
    def __init__(self, logger: ProcessingLogger):
        self.logger = logger
        self.api_key = config.openai_api_key
        self.summary_enabled = bool(self.api_key)
        
        if self.summary_enabled:
            api_client = APIClient(config)
            self.summary_agent = SummaryAgent(logger, api_client)
            # Debug info - store for final output only
            self.init_status = "Summary generator initialized (AI-powered)"
        else:
            self.init_status = "Summary generator initialized (no AI - basic extraction only)"
    
    def generate_summary(self, content: str, document_title: str = "Document") -> Tuple[str, bool]:
        """
        Generate a focused summary of benefits and eligibility information.
        
        Args:
            content: Full document content
            document_title: Title of the document
            
        Returns:
            Tuple of (summary_content, success)
        """
        
        if not content or not content.strip():
            return "No content available for summarization.", False
        
        try:
            if self.summary_enabled:
                # Use AI-powered summary agent
                self.logger.log_step("🤖 Generating AI-powered benefits summary...")
                
                input_data = {
                    "content": content,
                    "title": document_title
                }
                
                context = {
                    "summary_type": "benefits_eligibility",
                    "max_length": 1000
                }
                
                response = self.summary_agent.process(input_data, context)
                
                if response.success and response.content:
                    self.logger.log_success(f"✅ AI summary generated (confidence: {response.confidence:.2f})")
                    return response.content, True
                else:
                    self.logger.log_error(f"❌ AI summary failed: {response.error_message}")
                    # Fall back to basic extraction
                    return self._generate_basic_summary(content, document_title)
            else:
                # Use basic keyword-based extraction
                return self._generate_basic_summary(content, document_title)
                
        except Exception as e:
            self.logger.log_error(f"Summary generation failed: {str(e)}")
            return f"Summary generation error: {str(e)}", False
    
    def _generate_basic_summary(self, content: str, document_title: str) -> Tuple[str, bool]:
        """Generate a basic summary using keyword extraction (fallback method)."""
        
        self.logger.log_step("📝 Generating basic keyword-based summary...")
        
        # Key sections to look for
        benefit_keywords = [
            'benefit', 'benefits', 'coverage', 'eligible', 'eligibility', 
            'payment', 'payments', 'amount', 'premium', 'deductible',
            'qualify', 'qualification', 'requirement', 'requirements'
        ]
        
        # Split content into lines and paragraphs
        lines = content.split('\n')
        relevant_lines = []
        
        # Find lines containing benefit-related keywords
        for line in lines:
            line_clean = line.strip()
            if line_clean and any(keyword.lower() in line_clean.lower() for keyword in benefit_keywords):
                # Skip very short lines (likely noise)
                if len(line_clean) > 20:
                    relevant_lines.append(line_clean)
        
        if not relevant_lines:
            return f"""# {document_title} - Summary

## Benefits and Eligibility Information

No specific benefits or eligibility criteria were automatically identified in this document. 

*Note: This is a basic keyword-based summary. For more detailed analysis, an AI-powered summary would be more comprehensive.*

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}""", True
        
        # Create a basic structured summary
        summary = f"""# {document_title} - Summary

## Benefits and Eligibility Information

The following key information was extracted from the document:

"""
        
        # Group similar lines
        for i, line in enumerate(relevant_lines[:10]):  # Limit to top 10 relevant lines
            summary += f"- {line}\n"
        
        if len(relevant_lines) > 10:
            summary += f"\n*Note: {len(relevant_lines) - 10} additional relevant items found in full document.*\n"
        
        summary += f"""
---

**Summary Method:** Basic keyword extraction  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Source:** {document_title}

*For more detailed analysis, consider using AI-powered summarization.*"""
        
        self.logger.log_success(f"✅ Basic summary generated ({len(relevant_lines)} relevant items found)")
        return summary, True
    
    def save_summary_markdown(self, summary_content: str, original_filename: str) -> Optional[str]:
        """Save summary as Markdown file."""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(original_filename).stem if original_filename else "document"
            summary_filename = f"{base_name}_summary_{timestamp}.md"
            
            # Use system temp directory
            summary_path = Path(tempfile.gettempdir()) / summary_filename
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            self.logger.log_success(f"📁 Summary saved: {summary_path}")
            return str(summary_path)
            
        except Exception as e:
            self.logger.log_error(f"Failed to save summary: {str(e)}")
            return None
    
    def save_summary_pdf(self, summary_content: str, original_filename: str) -> Optional[str]:
        """Save summary as PDF file."""
        
        try:
            # First save as markdown
            md_path = self.save_summary_markdown(summary_content, original_filename)
            if not md_path:
                return None
            
            # Try weasyprint first, then reportlab as fallback
            pdf_path = self._try_weasyprint_pdf(summary_content, original_filename)
            if pdf_path:
                return pdf_path
                
            # Fallback to reportlab
            pdf_path = self._try_reportlab_pdf(summary_content, original_filename)
            if pdf_path:
                return pdf_path
                
            # Fallback to simple text PDF
            return self._create_simple_text_pdf(summary_content, original_filename)
                
        except Exception as e:
            self.logger.log_error(f"Failed to save PDF summary: {str(e)}")
            return None
    
    def _try_weasyprint_pdf(self, summary_content: str, original_filename: str) -> Optional[str]:
        """Try to create PDF using weasyprint and markdown."""
        try:
            import markdown
            import weasyprint

            # Convert markdown to HTML with table support
            html_content = markdown.markdown(
                summary_content,
                extensions=['tables', 'fenced_code', 'nl2br']
            )

            # Add basic styling with table support
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Benefits and Eligibility Summary</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        line-height: 1.6;
                        color: #333;
                    }}
                    h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    h3 {{ color: #7f8c8d; }}
                    ul, ol {{ margin-left: 20px; }}
                    li {{ margin-bottom: 5px; }}
                    hr {{ margin: 30px 0; border: 1px solid #ecf0f1; }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 20px 0;
                        border: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #3498db;
                        color: white;
                        padding: 12px;
                        text-align: left;
                        border: 1px solid #2980b9;
                        font-weight: bold;
                    }}
                    td {{
                        padding: 10px;
                        border: 1px solid #ddd;
                        text-align: left;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    tr:hover {{
                        background-color: #f1f1f1;
                    }}
                </style>
            </head>
            <body>
            {html_content}
            </body>
            </html>
            """
            
            # Generate PDF filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(original_filename).stem if original_filename else "document"
            pdf_filename = f"{base_name}_summary_{timestamp}.pdf"
            pdf_path = Path(tempfile.gettempdir()) / pdf_filename
            
            # Create PDF
            weasyprint.HTML(string=styled_html).write_pdf(str(pdf_path))
            
            self.logger.log_success(f"📄 PDF summary saved (weasyprint): {pdf_path}")
            return str(pdf_path)
            
        except ImportError:
            self.logger.log_warning("⚠️ weasyprint/markdown not available, trying fallback...")
            return None
        except Exception as e:
            self.logger.log_warning(f"Weasyprint PDF failed: {str(e)}, trying fallback...")
            return None
    
    def _try_reportlab_pdf(self, summary_content: str, original_filename: str) -> Optional[str]:
        """Try to create PDF using reportlab (fallback)."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            
            # Generate PDF filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(original_filename).stem if original_filename else "document"
            pdf_filename = f"{base_name}_summary_{timestamp}.pdf"
            pdf_path = Path(tempfile.gettempdir()) / pdf_filename
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Parse markdown-like content to basic formatting
            lines = summary_content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 6))
                elif line.startswith('# '):
                    # Main heading
                    story.append(Paragraph(line[2:], styles['Title']))
                    story.append(Spacer(1, 12))
                elif line.startswith('## '):
                    # Sub heading
                    story.append(Paragraph(line[3:], styles['Heading2']))
                    story.append(Spacer(1, 6))
                elif line.startswith('### '):
                    # Sub-sub heading
                    story.append(Paragraph(line[4:], styles['Heading3']))
                    story.append(Spacer(1, 6))
                elif line.startswith('- ') or line.startswith('* '):
                    # Bullet point
                    story.append(Paragraph(f"• {line[2:]}", styles['Normal']))
                else:
                    # Regular text
                    story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 3))
            
            # Build PDF
            doc.build(story)
            
            self.logger.log_success(f"📄 PDF summary saved (reportlab): {pdf_path}")
            return str(pdf_path)
            
        except ImportError:
            self.logger.log_warning("⚠️ reportlab not available, trying simple text PDF...")
            return None
        except Exception as e:
            self.logger.log_warning(f"Reportlab PDF failed: {str(e)}, trying simple text PDF...")
            return None
    
    def _create_simple_text_pdf(self, summary_content: str, original_filename: str) -> Optional[str]:
        """Create a simple text-based PDF (last resort fallback)."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            # Generate PDF filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(original_filename).stem if original_filename else "document"
            pdf_filename = f"{base_name}_summary_{timestamp}.pdf"
            pdf_path = Path(tempfile.gettempdir()) / pdf_filename
            
            # Create simple text PDF
            c = canvas.Canvas(str(pdf_path), pagesize=letter)
            width, height = letter
            
            # Set up fonts
            c.setFont("Helvetica-Bold", 16)
            y_position = height - 50
            
            # Title
            c.drawString(50, y_position, "Benefits and Eligibility Summary")
            y_position -= 30
            
            # Content
            c.setFont("Helvetica", 10)
            lines = summary_content.split('\n')
            
            for line in lines:
                if y_position < 50:  # Start new page if needed
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - 50
                
                # Handle line length
                line = line.strip()
                if len(line) > 80:
                    # Wrap long lines
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            if current_line:
                                c.drawString(50, y_position, current_line.strip())
                                y_position -= 12
                            current_line = word + " "
                    if current_line:
                        c.drawString(50, y_position, current_line.strip())
                        y_position -= 12
                else:
                    c.drawString(50, y_position, line)
                    y_position -= 12
                    
                # Extra space for empty lines
                if not line:
                    y_position -= 6
            
            c.save()
            
            self.logger.log_success(f"📄 PDF summary saved (simple text): {pdf_path}")
            return str(pdf_path)
            
        except Exception as e:
            self.logger.log_error(f"Simple text PDF failed: {str(e)}")
            return None
    
    def get_summary_stats(self, summary_content: str, original_content: str) -> dict:
        """Get statistics about the generated summary."""
        
        return {
            "summary_length": len(summary_content),
            "summary_words": len(summary_content.split()),
            "original_length": len(original_content),
            "compression_ratio": round(len(summary_content) / len(original_content) * 100, 1) if original_content else 0,
            "ai_powered": self.summary_enabled
        }
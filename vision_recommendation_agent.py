"""
Vision Recommendation Agent
Analyzes document pages and recommends whether vision OCR should be used
"""

import base64
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
from PIL import Image

from agent_base import BaseAgent, AgentResponse
from config import config


class VisionRecommendationAgent(BaseAgent):
    """Agent that analyzes pages and recommends vision OCR usage."""

    def __init__(self, api_client, logger):
        super().__init__(
            agent_id="VisionRecommendationAgent",
            logger=logger,
            api_client=api_client
        )
        self.thumbnail_size = (200, 260)  # Width x Height for thumbnails

    def get_system_prompt(self) -> str:
        """Return the system prompt for vision recommendation."""
        return """You are a document analysis expert. Analyze document page images and determine if vision OCR is needed.

Vision OCR should be recommended (YES) when:
- Page contains tables, charts, graphs, or diagrams
- Page has complex layouts (multi-column, mixed text/images)
- Page contains handwritten text
- Page has forms or structured data
- Text extraction quality appears poor
- Page has images with embedded text

Vision OCR should NOT be recommended (NO) when:
- Page is simple text-only with good quality
- Page can be reliably extracted with standard text extraction
- Page is blank or nearly blank

Respond with a JSON object:
{
    "recommendation": "YES" or "NO",
    "reason": "Brief explanation (max 50 chars)",
    "confidence": 0.0-1.0
}"""

    def process(self, input_data: dict, context: dict = None) -> AgentResponse:
        """
        Analyze document and recommend vision OCR per page.

        Args:
            input_data: {"file_path": str, "page_ranges": str (optional)}
            context: Additional context

        Returns:
            AgentResponse with page recommendations
        """
        file_path = input_data.get("file_path")
        page_ranges = input_data.get("page_ranges")

        if not file_path:
            return self._error_response("No file path provided")

        try:
            # Determine file type
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.pdf':
                return self._analyze_pdf(file_path, page_ranges)
            elif file_ext in ['.md', '.markdown', '.txt']:
                return self._analyze_text_file(file_path)
            else:
                return self._error_response(f"Unsupported file type: {file_ext}")

        except Exception as e:
            self.logger.error(f"Vision recommendation failed: {e}")
            return self._error_response(str(e))

    def _analyze_pdf(self, file_path: str, page_ranges: str = None) -> AgentResponse:
        """Analyze PDF and recommend vision OCR per page."""
        self.logger.log_step(f"📂 Opening PDF: {Path(file_path).name}")
        doc = fitz.open(file_path)
        total_pages = len(doc)
        self.logger.log_step(f"📄 Total pages in document: {total_pages}")

        # Parse page ranges
        pages_to_analyze = self._parse_page_ranges(page_ranges, total_pages)
        self.logger.log_step(f"📋 Pages to analyze: {len(pages_to_analyze)} pages {pages_to_analyze}")

        recommendations = []
        heuristic_count = 0
        vision_count = 0

        for idx, page_num in enumerate(pages_to_analyze, 1):
            self.logger.log_step(f"🔍 Analyzing page {page_num} ({idx}/{len(pages_to_analyze)})...")
            page_idx = page_num - 1  # 0-indexed
            page = doc[page_idx]

            # Generate thumbnail and full preview
            self.logger.log_step(f"  🖼️  Generating thumbnails for page {page_num}...")
            thumbnail_b64 = self._generate_thumbnail(page)
            full_image_b64 = self._generate_full_preview(page)

            # Get page image for analysis
            page_image_b64 = self._get_page_image(page)

            # Quick heuristic check first (fast)
            self.logger.log_step(f"  ⚡ Running heuristic analysis on page {page_num}...")
            heuristic_result = self._quick_heuristic_check(page)

            if heuristic_result["confidence"] > 0.8:
                # High confidence from heuristics, use that
                heuristic_count += 1
                self.logger.log_step(
                    f"  ✅ Heuristic decision (confidence {heuristic_result['confidence']:.2f}): "
                    f"{heuristic_result['recommendation']} - {heuristic_result['reason']}"
                )
                recommendations.append({
                    "page": page_num,
                    "recommendation": heuristic_result["recommendation"],
                    "reason": heuristic_result["reason"],
                    "confidence": heuristic_result["confidence"],
                    "thumbnail": thumbnail_b64,
                    "full_image": full_image_b64,
                    "method": "heuristic"
                })
            else:
                # Use vision model for more complex analysis
                vision_count += 1
                self.logger.log_step(
                    f"  🧠 Heuristic inconclusive (confidence {heuristic_result['confidence']:.2f}), "
                    f"using vision model..."
                )
                vision_result = self._vision_analysis(page_image_b64, page_num)
                self.logger.log_step(
                    f"  ✅ Vision decision (confidence {vision_result['confidence']:.2f}): "
                    f"{vision_result['recommendation']} - {vision_result['reason']}"
                )
                recommendations.append({
                    "page": page_num,
                    "recommendation": vision_result["recommendation"],
                    "reason": vision_result["reason"],
                    "confidence": vision_result["confidence"],
                    "thumbnail": thumbnail_b64,
                    "full_image": full_image_b64,
                    "method": "vision"
                })

        doc.close()

        self.logger.log_success(
            f"✨ Analysis complete: {heuristic_count} pages via heuristics, "
            f"{vision_count} pages via vision model"
        )

        return AgentResponse(
            success=True,
            content=recommendations,
            confidence=1.0,
            metadata={
                "total_pages": total_pages,
                "analyzed_pages": len(recommendations),
                "heuristic_count": heuristic_count,
                "vision_count": vision_count
            }
        )

    def _analyze_text_file(self, file_path: str) -> AgentResponse:
        """Analyze text/markdown files (no vision needed)."""
        # Text files don't need vision OCR
        return AgentResponse(
            success=True,
            content=[{
                "page": 1,
                "recommendation": "NO",
                "reason": "Text-only file",
                "confidence": 1.0,
                "thumbnail": None,
                "method": "heuristic"
            }],
            confidence=1.0,
            metadata={"file_type": "text"}
        )

    def _quick_heuristic_check(self, page: fitz.Page) -> Dict:
        """Fast heuristic analysis without vision API."""
        # Extract text
        text = page.get_text()
        text_len = len(text.strip())

        # Check for images
        image_list = page.get_images()
        has_images = len(image_list) > 0

        # Check for drawings/vector graphics
        drawings = page.get_drawings()
        # Be more conservative - colored sections/borders create many drawings
        # Only flag if there are MANY drawings (likely actual charts/diagrams)
        has_complex_graphics = len(drawings) > 100

        # Additional check: ratio of drawings to text length
        # Charts/diagrams have high drawing-to-text ratio
        drawings_per_100_chars = (len(drawings) / max(text_len, 1)) * 100
        has_high_graphics_ratio = drawings_per_100_chars > 20

        # Check text blocks for layout complexity
        blocks = page.get_text("dict")["blocks"]
        text_blocks = [b for b in blocks if b.get("type") == 0]  # Type 0 = text

        # Heuristics (ordered by priority)
        if text_len < 50 and not has_images:
            return {"recommendation": "NO", "reason": "Nearly blank page", "confidence": 0.95}

        if has_images:
            return {"recommendation": "YES", "reason": "Contains images", "confidence": 0.9}

        # More conservative: only flag if MANY drawings or high ratio
        if has_complex_graphics or has_high_graphics_ratio:
            return {"recommendation": "YES", "reason": "Contains graphics/charts", "confidence": 0.85}

        # Text-rich pages are usually fine with standard extraction
        if text_len > 500:
            return {"recommendation": "NO", "reason": "Text-rich page", "confidence": 0.85}

        # Complex multi-column layouts
        if len(text_blocks) > 30:
            return {"recommendation": "YES", "reason": "Complex layout", "confidence": 0.7}

        # Default for moderate text pages: NO (prefer standard extraction)
        if text_len > 200:
            return {"recommendation": "NO", "reason": "Standard text page", "confidence": 0.75}

        # Default: uncertain, needs vision analysis
        return {"recommendation": "UNCERTAIN", "reason": "Needs analysis", "confidence": 0.5}

    def _vision_analysis(self, image_b64: str, page_num: int) -> Dict:
        """Use vision model to analyze page."""
        self.logger.log_step(f"    📡 Calling vision API for page {page_num}...")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": f"""Analyze page {page_num} and determine if vision OCR is needed.

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "recommendation": "YES",
  "reason": "brief explanation (max 50 chars)",
  "confidence": 0.9
}}

Use "YES" if the page has tables, images, charts, or complex layout.
Use "NO" if it's simple text only."""
                    }
                ]
            }
        ]

        try:
            response, tokens = self.make_api_call(messages, task="vision")
            self.logger.log_step(f"    ✅ Vision API response received (tokens: {tokens})")

            # Debug: Check if response is empty
            if not response or not response.strip():
                self.logger.warning(f"Empty response from vision API for page {page_num}")
                return {
                    "recommendation": "YES",
                    "reason": "Empty API response",
                    "confidence": 0.5
                }

            # Parse JSON response
            import json

            # Clean up response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                response = response.replace("```json", "").replace("```", "").strip()

            result = json.loads(response)

            return {
                "recommendation": result.get("recommendation", "YES"),
                "reason": result.get("reason", "Complex page")[:50],  # Limit to 50 chars
                "confidence": result.get("confidence", 0.7)
            }
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON parse error for page {page_num}: {e}")
            if 'response' in locals():
                self.logger.warning(f"Response was: {response[:200]}")
            # Default to YES if parsing fails
            return {
                "recommendation": "YES",
                "reason": "JSON parse error",
                "confidence": 0.5
            }
        except Exception as e:
            self.logger.warning(f"Vision analysis failed for page {page_num}: {e}")
            # Default to YES if analysis fails
            return {
                "recommendation": "YES",
                "reason": "Analysis failed (default YES)",
                "confidence": 0.5
            }

    def _generate_thumbnail(self, page: fitz.Page) -> str:
        """Generate a thumbnail image for the page."""
        # Render page at lower DPI for thumbnail
        pix = page.get_pixmap(dpi=72)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Resize to thumbnail size
        img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()

        return img_b64

    def _generate_full_preview(self, page: fitz.Page) -> str:
        """Generate a full-resolution preview image for the page."""
        # Render at higher DPI for better quality preview
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Convert to base64 without resizing
        buffered = BytesIO()
        img.save(buffered, format="PNG", optimize=True)
        img_b64 = base64.b64encode(buffered.getvalue()).decode()

        return img_b64

    def _get_page_image(self, page: fitz.Page) -> str:
        """Get full page image for vision analysis."""
        # Render at moderate DPI for analysis
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()

        return img_b64

    def _parse_page_ranges(self, page_ranges: str, total_pages: int) -> List[int]:
        """Parse page ranges string into list of page numbers."""
        if not page_ranges or not page_ranges.strip():
            return list(range(1, total_pages + 1))

        pages = set()
        for part in page_ranges.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())
                pages.update(range(start, end + 1))
            else:
                pages.add(int(part))

        # Filter to valid page numbers
        return sorted([p for p in pages if 1 <= p <= total_pages])

    def _error_response(self, error_msg: str) -> AgentResponse:
        """Create error response."""
        return AgentResponse(
            success=False,
            content=None,
            confidence=0.0,
            metadata={"error": error_msg}
        )

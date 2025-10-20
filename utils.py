"""
Utility functions for OCR processing
Consolidates common functionality used across multiple modules
"""

import base64
from pathlib import Path
from typing import List, Tuple, Optional, Union
from PIL import Image
import io


def validate_page_ranges(page_ranges_str: str, total_pages: int) -> Tuple[bool, str, List[int]]:
    """
    Parse and validate page range string.

    Args:
        page_ranges_str: String like "1-5, 10, 15-20"
        total_pages: Total number of pages in document

    Returns:
        Tuple of (is_valid, error_message, page_list)
        - is_valid: True if parsing succeeded
        - error_message: Error description if invalid, empty string otherwise
        - page_list: List of valid page numbers (0-indexed)
    """
    if not page_ranges_str or not page_ranges_str.strip():
        return (True, "", list(range(total_pages)))

    pages = set()
    parts = page_ranges_str.split(',')

    try:
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip())

                if start < 1 or end > total_pages or start > end:
                    return (False, f"Invalid range {start}-{end}. Pages must be between 1 and {total_pages}", [])

                # Convert to 0-indexed and validate
                for page in range(start, end + 1):
                    pages.add(page - 1)  # Convert to 0-indexed
            else:
                page = int(part.strip())
                if page < 1 or page > total_pages:
                    return (False, f"Page {page} is out of range. Document has {total_pages} pages", [])
                pages.add(page - 1)  # Convert to 0-indexed
    except ValueError as e:
        return (False, f"Invalid page range format: {page_ranges_str}", [])

    page_list = sorted(list(pages)) if pages else list(range(total_pages))
    return (True, "", page_list)


def extract_document_title(filename: str) -> str:
    """
    Extract a clean document title from filename.
    
    Args:
        filename: Path or filename string
        
    Returns:
        Cleaned title string
    """
    if not filename:
        return "Document"
    
    title = Path(filename).stem
    # Convert to title case and replace separators with spaces
    title = title.replace('-', ' ').replace('_', ' ').title()
    return title


def image_to_base64(image: Union[Image.Image, bytes], format: str = "PNG", quality: int = 95) -> str:
    """
    Convert PIL Image or bytes to base64 string.

    Args:
        image: PIL Image object or image bytes
        format: Image format (PNG, JPEG, etc.)
        quality: JPEG compression quality (1-100, only used for JPEG format)

    Returns:
        Base64 encoded string
    """
    if isinstance(image, Image.Image):
        buffer = io.BytesIO()
        if format.upper() in ['JPEG', 'JPG']:
            image.save(buffer, format='JPEG', quality=quality, optimize=True)
        else:
            image.save(buffer, format=format)
        image_bytes = buffer.getvalue()
    else:
        image_bytes = image

    return base64.b64encode(image_bytes).decode('utf-8')


def parse_json_response(response_text: str, start_marker: str = "{", end_marker: str = "}") -> dict:
    """
    Extract and parse JSON from potentially mixed text response.
    
    Args:
        response_text: Text that may contain JSON
        start_marker: Start of JSON object
        end_marker: End of JSON object
        
    Returns:
        Parsed JSON dict or empty dict if parsing fails
    """
    import json
    
    try:
        # Find JSON boundaries
        start_idx = response_text.find(start_marker)
        if start_idx == -1:
            return {}
        
        # Find matching end marker
        depth = 0
        end_idx = -1
        for i in range(start_idx, len(response_text)):
            if response_text[i] == start_marker:
                depth += 1
            elif response_text[i] == end_marker:
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        
        if end_idx == -1:
            return {}
        
        json_str = response_text[start_idx:end_idx]
        return json.loads(json_str)
        
    except (json.JSONDecodeError, ValueError):
        return {}


def format_evaluation_score(score: float, max_score: float = 100) -> str:
    """
    Format evaluation score consistently.
    
    Args:
        score: Numeric score
        max_score: Maximum possible score
        
    Returns:
        Formatted score string
    """
    try:
        score_val = float(score)
        return f"{score_val:.1f}/{max_score}"
    except (ValueError, TypeError):
        return "N/A"


def get_recommendation_color(recommendation: str) -> str:
    """
    Get color code for recommendation status.
    
    Args:
        recommendation: ACCEPT, REJECT, or REVIEW
        
    Returns:
        HTML color code
    """
    colors = {
        "ACCEPT": "#059669",  # Green
        "REJECT": "#dc2626",  # Red
        "REVIEW": "#d97706",  # Orange
    }
    return colors.get(recommendation.upper(), "#94a3b8")  # Default gray
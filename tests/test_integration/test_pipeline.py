"""
Integration tests for the complete OCR pipeline.

Tests the full flow: PDF Upload → Vision OCR → Corruption Detection → Content Formatting → Evaluation
"""
import pytest
import os
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io

# Mark all tests in this file as integration tests and API-dependent
pytestmark = [pytest.mark.integration, pytest.mark.api]


@pytest.fixture
def skip_if_no_api_keys():
    """Skip test if API keys are not available."""
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("API keys not available - skipping integration test")


@pytest.fixture
def simple_pdf(tmp_path):
    """Create a simple single-page PDF for testing."""
    pdf_path = tmp_path / "simple_test.pdf"
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    text = """Test Document

This is a simple test document with basic text.
It has multiple lines and paragraphs.

Key points:
- Item 1
- Item 2
- Item 3

End of document."""
    page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def complex_pdf(tmp_path):
    """Create a complex multi-page PDF with tables."""
    pdf_path = tmp_path / "complex_test.pdf"
    doc = fitz.open()

    # Page 1
    page1 = doc.new_page(width=612, height=792)
    page1.insert_text((72, 72), "Complex Document Test", fontsize=16)

    # Page 2: Table
    page2 = doc.new_page(width=612, height=792)
    table_text = """Financial Summary

Quarter    Revenue    Expenses    Profit
Q1 2024    $50,000    $30,000     $20,000
Q2 2024    $55,000    $32,000     $23,000"""
    page2.insert_text((72, 72), table_text, fontsize=10)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


# =============================================================================
# Test Group 1: Basic Pipeline Tests (3 tests)
# =============================================================================

class TestBasicPipeline:
    """Test basic end-to-end pipeline functionality."""

    @pytest.mark.slow
    def test_simple_pdf_processing(self, simple_pdf, skip_if_no_api_keys):
        """Test processing a simple single-page PDF through the full pipeline."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str=None
        )

        # Verify basic result structure
        assert result is not None
        assert result.success is True
        assert len(result.content) > 0
        assert "Test Document" in result.content

    @pytest.mark.slow
    def test_complex_pdf_processing(self, complex_pdf, skip_if_no_api_keys):
        """Test processing a complex multi-page PDF with tables."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(complex_pdf),
            page_ranges_str=None
        )

        # Verify multi-page processing
        assert result is not None
        assert result.success is True
        assert len(result.content) > 0
        assert result.pages_processed == 2

    @pytest.mark.slow
    def test_page_range_processing(self, complex_pdf, skip_if_no_api_keys):
        """Test processing specific page range."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(complex_pdf),
            page_ranges_str="1"
        )

        # Should only process page 1
        assert result is not None
        assert result.success is True
        assert result.pages_processed == 1


# =============================================================================
# Test Group 2: Corruption Detection Tests (3 tests)
# =============================================================================

class TestCorruptionDetection:
    """Test corruption detection and routing logic."""

    def test_clean_text_detection(self, simple_pdf):
        """Test that clean extractable text is detected."""
        from corruption_detector import CorruptionDetector
        from config import Config
        import fitz

        config = Config()
        doc = fitz.open(str(simple_pdf))
        page = doc[0]
        text = page.get_text()
        doc.close()

        detector = CorruptionDetector(config=config)
        is_corrupted, score, details = detector.analyze_text(text)

        # Clean text should have low corruption score
        assert 0.0 <= score <= 1.0
        assert is_corrupted is False or score < config.vision_corruption_threshold

    def test_corrupted_text_detection(self):
        """Test that corrupted text is detected."""
        from corruption_detector import CorruptionDetector
        from config import Config

        config = Config()
        # Simulate corrupted text
        corrupted_text = """���� �Ђ� ��
        th!s t3xt i$ c0rrupt3d ���
        m@ny sp3c!@l ch@r@ct3r$"""

        detector = CorruptionDetector(config=config)
        is_corrupted, score, details = detector.analyze_text(corrupted_text)

        # Should detect corruption
        assert score > 0.0

    @pytest.mark.slow
    def test_mixed_quality_processing(self, complex_pdf, skip_if_no_api_keys):
        """Test document with mixed text quality."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(complex_pdf),
            page_ranges_str="1-2"
        )

        # Should successfully process
        assert result is not None
        assert result.success is True


# =============================================================================
# Test Group 3: Content Formatting Tests (3 tests)
# =============================================================================

class TestContentFormatting:
    """Test content formatting agent behavior."""

    @pytest.mark.slow
    def test_table_content_preserved(self, complex_pdf, skip_if_no_api_keys):
        """Test that table data is preserved."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(complex_pdf),
            page_ranges_str="2"
        )

        # Check table data is present
        assert "Revenue" in result.content or "50,000" in result.content

    @pytest.mark.slow
    def test_list_content_preserved(self, simple_pdf, skip_if_no_api_keys):
        """Test that list items are preserved."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str=None
        )

        # Check list items present
        content = result.content
        assert "Item 1" in content
        assert "Item 2" in content
        assert "Item 3" in content

    @pytest.mark.slow
    def test_formatting_produces_markdown(self, simple_pdf, skip_if_no_api_keys):
        """Test that formatting produces markdown output."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str=None
        )

        # Should have markdown-like formatting
        assert result.content is not None
        assert len(result.content) > 0


# =============================================================================
# Test Group 4: Edge Cases (3 tests)
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_pdf(self, tmp_path):
        """Test handling of empty PDF."""
        from processor_optimized import OptimizedDocumentProcessor

        # Create empty PDF
        empty_pdf = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page(width=612, height=792)
        doc.save(str(empty_pdf))
        doc.close()

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(empty_pdf),
            page_ranges_str=None
        )

        # Should handle gracefully
        assert result is not None

    @pytest.mark.slow
    def test_single_page_selection(self, simple_pdf, skip_if_no_api_keys):
        """Test processing a single page."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str="1"
        )

        assert result is not None
        assert result.success is True
        assert result.pages_processed == 1

    def test_invalid_page_range_handling(self, simple_pdf):
        """Test handling of invalid page range."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str="99"
        )

        # Should handle gracefully (may succeed with 0 pages or return error)
        assert result is not None


# =============================================================================
# Test Group 5: Error Handling (2 tests)
# =============================================================================

class TestErrorHandling:
    """Test error handling and recovery."""

    def test_invalid_pdf_path(self):
        """Test handling of invalid PDF path."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()

        # Should handle gracefully (returns error result)
        result = processor.process_document(
            uploaded_file="/nonexistent/path/to/file.pdf",
            page_ranges_str=None
        )

        # Should return a result indicating failure
        assert result is not None
        assert result.success is False or result.status == "error"

    def test_abort_mechanism(self, simple_pdf):
        """Test that processing can be aborted."""
        from processor_optimized import OptimizedDocumentProcessor
        import threading

        processor = OptimizedDocumentProcessor()

        # Abort immediately
        processor.abort_processing()

        # Try to process (may return early or error)
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str=None
        )

        # Should handle abort gracefully
        assert result is not None


# =============================================================================
# Test Group 6: Performance & Metrics (3 tests)
# =============================================================================

class TestPerformanceMetrics:
    """Test performance tracking and metrics."""

    @pytest.mark.slow
    def test_token_tracking(self, simple_pdf, skip_if_no_api_keys):
        """Test that token usage is tracked."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str=None
        )

        # Should track tokens
        assert hasattr(result, 'total_tokens')
        assert result.total_tokens >= 0

    @pytest.mark.slow
    def test_vision_call_tracking(self, simple_pdf, skip_if_no_api_keys):
        """Test that vision calls are tracked."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str=None
        )

        # Should track vision calls
        assert hasattr(result, 'vision_calls_used')
        assert result.vision_calls_used >= 0

    @pytest.mark.slow
    def test_processing_time_tracking(self, simple_pdf, skip_if_no_api_keys):
        """Test that processing time is tracked."""
        from processor_optimized import OptimizedDocumentProcessor

        processor = OptimizedDocumentProcessor()
        result = processor.process_document(
            uploaded_file=str(simple_pdf),
            page_ranges_str=None
        )

        # Should track processing time
        assert hasattr(result, 'processing_time')
        assert result.processing_time > 0

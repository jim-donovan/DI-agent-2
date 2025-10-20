"""API Response Models with OpenAPI documentation."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingResult(BaseModel):
    """Results from document processing."""

    content: str = Field(
        ...,
        description="Processed markdown content",
        example="# Document Title\n\nExtracted content..."
    )

    raw_ocr: Optional[str] = Field(
        None,
        description="Unformatted vision OCR output (if enabled)"
    )

    evaluation: Optional[Dict[str, Any]] = Field(
        None,
        description="Quality evaluation report (if enabled)"
    )

    summary: Optional[str] = Field(
        None,
        description="Benefits & eligibility summary (if enabled)"
    )

    page_count: int = Field(
        ...,
        description="Total number of pages processed",
        example=25
    )

    vision_pages: int = Field(
        ...,
        description="Number of pages using vision OCR",
        example=8
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing metadata"
    )


class JobResponse(BaseModel):
    """Response for job status and results."""

    job_id: str = Field(
        ...,
        description="Unique job identifier",
        example="550e8400-e29b-41d4-a716-446655440000"
    )

    status: JobStatus = Field(
        ...,
        description="Current job status"
    )

    progress: Optional[float] = Field(
        None,
        description="Processing progress (0-100)",
        ge=0,
        le=100,
        example=65.5
    )

    result: Optional[ProcessingResult] = Field(
        None,
        description="Processing results (when completed)"
    )

    error: Optional[str] = Field(
        None,
        description="Error message (if failed)",
        example="Failed to process page 5: Timeout"
    )

    created_at: datetime = Field(
        ...,
        description="Job creation timestamp"
    )

    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )

    completed_at: Optional[datetime] = Field(
        None,
        description="Completion timestamp"
    )


class PageRecommendation(BaseModel):
    """Vision OCR recommendation for a single page."""

    page_number: int = Field(
        ...,
        description="Page number (1-indexed)",
        ge=1,
        example=1
    )

    recommendation: str = Field(
        ...,
        description="Vision OCR recommendation",
        pattern="^(YES|NO)$",
        example="YES"
    )

    confidence: float = Field(
        ...,
        description="Confidence score (0-1)",
        ge=0,
        le=1,
        example=0.95
    )

    reasoning: str = Field(
        ...,
        description="Explanation for recommendation",
        example="Complex tables detected, vision OCR recommended"
    )


class DocumentAnalyzeResponse(BaseModel):
    """Response from document analysis."""

    filename: str = Field(
        ...,
        description="Original filename",
        example="contract.pdf"
    )

    page_count: int = Field(
        ...,
        description="Total number of pages",
        example=25
    )

    recommendations: List[PageRecommendation] = Field(
        ...,
        description="Vision OCR recommendations per page"
    )

    summary: Dict[str, int] = Field(
        ...,
        description="Summary counts",
        example={"vision_yes": 8, "vision_no": 17}
    )


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: str = Field(
        ...,
        description="Error type",
        example="ValidationError"
    )

    message: str = Field(
        ...,
        description="Human-readable error message",
        example="Unsupported file type. Supported: .pdf, .md, .txt"
    )

    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(
        ...,
        description="Service health status",
        example="healthy"
    )

    version: str = Field(
        ...,
        description="API version",
        example="1.0.0"
    )

    uptime: float = Field(
        ...,
        description="Service uptime in seconds",
        example=3600.5
    )

    workers: Dict[str, Any] = Field(
        default_factory=dict,
        description="Worker status information"
    )


class ConfigResponse(BaseModel):
    """API configuration response."""

    supported_formats: List[str] = Field(
        ...,
        description="Supported file formats",
        example=[".pdf", ".md", ".txt", ".xlsx", ".xls", ".csv"]
    )

    max_file_size_mb: int = Field(
        ...,
        description="Maximum file size in MB",
        example=50
    )

    max_pages: int = Field(
        ...,
        description="Maximum pages per document",
        example=500
    )

    features: Dict[str, bool] = Field(
        ...,
        description="Available features",
        example={
            "summary_generation": True,
            "quality_reports": True,
            "vision_ocr": True,
            "excel_processing": True
        }
    )

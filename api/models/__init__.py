"""API Models Package."""
from .requests import (
    DocumentProcessRequest,
    DocumentProcessOptions,
    DocumentAnalyzeRequest,
    ExcelProcessRequest,
    ExcelProcessOptions,
    ExcelColumnConfig,
    VisionRecommendation
)
from .responses import (
    JobResponse,
    JobStatus,
    ProcessingResult,
    DocumentAnalyzeResponse,
    PageRecommendation,
    ErrorResponse,
    HealthResponse,
    ConfigResponse
)

__all__ = [
    # Requests
    "DocumentProcessRequest",
    "DocumentProcessOptions",
    "DocumentAnalyzeRequest",
    "ExcelProcessRequest",
    "ExcelProcessOptions",
    "ExcelColumnConfig",
    "VisionRecommendation",
    # Responses
    "JobResponse",
    "JobStatus",
    "ProcessingResult",
    "DocumentAnalyzeResponse",
    "PageRecommendation",
    "ErrorResponse",
    "HealthResponse",
    "ConfigResponse",
]

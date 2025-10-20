"""FastAPI Application with Auto-Generated Swagger Documentation.

This module sets up the FastAPI application with:
- Auto-generated OpenAPI/Swagger documentation
- Request/response validation with Pydantic models
- CORS support
- Health check endpoints
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from typing import Dict, Any

from api.models import (
    DocumentProcessRequest,
    DocumentAnalyzeRequest,
    ExcelProcessRequest,
    JobResponse,
    DocumentAnalyzeResponse,
    ErrorResponse,
    HealthResponse,
    ConfigResponse,
    JobStatus,
)

# Service start time for uptime calculation
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("🚀 Document Ingestion API starting...")
    yield
    # Shutdown
    print("👋 Document Ingestion API shutting down...")


# Create FastAPI application with comprehensive OpenAPI configuration
app = FastAPI(
    title="Document Ingestion API",
    description="""
    **Document Ingestion API** - AI-powered document processing service

    ## Features

    * 📄 **Multi-format Support**: PDF, Markdown, TXT, Excel (XLSX/XLS/CSV)
    * 🔍 **Vision OCR**: GPT-4 Vision for complex documents
    * 🤖 **AI Agents**: Specialized agents for formatting, quality checks, summaries
    * 📊 **Excel Processing**: Smart label detection and markdown conversion
    * ⚡ **Async Processing**: Background job processing with webhooks
    * 📈 **Quality Reports**: Dual evaluation (OpenAI + Anthropic)

    ## Workflow

    1. **Analyze** document to get vision recommendations (optional)
    2. **Submit** processing job with options
    3. **Monitor** job status via polling or webhook
    4. **Retrieve** processed content and reports

    ## Authentication

    All endpoints require authentication via:
    - **API Key**: `X-API-Key` header
    - **JWT Token**: `Authorization: Bearer <token>` header

    ## Rate Limits

    - 100 requests per minute per API key
    - 10 concurrent processing jobs per account
    """,
    version="1.0.0",
    contact={
        "name": "Document Ingestion Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json",  # OpenAPI schema
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for standardized error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with ErrorResponse format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            details=getattr(exc, "details", None),
        ).dict(),
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health Check",
    description="Check API service health and status",
)
async def health_check() -> HealthResponse:
    """
    Get service health status.

    Returns uptime, version, and worker status.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=time.time() - START_TIME,
        workers={
            "active": 0,  # TODO: Get from Celery
            "available": 4,
        },
    )


@app.get(
    "/config",
    response_model=ConfigResponse,
    tags=["System"],
    summary="API Configuration",
    description="Get API capabilities and limits",
)
async def get_config() -> ConfigResponse:
    """
    Get API configuration.

    Returns supported formats, limits, and available features.
    """
    return ConfigResponse(
        supported_formats=[".pdf", ".md", ".txt", ".xlsx", ".xls", ".csv"],
        max_file_size_mb=50,
        max_pages=500,
        features={
            "summary_generation": True,
            "quality_reports": True,
            "vision_ocr": True,
            "excel_processing": True,
        },
    )


@app.post(
    "/documents/analyze",
    response_model=DocumentAnalyzeResponse,
    tags=["Documents"],
    summary="Analyze Document",
    description="Get vision OCR recommendations for each page",
    responses={
        200: {
            "description": "Analysis complete",
            "content": {
                "application/json": {
                    "example": {
                        "filename": "contract.pdf",
                        "page_count": 25,
                        "recommendations": [
                            {
                                "page_number": 1,
                                "recommendation": "YES",
                                "confidence": 0.95,
                                "reasoning": "Complex tables detected",
                            }
                        ],
                        "summary": {"vision_yes": 8, "vision_no": 17},
                    }
                }
            },
        },
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def analyze_document(request: DocumentAnalyzeRequest) -> DocumentAnalyzeResponse:
    """
    Analyze document for vision OCR recommendations.

    This endpoint processes the document and returns recommendations
    for which pages should use vision OCR vs. standard text extraction.

    - **file**: Base64-encoded document or URL
    - **filename**: Original filename with extension
    - **page_ranges**: Pages to analyze (default: all)

    Returns page-by-page recommendations with confidence scores.
    """
    # TODO: Implement actual analysis logic
    raise HTTPException(status_code=501, detail="Analysis endpoint not yet implemented")


@app.post(
    "/documents/process",
    response_model=JobResponse,
    status_code=202,
    tags=["Documents"],
    summary="Process Document",
    description="Submit document for processing (async)",
    responses={
        202: {
            "description": "Job created and queued",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "pending",
                        "progress": None,
                        "result": None,
                        "created_at": "2025-10-11T12:00:00Z",
                        "updated_at": "2025-10-11T12:00:00Z",
                    }
                }
            },
        },
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def process_document(
    request: DocumentProcessRequest, background_tasks: BackgroundTasks
) -> JobResponse:
    """
    Process document asynchronously.

    Submits document for processing and returns immediately with job ID.
    Use the job ID to poll status or provide a callback_url for webhook notification.

    - **file**: Base64-encoded document
    - **filename**: Original filename
    - **options**: Processing options (summary, quality report, vision settings, etc.)
    - **callback_url**: Webhook URL for completion notification (optional)

    Returns job information for status tracking.
    """
    # TODO: Implement actual processing logic with Celery
    raise HTTPException(status_code=501, detail="Processing endpoint not yet implemented")


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    tags=["Jobs"],
    summary="Get Job Status",
    description="Check processing job status and results",
    responses={
        200: {"description": "Job found"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    },
)
async def get_job_status(job_id: str) -> JobResponse:
    """
    Get job status and results.

    Poll this endpoint to check processing status. When status is 'completed',
    the result field will contain the processed content.

    - **job_id**: Unique job identifier from /documents/process

    Returns job status, progress, and results (when complete).
    """
    # TODO: Implement job status lookup
    raise HTTPException(status_code=501, detail="Job status endpoint not yet implemented")


@app.delete(
    "/jobs/{job_id}",
    status_code=204,
    tags=["Jobs"],
    summary="Cancel Job",
    description="Cancel a pending or running job",
    responses={
        204: {"description": "Job cancelled"},
        404: {"model": ErrorResponse, "description": "Job not found"},
        409: {"model": ErrorResponse, "description": "Job already completed"},
    },
)
async def cancel_job(job_id: str):
    """
    Cancel a processing job.

    Cancels a pending or in-progress job. Completed jobs cannot be cancelled.

    - **job_id**: Job identifier to cancel
    """
    # TODO: Implement job cancellation
    raise HTTPException(status_code=501, detail="Job cancellation not yet implemented")


@app.post(
    "/excel/process",
    response_model=JobResponse,
    status_code=202,
    tags=["Excel"],
    summary="Process Excel File",
    description="Process Excel/CSV file with custom column configuration",
    responses={
        202: {"description": "Job created"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
)
async def process_excel(
    request: ExcelProcessRequest, background_tasks: BackgroundTasks
) -> JobResponse:
    """
    Process Excel/CSV file.

    Processes spreadsheet with custom column configuration for labels and data.
    Supports up to 5 label columns and intelligent data formatting.

    - **file**: Base64-encoded Excel/CSV file
    - **filename**: Original filename
    - **options**: Column configuration, header rows, section headers
    - **callback_url**: Webhook URL for completion (optional)

    Returns job information for status tracking.
    """
    # TODO: Implement Excel processing
    raise HTTPException(status_code=501, detail="Excel processing not yet implemented")


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Document Ingestion API...")
    print("📚 Swagger UI: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("📄 OpenAPI Schema: http://localhost:8000/openapi.json")

    uvicorn.run(app, host="0.0.0.0", port=8000)

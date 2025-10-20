"""API Request Models with OpenAPI documentation."""
from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class VisionRecommendation(str, Enum):
    """Vision OCR recommendation."""
    YES = "YES"
    NO = "NO"


class DocumentProcessOptions(BaseModel):
    """Options for document processing."""

    page_ranges: Optional[str] = Field(
        None,
        description="Page ranges to process (e.g., '1-5,10,15-20'). Leave empty for all pages.",
        example="1-5,10"
    )

    enable_summary: bool = Field(
        False,
        description="Generate a benefits & eligibility summary"
    )

    enable_quality_report: bool = Field(
        False,
        description="Run dual evaluation (OpenAI + Anthropic) for quality assessment"
    )

    enable_raw_ocr: bool = Field(
        False,
        description="Capture unformatted vision OCR output"
    )

    vision_page_settings: Optional[Dict[int, VisionRecommendation]] = Field(
        None,
        description="Override vision OCR settings per page. Key: page number, Value: 'YES' or 'NO'",
        example={"1": "YES", "2": "NO", "3": "YES"}
    )


class DocumentProcessRequest(BaseModel):
    """Request to process a document."""

    file: str = Field(
        ...,
        description="Base64-encoded file content or URL to document",
        example="data:application/pdf;base64,JVBERi0xLjQK..."
    )

    filename: str = Field(
        ...,
        description="Original filename with extension",
        example="contract.pdf",
        min_length=1,
        max_length=255
    )

    options: DocumentProcessOptions = Field(
        default_factory=DocumentProcessOptions,
        description="Processing options"
    )

    callback_url: Optional[str] = Field(
        None,
        description="Webhook URL to receive completion notification",
        example="https://your-app.com/webhooks/document-complete"
    )

    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename has supported extension."""
        supported = ['.pdf', '.md', '.markdown', '.txt']
        if not any(v.lower().endswith(ext) for ext in supported):
            raise ValueError(f"Unsupported file type. Supported: {', '.join(supported)}")
        return v


class DocumentAnalyzeRequest(BaseModel):
    """Request to analyze document for vision recommendations."""

    file: str = Field(
        ...,
        description="Base64-encoded file content or URL to document"
    )

    filename: str = Field(
        ...,
        description="Original filename with extension",
        example="document.pdf"
    )

    page_ranges: Optional[str] = Field(
        "all",
        description="Page ranges to analyze (default: all)",
        example="1-10"
    )


class ExcelColumnConfig(BaseModel):
    """Configuration for Excel column processing."""

    column: str = Field(
        ...,
        description="Column identifier (e.g., 'A', 'B', 'C')",
        example="A"
    )

    role: Literal["Label 1", "Label 2", "Label 3", "Label 4", "Label 5", "Data", "Skip"] = Field(
        ...,
        description="Role of the column in processing",
        example="Label 1"
    )


class ExcelProcessOptions(BaseModel):
    """Options for Excel processing."""

    header_rows: int = Field(
        1,
        description="Number of header rows to skip",
        ge=0,
        le=10
    )

    column_config: list[ExcelColumnConfig] = Field(
        ...,
        description="Configuration for each column"
    )

    include_section_headers: bool = Field(
        False,
        description="Add H2 section headers to group related data"
    )


class ExcelProcessRequest(BaseModel):
    """Request to process Excel/CSV file."""

    file: str = Field(
        ...,
        description="Base64-encoded file content"
    )

    filename: str = Field(
        ...,
        description="Original filename with extension",
        example="data.xlsx"
    )

    options: ExcelProcessOptions = Field(
        ...,
        description="Excel processing options"
    )

    callback_url: Optional[str] = Field(
        None,
        description="Webhook URL for completion notification"
    )

    @validator('filename')
    def validate_excel_filename(cls, v):
        """Validate Excel filename."""
        supported = ['.xlsx', '.xls', '.csv']
        if not any(v.lower().endswith(ext) for ext in supported):
            raise ValueError(f"Unsupported file type. Supported: {', '.join(supported)}")
        return v

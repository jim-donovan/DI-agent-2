# Document Ingestion API

FastAPI-based REST API for the Document Ingestion system with auto-generated Swagger documentation.

## Quick Start

### Install Dependencies

```bash
pip install fastapi uvicorn[standard] pydantic
```

### Run the API Server

```bash
# Development mode with auto-reload
python api/main.py

# Or using uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API Documentation

The API uses Pydantic models to auto-generate comprehensive OpenAPI/Swagger documentation. All endpoints include:

- **Request schemas** with validation rules
- **Response schemas** with example data
- **Error responses** with standardized format
- **Field descriptions** and constraints
- **Interactive testing** via Swagger UI

## Endpoints

### System

- `GET /health` - Service health check
- `GET /config` - API configuration and capabilities

### Documents

- `POST /documents/analyze` - Analyze document for vision recommendations
- `POST /documents/process` - Submit document for processing (async)

### Jobs

- `GET /jobs/{job_id}` - Get job status and results
- `DELETE /jobs/{job_id}` - Cancel job

### Excel

- `POST /excel/process` - Process Excel/CSV with column config

## Request/Response Models

### Document Processing Request

```json
{
  "file": "data:application/pdf;base64,JVBERi0xLjQK...",
  "filename": "contract.pdf",
  "options": {
    "page_ranges": "1-5,10",
    "enable_summary": true,
    "enable_quality_report": false,
    "enable_raw_ocr": true,
    "vision_page_settings": {
      "1": "YES",
      "2": "NO",
      "3": "YES"
    }
  },
  "callback_url": "https://your-app.com/webhook"
}
```

### Job Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "result": null,
  "created_at": "2025-10-11T12:00:00Z",
  "updated_at": "2025-10-11T12:05:30Z"
}
```

### Completed Job with Results

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "result": {
    "content": "# Document Title\n\nExtracted content...",
    "raw_ocr": "Unformatted vision output...",
    "evaluation": { "score": 0.95, "issues": [] },
    "summary": "Benefits summary...",
    "page_count": 25,
    "vision_pages": 8,
    "metadata": {}
  },
  "created_at": "2025-10-11T12:00:00Z",
  "updated_at": "2025-10-11T12:10:00Z",
  "completed_at": "2025-10-11T12:10:00Z"
}
```

## Architecture

### Pydantic Models

All request/response schemas defined in `api/models/`:

- **requests.py** - Input models with validation
- **responses.py** - Output models with examples
- **__init__.py** - Package exports

### FastAPI Application

Main application in `api/main.py`:

- Auto-generated OpenAPI schema
- Request validation
- Response serialization
- Error handling
- CORS support

### Key Features

1. **Type Safety**: Pydantic validates all input/output
2. **Auto Documentation**: OpenAPI schema generated from models
3. **Interactive Testing**: Swagger UI for live API testing
4. **Standardized Errors**: ErrorResponse model for all errors
5. **Async Support**: Background processing with FastAPI BackgroundTasks

## Development

### Adding New Endpoints

1. Create request/response models in `api/models/`
2. Add endpoint decorator in `api/main.py`
3. Include comprehensive docstring
4. Define response models and status codes
5. Documentation auto-updates!

Example:

```python
@app.post(
    "/new-endpoint",
    response_model=MyResponse,
    tags=["Category"],
    summary="Short description",
    description="Detailed description",
)
async def my_endpoint(request: MyRequest) -> MyResponse:
    """
    Endpoint documentation shown in Swagger UI.

    - **param1**: Description
    - **param2**: Description
    """
    # Implementation
    pass
```

### Testing

```bash
# Run unit tests
pytest tests/test_api/

# Test with curl
curl http://localhost:8000/health

# Test with httpie
http GET localhost:8000/config
```

## Next Steps

1. **Implement endpoint logic** - Currently returns 501 (not implemented)
2. **Add Celery integration** - For async background processing
3. **Add authentication** - JWT or API key middleware
4. **Add rate limiting** - With Redis or in-memory store
5. **Add webhook support** - Callback notifications
6. **Deploy** - With Docker/K8s/cloud platform

## Production Considerations

- Configure CORS appropriately (not `allow_origins=["*"]`)
- Add authentication middleware
- Set up rate limiting
- Use production ASGI server (Gunicorn + Uvicorn workers)
- Configure logging and monitoring
- Set up health checks for orchestration
- Use environment variables for configuration

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Document Ingestion (DI) Agent 2 - A multi-agent OCR processing system that extracts text from PDFs and images using specialized AI agents with vision capabilities. Built as a Gradio-based web application optimized for accurate document extraction.

## Key Commands

### Running the Application
```bash
python app.py                     # Run the Gradio interface locally (auto-shares via ngrok on localhost)
python api/main.py                # Run the FastAPI REST API server (port 8000)
```

### Testing
```bash
pytest                            # Run all tests
pytest tests/test_file.py         # Run a specific test file
pytest tests/test_file.py::test_name  # Run a single test
pytest tests/test_core/           # Run tests in a specific directory
pytest -m unit                    # Run only unit tests
pytest -m "not api"               # Skip tests that hit external APIs
pytest -v --tb=short              # Verbose output with short traceback
```

### Dependencies Management
```bash
pip install -r requirements.txt   # Install all dependencies
pip install -r requirements-test.txt  # Install test dependencies
```

### Environment Setup
- Create `.env` file with API keys:
  - `ANTHROPIC_API_KEY` (required for vision OCR, content formatting, and corruption detection)
  - `OPENAI_API_KEY` (optional, only used for evaluation comparison with gpt-4o-mini)

### Environment Variables
Key configuration flags in `.env`:
- `ENABLE_CONTENT_FORMATTING_AGENT` (default: `true`) - Enable/disable content formatting
- `ENABLE_SUMMARY_AGENT` (default: `false`) - Enable/disable summary generation
- `USE_PARALLEL_VISION` (default: `true`) - Enable parallel vision processing
- `USE_LOCAL_DOWNLOADS_DIRECTORY` (default: `true`) - Use local temp dir vs HuggingFace deployment mode
- `DEBUG_OCR_PIPELINE` (default: `false`) - Enable detailed OCR stage logging
- `TALLY_FORM_ID` (optional) - Tally form ID for feedback collection

## Architecture Overview

### Agent System
The codebase implements a multi-agent architecture where specialized agents handle different aspects of document processing:

1. **Base Agent Architecture** (`agent_base.py`):
   - Abstract base class defining agent structure
   - State management and memory tracking
   - Confidence scoring system
   - Standardized response format

2. **Specialized Agents**:
   - **VisionOCRAgent** (`vision_ocr_agent.py`): Extracts text from images using Claude Sonnet 4.5 with vision capabilities
   - **CorruptionAgent** (`corruption_agent.py`): Detects and analyzes text corruption using Claude Sonnet 4.5
   - **ContentFormattingAgent** (`content_formatting_agent.py`): Formats and structures extracted content using Claude Sonnet 4.5
   - **CheckerAgent** (`checker_agent.py`): Validates extraction quality and generates quality reports using GPT-4o-mini
   - **SummaryAgent** (`summary_agent.py`): Generates document summaries
   - **Excel Agents**:
     - **ExcelStructureAgent** (`excel_structure_agent.py`): Detects table structure, identifies label columns (supports up to 5 consecutive text columns), and classifies data columns
     - **ExcelFormattingAgent** (`excel_formatting_agent.py`): Concatenates all label columns with " - " separator and formats data in markdown lists
     - **ExcelIngestionAgent** (`excel_ingestion_agent.py`): Orchestrates Excel processing pipeline with openpyxl for merged cell handling

3. **Core Processing Pipeline** (`processor_optimized.py`):
   - Orchestrates agent interactions through `OptimizedDocumentProcessor`
   - Two processing modes:
     - **Systematic processing**: Full agent pipeline (vision → corruption detection → formatting → evaluation)
     - **Traditional parallel processing**: Fallback mode with parallel page processing via ThreadPoolExecutor
   - Configurable worker threads (default: min(4, CPU count))
   - Abort capability with event-based signaling
   - Supports PDF, Markdown, TXT, and Excel formats

4. **OCR Engine** (`agent_ocr_engine.py`):
   - Entry point: `process_document_systematically()` for full pipeline
   - Manages the OCR extraction process through agent orchestration
   - Implements caching for optimization
   - Handles parallel vision API calls when enabled
   - Coordinates between vision, corruption, formatting, and checker agents
   - Returns structured results with content, evaluation, and metadata

### API Architecture

- **Unified Client** (`unified_client.py`):
  - Single interface for OpenAI and Anthropic APIs
  - `UnifiedResponse` standardizes responses across providers
  - Vision support detection for different models
- **API Client** (`api_client.py`):
  - Handles API communication with automatic retry logic
  - Uses `unified_client` under the hood
  - Implements exponential backoff for rate limiting
  - Tracks token usage and response truncation
- **Config** (`config.py`):
  - Task-specific configuration with helper methods (see Model Configuration section)
  - Legacy properties maintained for backward compatibility

### UI System (`ui.py`)

- Gradio-based interface (`create_ui()`) with tabs for:
  - **Formatted Content**: Final markdown output from content formatting agent
  - **Raw OCR**: Unformatted vision OCR extraction results
  - **Evaluation**: Quality assessment report from checker agent
  - **Logs**: Real-time processing logs with color-coded status messages
- Features:
  - Progress tracking with real-time log updates
  - Abort button with event-based cancellation
  - Download functionality for processed markdown files
  - Page range selection support (e.g., "1-5, 10, 15-20")

### REST API (`api/main.py`)

- FastAPI-based REST API with auto-generated Swagger documentation
- Swagger UI available at `/docs`, ReDoc at `/redoc`
- Note: Most endpoints are currently stubs (501 Not Implemented) - check implementation status in `api/main.py`

## Model Configuration

Model settings for each task are defined in [config.py](config.py). Use the helper methods to get task-specific settings:
- `config.get_model_for_task(task)` - Returns model name
- `config.get_provider_for_task(task)` - Returns "openai" or "anthropic"
- `config.get_temperature_for_task(task)` - Returns temperature
- `config.get_max_tokens_for_task(task)` - Returns max tokens

Valid task names: `"main"`, `"vision"`, `"evaluation"`, `"corruption"`, `"anthropic_evaluation"`

Check [config.py](config.py) for current model assignments - they are updated there as source of truth.

## Prompt Management

Prompts are stored in [prompts/](prompts/) directory as separate text files:
- Loaded dynamically via `PromptLoader` class in [prompts/prompt_loader.py](prompts/prompt_loader.py)
- Cached for performance with `_cache` dictionary
- Methods: `get(prompt_name)`, `list_available_prompts()`, `reload_all()`, `preload_all()`
- Easily editable without code changes - just modify `.txt` files
- Current prompts: `vision_ocr.txt`, `content_formatting.txt`

## Key Processing Features

1. **Parallel Processing**: Configurable worker threads for concurrent page processing
2. **Corruption Detection**: Systematic identification and handling of corrupted text
3. **Vision-First Approach**: Prioritizes vision OCR over traditional text extraction
4. **Caching System**: OCR results cached in `.ocr_cache/` directory to minimize API calls
5. **Abort Capability**: Processing can be interrupted via UI
6. **Multiple Output Formats**: PDF, Markdown, raw text
7. **Dual Evaluation**: OpenAI and Anthropic evaluators for quality comparison (in `evaluation/` directory)

## Important Patterns

### Agent Development
- All agents inherit from `BaseAgent` ([agent_base.py](agent_base.py)) and must implement:
  - `process(input_data, context)`: Main processing logic, returns `AgentResponse`
  - `get_system_prompt()`: Returns system prompt string for the agent
- Use `self.make_api_call(messages, task="task_name")` for API calls (handles retries)
- Use `self.logger` for all logging (not print statements)
- Return `AgentResponse` with: `success`, `content`, `confidence`, `metadata`, `reasoning_steps`

### API Integration
- All API calls go through `APIClient.make_api_call()` with automatic retry logic
- API client handles exponential backoff and tracks token usage
- Check `api_client.last_response_truncated` to detect truncation

### Data Flow
- Processing results use `ProcessingResult` dataclass with standardized fields
- Agent responses use `AgentResponse` dataclass for consistency
- Logging handled through `ProcessingLogger` with methods:
  - `log_step()`: Regular processing steps
  - `log_success()`: Successful completions
  - `log_error()`: Error messages
  - `log_warning()`: Warning messages

### Thread Safety
- Vision call counting uses `threading.Lock` (`_vision_calls_lock`)
- Token tracking uses separate lock (`_tokens_lock`)
- Each parallel worker opens its own document instance (PyMuPDF thread safety)

## Testing

The project uses pytest for testing with the following structure:
- Test files located in `tests/` directory
- Markers for test categorization:
  - `@pytest.mark.unit`: Unit tests
  - `@pytest.mark.integration`: Integration tests
  - `@pytest.mark.slow`: Slow-running tests
  - `@pytest.mark.api`: Tests that hit external APIs
- Configuration in [pytest.ini](pytest.ini)
- Fixtures defined in [tests/conftest.py](tests/conftest.py)
- Use `pytest -m "not api"` to skip external API tests during development

## Deployment

### HuggingFace Spaces
The application is deployed to HuggingFace Spaces:
```bash
./push_to_huggingface.sh        # Interactive script to push updates
./update_huggingface.sh         # Alternative update script
```
- Deployment target: `https://huggingface.co/spaces/jimbrodonovan/DI-agent-2`
- Uses Gradio SDK (configured in [README.md](README.md))
- Rebuild time: 1-2 minutes after push

### Utility Scripts
- `convert_to_pdf.py`: Convert markdown/text to PDF format
- `vision_recommendation_agent.py`: Analyze documents and recommend vision OCR usage per page

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an advanced OCR (Optical Character Recognition) processing application that extracts text from PDF documents using an intelligent agent-based system. The application employs multiple specialized AI agents for different content types, with support for complex tables (including nested headers), forms, and various document formats. It uses OpenAI Vision API and Anthropic Claude for dual evaluation, with Tesseract OCR as a fallback method.

## Common Development Commands

### Running the Application

```bash
# Main entry point (Gradio UI)
python app.py
```

### Installing Dependencies

**Two dependency files serve different purposes:**

- `requirements.txt` - Python packages installed via pip
- `packages.txt` - System packages for Hugging Face Spaces deployment (apt-get)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies for local development
# macOS: 
brew install tesseract

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-eng libgl1 libglib2.0-0

# Windows: 
# Download from https://github.com/UB-Mannheim/tesseract/wiki

# Note: packages.txt is automatically used by Hugging Face Spaces
# No manual installation needed for deployment
```

### Environment Setup

```bash
# Create .env file with required API keys
cat > .env << EOF
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional - for dual evaluation
EOF
```

**Note**: OpenAI API key is optional but recommended for vision OCR. Anthropic API key is optional and only needed for comparative evaluation.

## Architecture & Key Components

### Core Processing Pipeline

1. **Entry Points**
   - `app.py`: Primary entry point with environment validation
   - `ui.py`: Gradio interface creation and configuration

2. **Agent-Based OCR Engine** (`agent_ocr_engine.py`)
   - `AgentBasedOCREngine`: Main class using intelligent agents for text extraction
   - Agent pipeline methods:
     - `extract_with_vision_agent()`: Vision OCR Agent with specialized strategies
     - `format_content_with_agent()`: Content Formatting Agent for cleanup
     - `extract_page_text_with_agents()`: Complete agent pipeline orchestration
   - Intelligent fallback to Tesseract when agents are unavailable

3. **Document Processing** (`processor_optimized.py`)
   - `OptimizedDocumentProcessor`: Manages the complete OCR pipeline with parallel processing
   - Handles page range selection
   - Saves output as timestamped Markdown files

4. **Configuration** (`config.py`)
   - OpenAI API key is optional (Tesseract fallback if not provided)
   - Anthropic API key is optional (for dual evaluation comparison)
   - Enhanced vision prompt with complex table handling instructions
   - Key settings: `vision_corruption_threshold`, `max_vision_calls_per_doc`, `dpi`
   - Dual evaluation settings: `compare_evaluation_methods`, `anthropic_model`

5. **Agent Components**
   - `agent_base.py`: Foundation classes (BaseAgent, AgentOrchestrator, AgentState)
   - `vision_ocr_agent.py`: Specialized Vision OCR Agent with enhanced table extraction
     - Standard extraction
     - Table-focused extraction (with nested header support)
     - Form-focused extraction
     - Technical document extraction
   - `content_formatting_agent.py`: Content Formatting Agent with document type detection
   - `corruption_agent.py`: Analyzes text quality and determines extraction strategy
   - `checker_agent.py`: Dual evaluation system comparing OpenAI and Anthropic assessments
   - `summary_agent.py`: Generates summaries using GPT-4
   
6. **Supporting Components**
   - `corruption_detector.py`: Enhanced detection for complex tables and nested headers
   - `summary_generator.py`: Document summarization functionality
   - `logger.py`: Processing logs and metrics
   - `utils.py`: Page range parsing and validation utilities

### Agent-Based OCR Decision Flow

1. **Initial Extraction**: Extract PDF text using PyMuPDF
2. **Corruption Detection**: Analyze text quality using `CorruptionDetector`
   - Detects nested table headers, complex tables, encoding issues
   - Calculates corruption score based on multiple factors
3. **Strategy Selection**:
   - Clean text → Format with Content Formatting Agent
   - Tables detected → Use Vision OCR Agent with table-focused strategy
   - Forms detected → Use Vision OCR Agent with form-focused strategy
   - Corrupted text → Use Vision OCR Agent with appropriate strategy
4. **Fallback Logic**: If vision agent fails OR disabled → Tesseract OCR
5. **Content Formatting**: All text processed by Content Formatting Agent
6. **Quality Evaluation**: 
   - Dual evaluation using OpenAI GPT-4o and Anthropic Claude Opus 4-1 (claude-opus-4-1-20250805)
   - Enhanced table structure validation for multi-column data completeness
   - Streaming support for long Anthropic evaluation requests
   - Image compression for Anthropic API to reduce token usage
   - Side-by-side comparison in UI
   - Detailed missing/added items analysis with strict content completeness scoring
7. **Output**: Save as timestamped Markdown with evaluation report

## Key Features

### Intelligent Agent System
- **Vision OCR Agent**: Multiple extraction strategies for different content types
- **Content Formatting Agent**: Advanced document structure analysis and formatting
- **Corruption Detection Agent**: Identifies text quality issues and table patterns
- **Checker Agent**: Dual evaluation system for quality assessment
- **Agent Orchestrator**: Coordinates multi-agent workflows with state management

### Enhanced Table Support
- **Nested Header Detection**: Automatically identifies complex table structures
- **Multi-level Headers**: Preserves hierarchical relationships in tables
- **Column Spanning**: Handles merged cells and spanning headers
- **Agnostic Prompts**: Model-independent instructions for any AI provider

### Dual Evaluation System
- **Side-by-side Comparison**: OpenAI GPT-4V vs Anthropic Claude evaluations
- **Detailed Analysis**: Missing and added items tracking
- **Score Comparison**: Numerical scoring with recommendations (ACCEPT/REVIEW/REJECT)
- **Agreement Level**: Measures consensus between evaluators

### UI Enhancements
- **Gradio Interface**: Clean, modern web UI
- **Processing Animation**: Visual feedback during OCR processing
- **Quality Report Tab**: Side-by-side evaluation comparison
- **Summary Tab**: Document summaries with statistics
- **Download Options**: Export as Markdown or PDF

### Recent Updates
- **PostgreSQL Removed**: Simplified architecture without database dependencies
- **Enhanced Table Prompts**: Improved handling of complex nested tables
- **Evaluation Parsing Fix**: Corrected score extraction from evaluation reports
- **Clear Function Fix**: Proper reset of all UI components

## Testing Agent-Based OCR Functionality

```python
# Quick test of agent-based OCR engine
from logger import ProcessingLogger
from agent_ocr_engine import AgentBasedOCREngine

logger = ProcessingLogger()
engine = AgentBasedOCREngine(logger)
print('Vision enabled:', engine.vision_enabled)
print('Registered agents:', len(engine.orchestrator.agents))
print('Agent stats:', engine.get_agent_stats())
```

## Important Notes

### Deployment
- Supports both local development and Hugging Face Spaces deployment
- Gradio web UI accessible at `http://localhost:7860` when run locally
- Auto-detects Spaces environment for proper configuration

### Usage Tips
- **Page Ranges**: Specify as "1-5, 10, 15-20" for selective processing
- **Output Location**: Files saved to system temp directory with timestamps
- **Caching**: Vision OCR results cached to avoid duplicate API calls
- **API Keys**: OpenAI key enables vision OCR; Anthropic key enables dual evaluation

### Performance Considerations
- **Parallel Processing**: Multiple pages processed concurrently
- **Smart Fallback**: Automatic fallback to Tesseract when vision OCR unavailable
- **Corruption Detection**: Automatic strategy selection based on content analysis
- **Token Optimization**: Efficient prompt design to minimize API costs

### File Support
- **PDFs**: Primary format with full support
- **Markdown**: Direct processing with formatting agent
- **Text Files**: Plain text extraction and formatting
- **Images**: Individual page processing (PNG, JPG, etc.)

### Known Limitations
- Files API doesn't support PDF vision analysis (only individual images)
- Large documents may hit API token limits
- Complex nested tables may require manual verification
- Some formatting may be lost in heavily corrupted documents
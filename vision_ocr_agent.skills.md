# Vision OCR Agent Skills

## Overview
The VisionOCRAgent is a specialized AI agent that extracts text from images using GPT-4 Vision API. It provides multiple extraction strategies optimized for different document types and implements intelligent caching and parallel processing.

## Core Capabilities

### 1. Multi-Strategy Text Extraction
Extract text from images using document-type-specific strategies:

- **Standard Extraction**: General-purpose text extraction for regular documents
- **Table-Focused**: Enhanced extraction for table-heavy documents with nested headers
- **Form-Focused**: Specialized for forms with checkboxes (`[x]` for checked, `[ ]` for unchecked)
- **Technical Document**: Optimized for technical docs with diagrams, formulas, and symbols

### 2. Intelligent Image Optimization
- Automatic image resizing (max 2048px dimension) using high-quality LANCZOS resampling
- RGB conversion for compatibility
- JPEG compression (85% quality) for optimal API transfer
- Preserves quality while minimizing payload size

### 3. Caching System
- SHA256-based content hashing for deduplication
- 24-hour cache validity period
- Thread-safe cache access with locking
- Automatic cache invalidation
- Cache stored in `.ocr_cache/` directory

### 4. Parallel Processing
- Thread pool executor (3 workers default)
- Process multiple pages concurrently
- Maintains page order in results
- 2-minute timeout per page
- Graceful error handling per page

### 5. Confidence Scoring
Calculates extraction confidence based on:
- Text length (penalizes very short extracts)
- Image resolution (rewards high-quality images)
- Retry attempts (reduces confidence on retries)
- Strategy-specific indicators (e.g., presence of table/form markers)

### 6. AI Metadata Cleaning
Removes common AI commentary patterns:
- "I'm unable to...", "I cannot..."
- "Here is...", "The following..."
- "Based on...", "As requested..."
- Cleans excessive whitespace and empty lines

## Usage Examples

### Basic Single Image Extraction

```python
from vision_ocr_agent import VisionOCRAgent
from logger import ProcessingLogger
from PIL import Image

# Initialize agent
logger = ProcessingLogger()
agent = VisionOCRAgent(logger)

# Load image
image = Image.open("document.jpg")

# Extract text
result = agent.process(
    input_data={
        "image": image,
        "page_number": 1
    },
    context={"strategy": "standard"}
)

if result.success:
    print(f"Extracted text: {result.content}")
    print(f"Confidence: {result.confidence}")
    print(f"Tokens used: {result.tokens_used}")
```

### Table Extraction

```python
# For documents with complex tables
result = agent.process(
    input_data={
        "image": table_image,
        "page_number": 1
    },
    context={
        "strategy": "table_focused",
        "has_tables": True
    }
)
```

### Form Extraction

```python
# For forms with checkboxes
result = agent.process(
    input_data={
        "image": form_image,
        "page_number": 1
    },
    context={
        "strategy": "form_focused",
        "has_forms": True
    }
)

# Output will include [x] and [ ] for checkbox states
```

### Parallel Multi-Page Processing

```python
# Process multiple pages concurrently
pages = [
    {"image": Image.open(f"page_{i}.jpg"), "page_number": i}
    for i in range(1, 11)
]

results = agent.process_pages_parallel(
    pages=pages,
    context={"strategy": "standard"}
)

for i, result in enumerate(results, 1):
    print(f"Page {i}: {len(result.content)} characters extracted")
```

### Technical Document Extraction

```python
# For documents with formulas and diagrams
result = agent.process(
    input_data={
        "image": technical_doc,
        "page_number": 1
    },
    context={"strategy": "technical_doc"}
)
```

### Using Cache for Repeated Extractions

```python
# First call - hits API
result1 = agent.process({"image": image, "page_number": 1})

# Second call with same image - uses cache (much faster!)
result2 = agent.process({"image": image, "page_number": 1})
```

## Input Schema

### `process()` Method

**input_data** (required):
- `image` (PIL.Image.Image): The image to extract text from
- `page_number` (int, optional): Page number for tracking (default: 1)

**context** (optional):
- `strategy` (str): Extraction strategy - "standard", "table_focused", "form_focused", or "technical_doc"
- `has_tables` (bool): Hint for table content (enhances prompt)
- `has_forms` (bool): Hint for form content (enhances prompt)
- `quality_issues` (bool): Image has quality issues (marks unclear text with [?])
- `retry_count` (int): Number of retry attempts (affects confidence)

## Output Schema

Returns `AgentResponse` dataclass with:

```python
@dataclass
class AgentResponse:
    success: bool              # Whether extraction succeeded
    content: str              # Extracted text (cleaned of AI metadata)
    confidence: float         # Confidence score (0.0-1.0)
    metadata: dict           # Additional info:
                            #   - page_number
                            #   - extraction_strategy
                            #   - image_dimensions
                            #   - estimated_word_count
    reasoning_steps: list    # Processing steps taken
    tokens_used: int         # API tokens consumed
    processing_time: float   # Time in seconds
    error_message: str       # Error details (if failed)
```

## Best Practices

### 1. Choose the Right Strategy
- Use **table_focused** for financial statements, spreadsheets, or any tabular data
- Use **form_focused** for application forms, surveys, or checkbox-heavy documents
- Use **technical_doc** for scientific papers, engineering docs, or math-heavy content
- Use **standard** for general text documents

### 2. Optimize for Performance
- Process multiple pages in parallel using `process_pages_parallel()`
- Cache will automatically speed up repeated processing of the same image
- Larger images are automatically optimized to 2048px max dimension

### 3. Monitor Confidence Scores
- Confidence < 0.5: Review extraction manually
- Confidence 0.5-0.8: Generally reliable, spot-check recommended
- Confidence > 0.8: High quality extraction

### 4. Handle Low-Quality Images
- Set `quality_issues: True` in context to mark unclear text with `[?]`
- Consider preprocessing (contrast enhancement, deskewing) before OCR
- Lower resolution images will have reduced confidence scores

### 5. Manage Cache
- Cache is stored in `.ocr_cache/` directory
- Cache entries expire after 24 hours
- Delete cache directory to force fresh extractions
- Cache keys are content-based (SHA256) - same image always uses same cache

## Integration Points

### With Other Agents
VisionOCRAgent is typically the first agent in the pipeline:

```
VisionOCRAgent → CorruptionAgent → ContentFormattingAgent → CheckerAgent
```

### With BaseAgent Architecture
Inherits from `BaseAgent` ([agent_base.py](agent_base.py:42-201)):
- State management and memory tracking
- Standardized `AgentResponse` format
- Built-in retry logic via `retry_with_fallback()`
- API client with automatic retries

### With API Client
Uses `APIClient.make_api_call()` internally:
- Automatic exponential backoff on rate limits
- Token usage tracking
- Response truncation detection

## Configuration

Uses task-based configuration from [config.py](config.py):

```python
task = "vision"
model = config.get_model_for_task("vision")        # "gpt-4o"
provider = config.get_provider_for_task("vision")  # "openai"
temperature = config.get_temperature_for_task("vision")  # 0.0
max_tokens = config.get_max_tokens_for_task("vision")    # 4096
```

## Prompts

System prompt loaded from [prompts/vision_ocr.txt](prompts/vision_ocr.txt):
- Extracts text exactly as it appears
- Preserves layout, structure, and formatting
- Handles nested table headers intelligently
- Replaces unclear characters with `�`
- No summarization or interpretation

## Error Handling

### Graceful Degradation
- Returns `success: False` with empty content on failure
- Captures error message in `error_message` field
- Logs errors via `ProcessingLogger`
- Cache failures don't block processing (falls back to API)

### Retry Logic
Inherited from `BaseAgent`:
```python
response = agent.retry_with_fallback(
    input_data={"image": image, "page_number": 1},
    context={"strategy": "standard"},
    max_retries=2
)
```

## Performance Characteristics

- **Latency**: ~2-5 seconds per page (GPT-4 Vision API)
- **Throughput**: ~10-15 pages/minute with parallel processing
- **Cache hit**: ~10ms (instant return)
- **Memory**: Minimal - images optimized before encoding
- **Thread safety**: Cache operations are locked, parallel processing is safe

## Limitations

1. **API-Dependent**: Requires OpenAI API access and credits
2. **Image Size**: Very large images (>2048px) are automatically downsampled
3. **Cache Storage**: Large documents will accumulate cache files
4. **Language Support**: Limited by GPT-4 Vision's language capabilities
5. **Handwriting**: Performance varies on handwritten text quality

## Related Files

- [agent_base.py](agent_base.py) - Base agent architecture
- [api_client.py](api_client.py) - API communication layer
- [unified_client.py](unified_client.py) - Multi-provider API interface
- [config.py](config.py) - Configuration management
- [prompts/vision_ocr.txt](prompts/vision_ocr.txt) - System prompt
- [utils.py](utils.py) - Image encoding utilities

# Corruption Agent Skills

## Overview
The CorruptionAgent is an intelligent routing agent that analyzes document pages to determine the optimal OCR processing method. It combines text pattern analysis with optional vision-based analysis to route pages to the most appropriate extraction method: Vision OCR, Tesseract, or PDF text extraction.

## Core Capabilities

### 1. Intelligent OCR Method Routing
Routes pages to the optimal processing method:

- **VISION_OCR**: For pages with tables, charts, forms, complex layouts, or poor text quality
- **TESSERACT**: For clean text with simple layouts and good extraction quality
- **PDF_TEXT**: For pages where text was successfully extracted from PDF

### 2. Hybrid Analysis System

#### Text Pattern Analysis
Analyzes extracted PDF text for:
- **Table Detection**: Box-drawing characters, aligned columns, multi-space patterns
- **Checkbox Detection**: `[x]`, `[ ]`, ☐, ☑, ✓ symbols
- **Structured Data**: Label-value patterns (e.g., "Name: John")
- **Text Quality**: Word fragmentation, average word length, spacing issues
- **Encoding Issues**: Unusual characters suggesting corruption

#### Visual Analysis (Optional)
Uses vision model to detect:
- Tables, charts, graphs, diagrams
- Forms, checkboxes, radio buttons
- Layout complexity (simple/moderate/complex)
- Image quality assessment
- Text readability from image

### 3. Quality Scoring
Calculates corruption score based on:
- Fragmented words (>10% single-character words)
- Short average word length (<2.5 characters)
- Excessive spacing (>50% space ratio)
- Character encoding issues (>1% weird characters)

### 4. Vision Budget Management
- Respects `max_vision_calls_per_doc` limit from config
- Routes to Tesseract when vision budget exhausted
- Tracks vision calls across document processing

### 5. Deterministic JSON Output
Returns structured decision data:
```json
{
    "recommended_method": "VISION_OCR|TESSERACT|PDF_TEXT",
    "confidence": 0.85,
    "reasoning": "Tables detected in image, complex layout",
    "detected_elements": ["table", "complex_layout"],
    "visual_complexity": "high"
}
```

## Usage Examples

### Basic Text-Only Analysis

```python
from corruption_agent import CorruptionAgent
from logger import ProcessingLogger

# Initialize agent
logger = ProcessingLogger()
agent = CorruptionAgent(logger)

# Analyze extracted PDF text
pdf_text = "Some extracted text from PDF..."

result = agent.process(
    input_data={"text": pdf_text},
    context={"page_number": 1, "vision_calls_used": 0}
)

if result.success:
    recommendation = result.content
    print(f"Method: {recommendation['recommended_method']}")
    print(f"Confidence: {recommendation['confidence']}")
    print(f"Reasoning: {recommendation['reasoning']}")
    print(f"Elements: {recommendation['detected_elements']}")
```

### Hybrid Analysis with Image

```python
from PIL import Image

# Analyze both text and image
pdf_text = "Extracted text..."
page_image = Image.open("page_1.jpg")

result = agent.process(
    input_data={
        "text": pdf_text,
        "image": page_image
    },
    context={
        "page_number": 1,
        "vision_calls_used": 2
    }
)

recommendation = result.content
# Will use visual analysis if available
```

### Using Compatibility Method

```python
# Legacy interface for existing code
should_use_vision, reason = agent.should_use_vision(
    text=pdf_text,
    page_image=page_image,
    vision_calls_used=5,
    page_number=1
)

if should_use_vision:
    print(f"Use vision OCR: {reason}")
else:
    print(f"Use Tesseract: {reason}")
```

### Table Detection Example

```python
# Text with table patterns
table_text = """
Item        | Price | Quantity
------------|-------|----------
Widget A    | $10   | 5
Widget B    | $15   | 3
"""

result = agent.process(
    input_data={"text": table_text},
    context={"page_number": 1}
)

# Will detect table patterns and recommend VISION_OCR
assert result.content["recommended_method"] == "vision_ocr"
assert "table" in result.content["detected_elements"]
```

### Checkbox Detection Example

```python
# Text with checkboxes
form_text = """
Please select:
[x] Option A
[ ] Option B
[x] Option C
"""

result = agent.process(
    input_data={"text": form_text},
    context={"page_number": 1}
)

# Will detect checkboxes and recommend VISION_OCR
assert "checkbox" in result.content["detected_elements"]
```

### Vision Budget Limit Example

```python
# Vision calls exhausted
result = agent.process(
    input_data={"text": "Some text..."},
    context={
        "page_number": 15,
        "vision_calls_used": 10  # Assuming max is 10
    }
)

# Will route to Tesseract due to budget
assert result.content["recommended_method"] == "tesseract"
assert "vision_limit_reached" in result.content["detected_elements"]
```

### Poor Quality Text Example

```python
# Corrupted/fragmented text
poor_text = "T h i s i s f r a g m e n t e d t e x t w i t h m a n y s p a c e s"

result = agent.process(
    input_data={"text": poor_text},
    context={"page_number": 1}
)

# Will detect poor quality and recommend VISION_OCR
assert "poor_text" in result.content["detected_elements"]
```

## Input Schema

### `process()` Method

**input_data** (required):
- `text` (str): Extracted text from PDF (can be empty string)
- `image` (PIL.Image.Image, optional): Page image for visual analysis

**context** (optional):
- `page_number` (int): Current page number for logging
- `vision_calls_used` (int): Number of vision calls already made
- Any additional metadata for analysis

### `should_use_vision()` Compatibility Method

**Parameters**:
- `text` (str): Extracted PDF text
- `page_image` (PIL.Image.Image, optional): Page image
- `vision_calls_used` (int): Vision call count
- `page_number` (int): Page number

**Returns**: `(bool, str)` - (should_use_vision, reasoning)

## Output Schema

### AgentResponse

Returns `AgentResponse` dataclass with:

```python
@dataclass
class AgentResponse:
    success: bool              # Always True unless exception
    content: dict              # Recommendation dictionary (see below)
    confidence: float          # 0.0-1.0 confidence in decision
    metadata: dict            # Analysis details:
                             #   - page_number
                             #   - text_analysis (quality metrics)
                             #   - visual_analysis (if image provided)
                             #   - processing_method
    reasoning_steps: list     # Analysis steps performed
    tokens_used: int         # API tokens (if visual analysis used)
    processing_time: float   # Seconds
    error_message: str       # Error details (if failed)
```

### Recommendation Dictionary (in `content` field)

```python
{
    "recommended_method": str,      # "vision_ocr", "tesseract", or "pdf_text"
    "confidence": float,            # 0.0-1.0
    "reasoning": str,               # Human-readable explanation
    "detected_elements": list,      # ["table", "checkbox", "poor_text", etc.]
    "visual_complexity": str        # "low", "medium", "high", or "unknown"
}
```

### Text Analysis Dictionary (in `metadata.text_analysis`)

```python
{
    "text_quality": str,            # "good", "fair", "poor", or "missing"
    "has_tables": bool,             # Table patterns detected
    "has_checkboxes": bool,         # Checkbox patterns detected
    "has_structured_data": bool,    # Label:value patterns detected
    "corruption_indicators": list,  # List of detected issues
    "quality_score": float          # 0.0-1.0 quality score
}
```

### Visual Analysis Dictionary (in `metadata.visual_analysis`)

```python
{
    "visual_analysis_available": bool,
    "has_tables": bool,
    "has_charts": bool,
    "has_forms": bool,
    "layout_complexity": str,       # "simple", "moderate", "complex"
    "image_quality": str,           # "poor", "fair", "good", "excellent"
    "visual_elements": list,        # Detected elements
    "text_readability": str,        # "poor", "fair", "good", "excellent"
    "tokens_used": int              # Vision API tokens used
}
```

## Decision Logic

### Priority Order

1. **Vision Budget Check**: If `vision_calls_used >= max_vision_calls_per_doc` → Route to TESSERACT
2. **Visual Elements**: If tables, charts, or forms detected → Route to VISION_OCR
3. **Text Quality Issues**: If quality score < 0.7 or text missing → Route to VISION_OCR
4. **Clean Text**: If quality is good and no visual elements → Route to TESSERACT
5. **Fallback**: Conservative routing to TESSERACT

### Detected Elements

| Element | Trigger | Recommendation |
|---------|---------|----------------|
| `table` | Visual table detection | VISION_OCR |
| `table_text` | Text patterns: `\|`, `─`, aligned columns | VISION_OCR |
| `chart` | Visual chart/graph detection | VISION_OCR |
| `forms`, `checkbox` | Checkbox symbols: `[x]`, ☐, ☑ | VISION_OCR |
| `complex_layout` | Moderate/complex visual layout | VISION_OCR |
| `poor_text` | Quality score < 0.7 | VISION_OCR |
| `poor_image_quality` | Visual quality assessment | VISION_OCR (lower confidence) |
| `fragmented_words` | >10% single-char words | VISION_OCR |
| `spacing_corruption` | Excessive spacing ratio | VISION_OCR |
| `encoding_issues` | Unusual characters >1% | VISION_OCR |
| `clean_text` | Good quality, no issues | TESSERACT |
| `vision_limit_reached` | Budget exhausted | TESSERACT |

## Best Practices

### 1. Provide Both Text and Image
- Text analysis is fast but limited
- Visual analysis is slower but more accurate
- Combining both gives best routing decisions

### 2. Track Vision Budget
Always pass `vision_calls_used` in context:
```python
context = {
    "vision_calls_used": current_count,
    "page_number": page_num
}
```

### 3. Handle Fallback Cases
Agent returns conservative fallback on errors:
```python
if not result.success:
    # Falls back to Tesseract with 0.3 confidence
    print(f"Fallback: {result.content['reasoning']}")
```

### 4. Interpret Confidence Scores
- **Confidence > 0.8**: High confidence in decision
- **Confidence 0.6-0.8**: Moderate confidence
- **Confidence < 0.6**: Low confidence, consider manual review

### 5. Use Detected Elements
Check `detected_elements` to understand why a method was chosen:
```python
elements = result.content["detected_elements"]
if "table" in elements:
    # Expect structured data output
    pass
```

### 6. Monitor Visual Analysis Availability
Visual analysis requires:
- Image provided in `input_data`
- API client configured for vision
- Vision API available (OpenAI GPT-4 Vision)

```python
if result.metadata.get("visual_analysis", {}).get("visual_analysis_available"):
    # Visual analysis was performed
    pass
```

## Integration Points

### With Pipeline
Typically used early in pipeline to route pages:

```
CorruptionAgent (routing) → VisionOCRAgent OR Tesseract → ContentFormattingAgent
```

### With Config
Uses configuration from [config.py](config.py):
- `max_vision_calls_per_doc`: Budget limit (default: 10)
- Task "corruption" for visual analysis API calls

### With BaseAgent
Inherits from `BaseAgent` ([agent_base.py](agent_base.py:42-201)):
- State management and memory
- `make_api_call()` for vision analysis
- Standardized `AgentResponse` format

## Configuration

### Task-Based Config
```python
task = "corruption"
model = config.get_model_for_task("corruption")  # "claude-sonnet-4-20250514"
temperature = 0.0  # Deterministic JSON output
max_tokens = 500   # Limited for JSON response
```

### Vision Budget
```python
from config import config

max_calls = config.max_vision_calls_per_doc  # Default: 10
```

## Performance Characteristics

- **Text-only analysis**: ~10ms (regex patterns)
- **With visual analysis**: ~2-3 seconds (vision API call)
- **Fallback**: Instant (returns conservative default)
- **Memory**: Minimal (no caching, stateless)
- **Thread safety**: Safe for concurrent calls

## Error Handling

### Graceful Degradation
1. **Visual analysis fails**: Falls back to text-only analysis
2. **JSON parsing fails**: Uses fallback pattern matching on response
3. **Complete failure**: Returns Tesseract routing with 0.3 confidence
4. **Vision budget exceeded**: Routes to Tesseract with clear reasoning

### Error Recovery
```python
try:
    result = agent.process(input_data, context)
    if result.success:
        # Use recommendation
        method = result.content["recommended_method"]
    else:
        # Fallback routing included in result.content
        method = result.content["recommended_method"]  # Will be "tesseract"
except Exception as e:
    # Use compatibility method for extra safety
    should_use_vision, reason = agent.should_use_vision(text)
```

## Text Pattern Recognition

### Table Indicators
- Box-drawing characters: `|`, `─`, `┌`, `┐`, `└`, `┘`, `├`, `┤`, `┬`, `┴`, `┼`
- Multi-space alignment: `\w\s{4,}\w` (4+ spaces between words)
- Detection threshold: 3+ aligned columns

### Checkbox Patterns
- Bracket notation: `[x]`, `[ ]`, `[✓]`
- Unicode symbols: `☐`, `☑`, `✓`, `✔`
- Selection markers: `x (a)`, `¨ (b)`
- Case-insensitive matching

### Structured Data
- Label-value pairs: `Label: $100`, `Name: John`
- Regex: `^\s*[A-Z][^:]*:\s*\$?\d`
- Multiline matching

## Limitations

1. **Visual Analysis Dependency**: Optional vision analysis requires image and API access
2. **Language Support**: Text patterns optimized for English documents
3. **Binary Decision**: Routes to one method, no hybrid processing
4. **Vision Budget**: Hard limit prevents optimal routing after budget exhausted
5. **JSON Parsing**: Vision API responses may need cleanup/repair
6. **No Learning**: Doesn't adapt based on routing success/failure

## Related Files

- [agent_base.py](agent_base.py) - Base agent architecture
- [config.py](config.py) - Configuration and vision budget
- [vision_ocr_agent.py](vision_ocr_agent.py) - Vision OCR implementation
- [api_client.py](api_client.py) - API communication layer
- [processor_optimized.py](processor_optimized.py) - Pipeline orchestration

## Advanced Usage

### Custom Vision Budget Per Document
```python
# Override config for specific document
custom_context = {
    "page_number": 1,
    "vision_calls_used": 0,
    "custom_vision_limit": 20  # Note: Not currently supported, use config
}

# To actually override, modify config before processing
from config import config
config.max_vision_calls_per_doc = 20
```

### Batch Analysis
```python
# Analyze multiple pages
pages = [
    {"text": page1_text, "image": page1_img},
    {"text": page2_text, "image": page2_img},
    {"text": page3_text, "image": page3_img},
]

recommendations = []
vision_count = 0

for i, page_data in enumerate(pages, 1):
    result = agent.process(
        input_data=page_data,
        context={
            "page_number": i,
            "vision_calls_used": vision_count
        }
    )
    recommendations.append(result.content)

    # Track vision usage
    if result.metadata.get("visual_analysis", {}).get("visual_analysis_available"):
        vision_count += 1

# Analyze routing distribution
vision_pages = sum(1 for r in recommendations if r["recommended_method"] == "vision_ocr")
print(f"{vision_pages}/{len(pages)} pages routed to vision OCR")
```

### Quality Assessment
```python
# Get detailed quality metrics
result = agent.process({"text": pdf_text}, {"page_number": 1})

text_analysis = result.metadata["text_analysis"]
print(f"Quality: {text_analysis['text_quality']}")
print(f"Quality score: {text_analysis['quality_score']:.2f}")
print(f"Issues: {text_analysis['corruption_indicators']}")

# Make informed decisions
if text_analysis["quality_score"] < 0.5:
    print("WARNING: Very poor text quality detected")
```

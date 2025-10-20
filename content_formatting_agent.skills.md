# Content Formatting Agent Skills

## Overview
The ContentFormattingAgent transforms raw OCR text into structured, formatted markdown optimized for vector database storage and semantic search. It uses AI-powered formatting with multiple strategies tailored to different document types, with special emphasis on flattening tables and standardizing form elements for chunked retrieval.

## Core Capabilities

### 1. Intelligent Content Analysis
Analyzes raw text to detect:
- **Tables**: Box-drawing characters, aligned columns, multi-space patterns
- **Checkboxes**: `[x]`, `[ ]`, ☐, ☑, ✓, and various checkbox symbols
- **Lists**: Bullet points and numbered lists
- **Technical Content**: LaTeX math, code, chemical formulas
- **Structure Complexity**: Section headers, estimated sections
- **Document Statistics**: Line count, word count, compression ratio

### 2. Multi-Strategy Formatting

Six specialized formatting strategies:

- **Standard**: General documents with simple structure
- **Table-Focused**: Documents with multiple tables requiring flattening
- **Form-Focused**: Forms with checkboxes and field elements (highest priority)
- **Technical**: Technical docs with formulas, code, notation
- **Comprehensive**: Complex docs with tables AND forms
- **Structure-Focused**: Documents with complex section hierarchy

### 3. Vector Database Optimization

**Critical Feature**: Tables are ALWAYS flattened to self-contained entries:

```
**[Column Label]** - **[Row Label]**: [Value]
```

This ensures each line remains meaningful when document is chunked for vector storage (e.g., Pinecone).

### 4. Checkbox Standardization

Converts all checkbox variations to standard format:
- **Checked**: `[SELECTED] **Field Label**: value`
- **Unchecked**: `**Field Label**: value`

Recognizes: `[x]`, `[X]`, `☑`, `✓`, `✔`, `(x)`, standalone `x/X`

### 5. Document-Wide Processing

Two processing modes:
- **Single-page**: Process individual text chunks
- **Multi-page**: Process entire documents with consistency enforcement
  - Automatic chunking for large docs (>30 pages or >150k chars)
  - Fallback page-by-page processing on errors
  - Cross-page formatting consistency

### 6. Markdown Table Cleanup

Automatically detects and converts pipe-style markdown tables to flattened format:
- Removes problematic `|---|---|` syntax
- Converts to searchable entries
- Preserves all table data

### 7. Footnote Conversion (Optional)

Converts footnotes to inline parenthetical format:
- Recognizes superscript numbers (⁰¹²³⁴⁵⁶⁷⁸⁹)
- Handles bracketed `[1]` and parenthetical `(1)` citations
- Three styles: inline, minimal, preserve

### 8. AI Metadata Cleaning

Removes common AI commentary:
- "I'm unable to...", "Here is...", "Based on..."
- Apologies and explanations
- Extra whitespace cleanup

## Usage Examples

### Basic Text Formatting

```python
from content_formatting_agent import ContentFormattingAgent
from logger import ProcessingLogger

# Initialize agent
logger = ProcessingLogger()
agent = ContentFormattingAgent(logger)

# Format raw OCR text
raw_text = """
Section 1
This is some text extracted from OCR.

Item     Price    Quantity
Widget   $10      5
Gadget   $15      3
"""

result = agent.process(raw_text)

if result.success:
    print(f"Formatted content:\n{result.content}")
    print(f"Strategy used: {result.metadata['formatting_strategy']}")
    print(f"Confidence: {result.confidence}")
```

### Table-Focused Formatting

```python
# Text with table
table_text = """
Financial Summary

Service            Cost    Coverage
Primary Care       $50     80%
Specialist Visit   $120    60%
Emergency Care     $500    90%
"""

result = agent.process(table_text)

# Output will be flattened:
# **Cost** - **Primary Care**: $50
# **Coverage** - **Primary Care**: 80%
# **Cost** - **Specialist Visit**: $120
# etc.
```

### Form-Focused Formatting

```python
# Text with checkboxes
form_text = """
Please select options:
[x] Email notifications
[ ] SMS notifications
☑ Newsletter subscription
☐ Marketing emails
"""

result = agent.process(form_text)

# Output will be standardized:
# [SELECTED] **Email notifications**
# **SMS notifications**
# [SELECTED] **Newsletter subscription**
# **Marketing emails**
```

### Complete Document Processing

```python
# Process multiple pages with consistency
pages = [
    "Page 1 text with tables...",
    "Page 2 text continuing from page 1...",
    "Page 3 text with forms..."
]

result = agent.process_entire_document(
    document_pages=pages,
    context={"convert_footnotes": True}
)

if result.success:
    print(f"Formatted {result.metadata['total_pages']} pages")
    print(f"Strategy: {result.metadata['formatting_strategy']}")
    print(f"Consistency score: {result.metadata['consistency_score']}")
```

### With Context Options

```python
# Custom formatting options
context = {
    "convert_footnotes": True,
    "footnote_style": "inline",  # or "minimal", "preserve"
    "max_footnote_length": 150,
    "preserve_references": False
}

result = agent.process(
    input_data=raw_text,
    context=context
)
```

### Error Handling

```python
# Handle minimal/problematic content
minimal_text = "https://example.com/document.pdf"

result = agent.process(minimal_text)

if not result.success:
    print(f"Error: {result.error_message}")
    # Output: "Document appears to be image-based with minimal
    #          extractable text... Please use Vision OCR instead."
```

### String or Dict Input

```python
# Agent accepts both string and dict input
result1 = agent.process("Simple string text")
result2 = agent.process({"text": "Dict with text key"})

# Both work identically
```

## Input Schema

### `process()` Method

**input_data** (required):
- `str`: Raw text to format
- `dict`: Dictionary with `"text"` key containing raw text

**context** (optional):
- `convert_footnotes` (bool): Convert footnotes to inline format (default: False)
- `footnote_style` (str): "inline", "minimal", or "preserve" (default: "inline")
- `max_footnote_length` (int): Max footnote text length (default: 200)
- `preserve_references` (bool): Keep citation markers in inline format (default: False)

### `process_entire_document()` Method

**document_pages** (required):
- `List[str]`: List of page texts to format with consistency

**context** (optional):
- Same as `process()` method

## Output Schema

Returns `AgentResponse` dataclass:

```python
@dataclass
class AgentResponse:
    success: bool              # Whether formatting succeeded
    content: str              # Formatted markdown text
    confidence: float         # 0.0-1.0 confidence score
    metadata: dict           # Formatting details (see below)
    reasoning_steps: list    # Processing steps taken
    tokens_used: int         # API tokens consumed
    processing_time: float   # Seconds
    error_message: str       # Error details (if failed)
```

### Metadata Dictionary

#### For `process()`:
```python
{
    "formatting_strategy": str,        # Strategy used
    "content_analysis": dict,          # Analysis results (see below)
    "original_length": int,            # Original text length
    "formatted_length": int,           # Formatted text length
    "compression_ratio": float         # formatted/original length
}
```

#### For `process_entire_document()`:
```python
{
    "total_pages": int,
    "formatting_strategy": str,
    "document_analysis": dict,
    "processing_mode": "complete_document",
    "consistency_score": float         # 0.0-1.0 consistency metric
}
```

### Content Analysis Dictionary

```python
{
    "has_tables": bool,
    "has_checkboxes": bool,
    "has_lists": bool,
    "has_technical_content": bool,
    "structure_complexity": str,       # "simple", "moderate", "complex"
    "estimated_sections": int,
    "line_count": int,
    "word_count": int
}
```

### Document Analysis Dictionary

```python
{
    "total_pages": int,
    "has_tables": bool,
    "has_forms": bool,
    "has_complex_structure": bool,
    "consistent_elements": list,       # ["tables_throughout", "form_elements"]
    "formatting_challenges": list,     # ["consistent_table_formatting", etc.]
    "section_structure": str          # "simple", "moderate", "complex"
}
```

## Strategy Selection Logic

### Priority Order (Highest to Lowest)

1. **Comprehensive** - Has both checkboxes AND tables
2. **Form-Focused** - Has checkboxes (priority over tables)
3. **Table-Focused** - Has tables only
4. **Technical** - Has technical content
5. **Structure-Focused** - Complex structure (>5 section headers)
6. **Standard** - Default for simple documents

### Document-Wide Strategies

1. **Comprehensive Document** - Tables + forms throughout
2. **Table-Heavy Document** - 30%+ pages have tables
3. **Form Document** - Has form elements
4. **Structured Document** - Complex section structure
5. **Standard Document** - Default

## Table Flattening Rules

### Why Tables are Flattened

When documents are chunked for vector databases (e.g., Pinecone), traditional table formats break:
- Headers get separated from data
- Context is lost in chunks
- Search/retrieval becomes useless

### Flattened Format

Original table:
```
Service          Participating    Non-Participating
Primary care     30% coinsurance  50% coinsurance
Specialist       30% coinsurance  50% coinsurance
```

Flattened output:
```
**Participating Provider** - **Primary care**: 30% coinsurance
**Non-Participating Provider** - **Primary care**: 50% coinsurance
**Participating Provider** - **Specialist**: 30% coinsurance
**Non-Participating Provider** - **Specialist**: 50% coinsurance
```

Each line is now:
- ✅ Self-contained with full context
- ✅ Searchable independently
- ✅ Meaningful when chunked
- ✅ Optimized for semantic similarity

### Table Detection Patterns

Tables are recognized by:
- Box-drawing characters: `|`, `─`, `┌`, `┐`, `└`, `┘`, `├`, `┤`, `┬`, `┴`, `┼`
- Aligned columns: 4+ spaces between words (`\w\s{4,}\w`)
- Multiple alignment patterns (>5 occurrences)

### Markdown Table Cleanup

Post-processing automatically converts any pipe-style markdown tables:

```markdown
| Header1 | Header2 |
|---------|---------|
| Value1  | Value2  |
```

To flattened format:
```
**Header2** - **Header1**: Value1
**Header2** - **Header1**: Value2
```

## Checkbox Formatting Rules

### Recognized Patterns

**Checked**:
- `[x]`, `[X]` (bracketed)
- `☑`, `✓`, `✔` (symbols)
- `(x)`, `(X)` (parenthetical)
- `x (a)`, `✓ (ii)` (with labels)
- Standalone `x`/`X` in checkbox context

**Unchecked**:
- `[ ]` (empty brackets)
- `☐` (empty checkbox)
- `( )` (empty parentheses)
- `¨ (a)` (unchecked marker with label)

### Output Format

**Checked**: `[SELECTED] **Field Label**: additional value`
**Unchecked**: `**Field Label**: additional value`

### Detection Scope

Agent scans **all text**, not just line beginnings, using regex patterns:
```python
checkbox_patterns = [
    r'\[[ x✓]\]',
    r'☐', r'☑',
    r'✓', r'✔',
    r'^\s*[x✓✔]\s+\([a-z]\)',
    r'^\s*¨\s+\([a-z]\)',
    r'^\s*[x✓✔]\s+\([a-z][a-z]?\)',
]
```

## Confidence Scoring

Base confidence: **0.85**

### Adjustments

**Positive**:
- +0.05: Good length ratio (0.8-1.2)
- +0.05: Section headers present and formatted
- +0.05: Tables detected and properly flattened
- +0.05: Checkboxes detected and standardized
- +0.05: Good paragraph structure

**Negative**:
- -0.30: Excessive content loss (ratio < 0.5)
- -0.20: Excessive content added (ratio > 2.0)

### Document-Wide Confidence

Additional factors for multi-page:
- +0.05: Consistent header hierarchy (h2/h3)
- +0.10: Tables properly flattened
- +0.05: Checkboxes standardized
- +0.05: Good content preservation (0.7-1.3 ratio)
- -0.20: Poor table formatting
- -0.20: Excessive content loss

## Best Practices

### 1. Use Appropriate Processing Mode
- **Single page/chunk**: Use `process()` for fast formatting
- **Complete document**: Use `process_entire_document()` for consistency

### 2. Verify Table Flattening
Check that tables are flattened:
```python
result = agent.process(table_text)
# Should NOT contain pipe syntax: |---|---|
assert '|---' not in result.content
# Should contain flattened format: **Column** - **Row**:
assert '**' in result.content and ' - **' in result.content
```

### 3. Monitor Confidence Scores
- **Confidence > 0.8**: High quality formatting
- **Confidence 0.6-0.8**: Review recommended
- **Confidence < 0.6**: Manual review required

### 4. Handle Empty/Minimal Content
Agent rejects content that's:
- Empty or whitespace-only
- Less than 200 chars and mostly URLs
- OCR error messages

Check `success` field before using content.

### 5. Use Footnote Conversion Sparingly
Only enable when needed:
```python
context = {"convert_footnotes": True}
```
Adds processing time for citation detection.

### 6. Check Processing Mode
For large documents:
```python
result = agent.process_entire_document(pages)
if result.metadata.get('processing_mode') == 'chunked':
    # Document was processed in 10-page chunks
    pass
```

### 7. Review Reasoning Steps
```python
for step in result.reasoning_steps:
    print(step)
# "Executing table_focused formatting strategy"
# "Successfully applied table-focused formatting"
# "Applied post-processing cleanup to remove problematic markdown tables"
```

## Integration Points

### With Pipeline
Typically positioned after VisionOCRAgent or corruption detection:

```
VisionOCRAgent → ContentFormattingAgent → CheckerAgent
```

### With BaseAgent
Inherits from `BaseAgent` ([agent_base.py](agent_base.py:42-201)):
- `make_api_call()` for AI formatting
- State management and memory
- Standardized `AgentResponse` format

### With Config
Uses configuration from [config.py](config.py):
- Model: Claude Sonnet 4 for formatting task
- Temperature: 0.0 (deterministic) to 0.1 (slight variation)
- Max tokens: 16384 for long documents

## System Prompt

Loaded from [prompts/content_formatting.txt](prompts/content_formatting.txt).

Key directives:
1. **Markdown syntax**: `##` for sections, `###` for subsections
2. **Table flattening**: MANDATORY for vector DB optimization
3. **NO pipe tables**: Critical - never use `|---|---|` syntax
4. **Checkbox standardization**: `[SELECTED]` for checked items
5. **Preserve structure**: Bullets, lists, indentation
6. **Remove metadata**: Page numbers, page breaks

## Performance Characteristics

- **Single page**: ~2-4 seconds (AI API call)
- **Multi-page (small)**: ~5-10 seconds for <10 pages
- **Multi-page (large)**: ~30-60 seconds for 30+ pages (chunked)
- **Chunked processing**: 10 pages per chunk
- **Fallback processing**: Page-by-page on errors
- **Memory**: Scales with document size
- **Tokens used**: ~1000-3000 per page depending on complexity

## Error Handling

### Validation Errors

1. **Empty input**: Returns `success=False`, error message
2. **OCR failure message**: Detects and rejects with helpful error
3. **Minimal content (<200 chars, mostly URLs)**: Rejects with suggestion to use Vision OCR

### Processing Errors

1. **API call fails**: Returns unformatted text with error logged
2. **Document too large**: Automatically switches to chunked processing
3. **Chunk processing fails**: Falls back to page-by-page processing
4. **Page processing fails**: Keeps original page text

### Graceful Degradation

```python
try:
    formatted_text, tokens_used = self.make_api_call(messages)
    return formatted_text, reasoning_steps, tokens_used
except Exception as e:
    reasoning_steps.append(f"Formatting failed: {str(e)}")
    return text, reasoning_steps, 0  # Return original text
```

## Advanced Features

### Consistency Score

For document-wide processing, calculates consistency:
```python
consistency_score = result.metadata['consistency_score']
# 0.0-1.0: Higher = more consistent formatting
```

Checks:
- Uniform header hierarchy
- Consistent table flattening
- Standardized checkboxes

### Compression Ratio

Tracks content expansion/compression:
```python
ratio = result.metadata['compression_ratio']
# < 1.0: Content compressed (tables flattened often reduce length)
# > 1.0: Content expanded (structured formatting adds markup)
```

Typical ratios:
- **0.8-1.2**: Normal formatting
- **<0.7**: Significant compression (tables heavily flattened)
- **>1.5**: Significant expansion (added structure/formatting)

### Chunked Processing

For large documents (>30 pages or >150k chars):
```python
# Automatically processes in 10-page chunks
result = agent.process_entire_document(large_doc_pages)

# Check if chunking was used
if 'chunked processing' in result.reasoning_steps[0]:
    print("Document was chunked for processing")
```

Benefits:
- Avoids API token limits
- Faster parallel processing potential
- Better error isolation

### Footnote Processing

Three styles available:

**Inline** (default):
```
Citation¹ in text.

¹ Full footnote text here.
```
Becomes:
```
Citation (Full footnote text here) in text.
```

**Minimal**:
```
Citation (Full footnote) in text.
```
(Only key info extracted)

**Preserve**:
Original format maintained.

### Custom Footnote Config

```python
context = {
    "convert_footnotes": True,
    "footnote_style": "minimal",
    "max_footnote_length": 100,
    "preserve_references": True  # Keep [1] markers
}
```

## Limitations

1. **AI-Dependent**: Requires Anthropic Claude API access
2. **Processing Time**: Multi-page documents take significant time
3. **Token Costs**: Large documents consume many tokens
4. **Language**: Optimized for English documents
5. **Table Complexity**: Very complex nested tables may lose some structure
6. **Footnote Recognition**: May miss non-standard footnote formats
7. **No Learning**: Doesn't adapt based on formatting success/failure

## Related Files

- [agent_base.py](agent_base.py) - Base agent architecture
- [config.py](config.py) - Configuration management
- [prompts/content_formatting.txt](prompts/content_formatting.txt) - System prompt
- [api_client.py](api_client.py) - API communication layer
- [logger.py](logger.py) - Logging system

## Vector Database Optimization

This agent is specifically designed for **vector database workflows**:

### Why Flattening Matters

Traditional table formats fail in vector DBs because:
```
Chunking breaks context:
Chunk 1: "Service | Cost | Coverage"
Chunk 2: "Primary Care | $50 | 80%"
         ↑ Missing header context!
```

Flattened format ensures:
```
Chunk 1: "**Cost** - **Primary Care**: $50"
         ↑ Complete, searchable context
```

### Semantic Search Benefits

Each flattened entry:
- ✅ Contains full semantic context
- ✅ Produces meaningful embeddings
- ✅ Retrieves correctly on similarity search
- ✅ Supports hybrid keyword + semantic search

### Recommended Chunking

After formatting with this agent:
```python
# Chunk on double newlines for optimal results
chunks = formatted_content.split('\n\n')

# Each chunk is now semantically complete
for chunk in chunks:
    # Embed and store in vector DB
    embedding = embed(chunk)
    store(embedding, chunk)
```

## Testing Recommendations

### Unit Tests
```python
def test_table_flattening():
    agent = ContentFormattingAgent(logger)
    table = "Col1  Col2\nVal1  Val2"
    result = agent.process(table)
    assert '**Col2** - **Col1**:' in result.content
    assert '|---' not in result.content

def test_checkbox_standardization():
    agent = ContentFormattingAgent(logger)
    form = "[x] Option A\n[ ] Option B"
    result = agent.process(form)
    assert '[SELECTED]' in result.content
    assert '[x]' not in result.content
```

### Integration Tests
```python
def test_complete_pipeline():
    vision_result = vision_agent.process({"image": img})
    format_result = formatting_agent.process(vision_result.content)
    assert format_result.success
    assert format_result.confidence > 0.7
```

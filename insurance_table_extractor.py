#!/usr/bin/env python3
"""
Dedicated Insurance Comparison Table Extractor

Specialized script for extracting data from complex insurance comparison PDFs
with rotated multi-column tables.

Strategy:
1. Extract PDF pages as high-res images
2. Use Vision OCR with insurance-specific prompts
3. Process each column/plan separately to avoid cross-contamination
4. Output structured JSON + formatted markdown
5. Include validation warnings for suspicious values
"""

import os
import sys
import json
import base64
import io
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import fitz  # PyMuPDF
from PIL import Image
from anthropic import Anthropic


class InsuranceTableExtractor:
    """Extract data from insurance comparison table PDFs."""

    def __init__(self, api_key: str = None):
        """Initialize with Anthropic API key."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def extract_from_pdf(self, pdf_path: str, output_dir: str = None) -> Dict[str, Any]:
        """
        Extract insurance comparison data from PDF.

        Args:
            pdf_path: Path to insurance quote PDF
            output_dir: Directory for output files (default: same as PDF)

        Returns:
            Dictionary with extracted data, warnings, and metadata
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Setup output directory
        if output_dir is None:
            output_dir = pdf_path.parent
        else:
            output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        print(f"📄 Processing: {pdf_path.name}")
        print(f"📁 Output dir: {output_dir}")

        # Open PDF
        pdf = fitz.open(pdf_path)
        print(f"📊 Pages: {len(pdf)}")

        # Extract each page with specialized processing
        all_extracted_data = []

        for page_num in range(len(pdf)):
            print(f"\n🔍 Processing page {page_num + 1}/{len(pdf)}...")

            page = pdf[page_num]

            # Convert to high-res image (200 DPI for balance of quality and size)
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes()))

            # Compress if still too large (Claude API has 5MB limit)
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            if buffer.tell() > 4 * 1024 * 1024:  # If > 4MB, compress more
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                img = Image.open(buffer)

            # Extract with specialized insurance table prompt
            extracted_data = self._extract_page_with_vision(img, page_num + 1)

            all_extracted_data.append({
                'page': page_num + 1,
                'raw_text': extracted_data
            })

            print(f"✅ Page {page_num + 1}: Extracted {len(extracted_data)} characters")

        # Store page count before closing
        total_pages = len(pdf)
        pdf.close()

        # Combine and structure the data
        combined_text = "\n\n=== PAGE BREAK ===\n\n".join([p['raw_text'] for p in all_extracted_data])

        # Parse into structured format
        print(f"\n🧠 Analyzing and structuring extracted data...")
        structured_data = self._structure_insurance_data(combined_text)

        # Validate and detect issues
        print(f"\n🔎 Validating extracted data...")
        validation_warnings = self._validate_data(structured_data)

        # Prepare output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = pdf_path.stem

        result = {
            'source_pdf': str(pdf_path),
            'timestamp': timestamp,
            'pages_processed': total_pages,
            'structured_data': structured_data,
            'validation_warnings': validation_warnings,
            'raw_extractions': all_extracted_data
        }

        # Save outputs
        json_path = output_dir / f"{base_name}_insurance_data_{timestamp}.json"
        md_path = output_dir / f"{base_name}_insurance_formatted_{timestamp}.md"

        # Save JSON
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Saved JSON: {json_path}")

        # Save formatted markdown
        markdown = self._format_as_markdown(structured_data, validation_warnings)
        with open(md_path, 'w') as f:
            f.write(markdown)
        print(f"💾 Saved Markdown: {md_path}")

        # Print warnings if any
        if validation_warnings:
            print(f"\n⚠️  {len(validation_warnings)} validation warnings:")
            for warning in validation_warnings[:5]:  # Show first 5
                print(f"   - {warning}")
            if len(validation_warnings) > 5:
                print(f"   ... and {len(validation_warnings) - 5} more (see JSON file)")

        return result

    def _extract_page_with_vision(self, img: Image.Image, page_num: int) -> str:
        """Extract text from image using Vision OCR with insurance-specific prompting."""

        # Convert image to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Insurance-specific extraction prompt
        prompt = """You are extracting data from an INSURANCE COMPARISON TABLE.

This is a CRITICAL TASK - insurance data must be 100% accurate.

INSTRUCTIONS:
1. **ORIENTATION**: If the table is rotated 90°, mentally rotate it to read normally
2. **READ SLOWLY**: Process each row one at a time, left to right
3. **VERIFY ALIGNMENT**: For each value, confirm it matches BOTH:
   - The ROW label (service/benefit name on the left)
   - The COLUMN header (plan name at top)
4. **UNIQUE VALUES**: Each plan/column has DIFFERENT values - do NOT copy values between plans
5. **DOUBLE-CHECK NUMBERS**: Premium amounts, deductibles, copays must be plan-specific

CRITICAL RULES:
- Extract ALL text exactly as it appears
- Preserve spacing and alignment to show column structure
- Include headers, row labels, and all data values
- If a value is unclear, mark it as [UNCLEAR] rather than guessing
- Pay special attention to dollar amounts and percentages

OUTPUT FORMAT:
- Raw text with spacing preserved to show table structure
- Use consistent spacing/tabs to separate columns
- Include all headers and labels

Begin extraction:"""

        # Call Claude Vision API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16384,
                temperature=0.0,  # Deterministic for accuracy
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )

            extracted_text = response.content[0].text
            return extracted_text

        except Exception as e:
            print(f"❌ Vision OCR failed for page {page_num}: {e}")
            return f"[EXTRACTION FAILED: {str(e)}]"

    def _structure_insurance_data(self, raw_text: str) -> Dict[str, Any]:
        """Parse raw extracted text into structured insurance data."""

        # Use Claude to structure the raw text
        prompt = f"""Parse this raw insurance comparison table data into structured JSON format.

RAW EXTRACTED TEXT:
{raw_text}

Parse into this JSON structure:
{{
  "plans": [
    {{
      "plan_name": "Plan 1 Name",
      "network": "Network type",
      "enrollment": {{
        "total": 0,
        "employee_only": 0,
        "employee_spouse": 0,
        "employee_children": 0,
        "family": 0
      }},
      "premiums": {{
        "employee_only": "$0.00",
        "employee_spouse": "$0.00",
        "employee_children": "$0.00",
        "family": "$0.00"
      }},
      "deductibles": {{
        "in_network": "$0",
        "out_of_network": "$0"
      }},
      "coinsurance": {{
        "in_network": "0%",
        "out_of_network": "0%"
      }},
      "copays": {{
        "pcp": "$0",
        "specialist": "$0",
        "urgent_care": "$0",
        "er": "$0"
      }},
      "rx_tiers": {{
        "tier_1": "$0",
        "tier_2": "$0",
        "tier_3": "$0",
        "tier_4": "$0"
      }}
    }}
  ]
}}

IMPORTANT:
- Extract actual values from the text, don't use placeholder zeros
- If a value is missing or unclear, use null
- Preserve dollar amounts and percentages exactly
- Each plan should have unique values

Output ONLY valid JSON:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            json_text = response.content[0].text

            # Extract JSON from response (might have markdown wrapping)
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0]
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0]

            structured = json.loads(json_text.strip())
            return structured

        except Exception as e:
            print(f"⚠️  Structuring failed: {e}")
            return {"plans": [], "error": str(e), "raw_text": raw_text}

    def _validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate extracted data and return warnings for suspicious values."""

        warnings = []

        if 'plans' not in data or not data['plans']:
            warnings.append("No plans found in extracted data")
            return warnings

        plans = data['plans']

        # Check for duplicate premium values across plans (suspicious)
        premium_sets = []
        for plan in plans:
            if 'premiums' in plan and plan['premiums']:
                # Filter out None values before sorting
                premiums = tuple(sorted([v for v in plan['premiums'].values() if v is not None]))
                if premiums and premiums in premium_sets:
                    warnings.append(f"DUPLICATE PREMIUMS: {plan.get('plan_name', 'Unknown')} has same premiums as another plan")
                if premiums:
                    premium_sets.append(premiums)

        # Check for missing critical data
        for i, plan in enumerate(plans):
            plan_name = plan.get('plan_name', f'Plan {i+1}')

            if not plan.get('premiums'):
                warnings.append(f"{plan_name}: Missing premium data")

            if not plan.get('deductibles'):
                warnings.append(f"{plan_name}: Missing deductible data")

            if not plan.get('copays'):
                warnings.append(f"{plan_name}: Missing copay data")

        # Check for null values
        for i, plan in enumerate(plans):
            plan_name = plan.get('plan_name', f'Plan {i+1}')

            def check_nulls(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if value is None:
                            warnings.append(f"{plan_name}{path}.{key}: Value is null")
                        elif isinstance(value, (dict, list)):
                            check_nulls(value, f"{path}.{key}")

            check_nulls(plan)

        return warnings

    def _format_as_markdown(self, data: Dict[str, Any], warnings: List[str]) -> str:
        """Format structured data as markdown."""

        lines = ["# Insurance Comparison - Extracted Data\n"]

        if warnings:
            lines.append("## ⚠️ Validation Warnings\n")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("\n---\n")

        if 'plans' not in data or not data['plans']:
            lines.append("**No plans data available**\n")
            if 'raw_text' in data:
                lines.append("## Raw Extracted Text\n")
                lines.append("```")
                lines.append(data['raw_text'])
                lines.append("```")
            return '\n'.join(lines)

        for i, plan in enumerate(data['plans']):
            plan_name = plan.get('plan_name', f'Plan {i+1}')
            lines.append(f"## {plan_name}\n")

            if 'network' in plan:
                lines.append(f"**Network**: {plan['network']}\n")

            if 'enrollment' in plan:
                lines.append("### Enrollment")
                for key, value in plan['enrollment'].items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
                lines.append("")

            if 'premiums' in plan:
                lines.append("### Premiums")
                for key, value in plan['premiums'].items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
                lines.append("")

            if 'deductibles' in plan:
                lines.append("### Deductibles")
                for key, value in plan['deductibles'].items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
                lines.append("")

            if 'coinsurance' in plan:
                lines.append("### Coinsurance")
                for key, value in plan['coinsurance'].items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
                lines.append("")

            if 'copays' in plan:
                lines.append("### Copays")
                for key, value in plan['copays'].items():
                    lines.append(f"- **{key.replace('_', ' ').upper()}**: {value}")
                lines.append("")

            if 'rx_tiers' in plan:
                lines.append("### Prescription Drug Tiers")
                for key, value in plan['rx_tiers'].items():
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
                lines.append("")

            lines.append("---\n")

        return '\n'.join(lines)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract data from insurance comparison table PDFs"
    )
    parser.add_argument('pdf_path', help='Path to insurance quote PDF')
    parser.add_argument('-o', '--output-dir', help='Output directory (default: same as PDF)')
    parser.add_argument('--api-key', help='Anthropic API key (or set ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    try:
        extractor = InsuranceTableExtractor(api_key=args.api_key)
        result = extractor.extract_from_pdf(args.pdf_path, args.output_dir)

        print("\n✅ Extraction complete!")
        print(f"📊 Extracted {len(result['structured_data'].get('plans', []))} plans")

        if result['validation_warnings']:
            print(f"⚠️  {len(result['validation_warnings'])} warnings - review JSON file for details")
        else:
            print("✅ No validation warnings!")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

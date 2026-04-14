#!/usr/bin/env python3
"""
Convert SAAS_PRICING_PROPOSAL.md to PDF with proper table formatting
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path

def convert_markdown_to_pdf(md_file, pdf_file):
    """Convert markdown file to PDF with styling."""

    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert markdown to HTML with tables extension
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite']
    )

    # Add CSS styling for professional look
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>SaaS Pricing Proposal</title>
        <style>
            @page {{
                size: letter;
                margin: 0.75in;
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 10pt;
                    color: #666;
                }}
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
            }}

            h1 {{
                color: #1a1a1a;
                border-bottom: 3px solid #4A90E2;
                padding-bottom: 10px;
                margin-top: 30px;
                font-size: 28pt;
            }}

            h2 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 8px;
                margin-top: 25px;
                font-size: 20pt;
                page-break-after: avoid;
            }}

            h3 {{
                color: #34495e;
                margin-top: 20px;
                font-size: 16pt;
                page-break-after: avoid;
            }}

            h4 {{
                color: #555;
                margin-top: 15px;
                font-size: 14pt;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 10pt;
                page-break-inside: avoid;
            }}

            th {{
                background-color: #4A90E2;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
                border: 1px solid #3498db;
            }}

            td {{
                padding: 10px;
                border: 1px solid #ddd;
            }}

            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}

            tr:hover {{
                background-color: #e3f2fd;
            }}

            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }}

            pre {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #4A90E2;
                border-radius: 4px;
                overflow-x: auto;
                font-size: 9pt;
                page-break-inside: avoid;
            }}

            pre code {{
                background-color: transparent;
                padding: 0;
            }}

            blockquote {{
                border-left: 4px solid #4A90E2;
                padding-left: 20px;
                margin-left: 0;
                color: #555;
                font-style: italic;
                background-color: #f8f9fa;
                padding: 10px 20px;
            }}

            ul, ol {{
                margin: 15px 0;
                padding-left: 30px;
            }}

            li {{
                margin: 8px 0;
            }}

            strong {{
                color: #2c3e50;
            }}

            hr {{
                border: none;
                border-top: 2px solid #e0e0e0;
                margin: 30px 0;
            }}

            /* Tier pricing boxes */
            h3:contains("Starter"),
            h3:contains("Professional"),
            h3:contains("Business"),
            h3:contains("Enterprise") {{
                background-color: #f0f8ff;
                padding: 10px;
                border-radius: 5px;
            }}

            /* Emoji support */
            .emoji {{
                font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji";
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    print(f"Converting {md_file} to PDF...")
    HTML(string=styled_html).write_pdf(
        pdf_file,
        stylesheets=[CSS(string='@page { size: letter; }')]
    )

    print(f"✅ PDF created: {pdf_file}")
    print(f"   Size: {Path(pdf_file).stat().st_size / 1024:.1f} KB")

if __name__ == '__main__':
    import sys

    # Allow command line argument for input file
    if len(sys.argv) > 1:
        md_file = Path(sys.argv[1])
        pdf_file = md_file.with_suffix('.pdf')
    else:
        md_file = Path(__file__).parent / 'SAAS_PRICING_PROPOSAL.md'
        pdf_file = Path(__file__).parent / 'SAAS_PRICING_PROPOSAL.pdf'

    if not md_file.exists():
        print(f"❌ Error: {md_file} not found")
        exit(1)

    try:
        convert_markdown_to_pdf(md_file, pdf_file)
        print(f"\n🎉 Success! Open the PDF:")
        print(f"   open {pdf_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

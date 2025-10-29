#!/usr/bin/env python3
"""
Convert Markdown to PDF
Converts SETUP_GUIDE_MACOS.md to a nicely formatted PDF
"""

import markdown
import os
import subprocess
import sys
from pathlib import Path

def markdown_to_html(md_file, output_html=None):
    """Convert markdown file to HTML with styling"""
    
    if output_html is None:
        output_html = md_file.replace('.md', '.html')
    
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert to HTML with extensions
    md = markdown.Markdown(extensions=['toc', 'tables', 'fenced_code', 'codehilite'])
    html_content = md.convert(md_content)
    
    # Create styled HTML document
    styled_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scientific Papers RAG System - macOS Setup Guide</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
            margin-top: 25px;
        }}
        
        h3 {{
            color: #2c3e50;
            margin-top: 20px;
        }}
        
        h4 {{
            color: #7f8c8d;
            margin-top: 15px;
        }}
        
        code {{
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }}
        
        pre {{
            background-color: #f8f9fa;
            border: 1px solid #e1e8ed;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            margin: 16px 0;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
            color: #333;
        }}
        
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 16px 0;
            padding: 0 16px;
            color: #6a737d;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 16px 0;
        }}
        
        th, td {{
            border: 1px solid #dfe2e5;
            padding: 8px 12px;
            text-align: left;
        }}
        
        th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        
        ul, ol {{
            padding-left: 24px;
        }}
        
        li {{
            margin: 4px 0;
        }}
        
        strong {{
            color: #2c3e50;
        }}
        
        em {{
            color: #7f8c8d;
        }}
        
        .emoji {{
            font-style: normal;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }}
        
        @media print {{
            body {{
                margin: 0;
                padding: 15px;
                font-size: 12px;
                line-height: 1.4;
            }}
            
            h1 {{
                font-size: 24px;
                page-break-after: avoid;
            }}
            
            h2 {{
                font-size: 20px;
                page-break-after: avoid;
            }}
            
            h3 {{
                font-size: 16px;
                page-break-after: avoid;
            }}
            
            pre {{
                page-break-inside: avoid;
                font-size: 10px;
            }}
            
            table {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    {html_content}
    
    <hr>
    <footer style="text-align: center; color: #7f8c8d; font-size: 0.9em; margin-top: 40px;">
        <p>Scientific Papers RAG System - macOS Setup Guide</p>
        <p>Generated from Markdown on {Path(md_file).stat().st_mtime}</p>
    </footer>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    return output_html

def html_to_pdf_instructions(html_file):
    """Provide instructions for converting HTML to PDF"""
    
    pdf_file = html_file.replace('.html', '.pdf')
    
    print(f"📄 HTML file created: {html_file}")
    print(f"🖨️  To convert to PDF, follow these steps:")
    print()
    print("Option 1 - Using Safari/Chrome:")
    print(f"1. Open {html_file} in Safari or Chrome")
    print("2. Press Cmd+P (Print)")
    print("3. Choose 'Save as PDF'")
    print(f"4. Save as '{pdf_file}'")
    print()
    print("Option 2 - Using wkhtmltopdf (if installed):")
    print(f"   brew install wkhtmltopdf")
    print(f"   wkhtmltopdf {html_file} {pdf_file}")
    print()
    print("Option 3 - Using pandoc (if installed):")
    print(f"   brew install pandoc basictex")
    print(f"   pandoc SETUP_GUIDE_MACOS.md -o {pdf_file}")
    
    return pdf_file

def try_automated_pdf_conversion(html_file):
    """Try to automatically convert HTML to PDF using available tools"""
    
    pdf_file = html_file.replace('.html', '.pdf')
    
    # Try wkhtmltopdf
    try:
        result = subprocess.run(['wkhtmltopdf', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("🔄 Converting with wkhtmltopdf...")
            result = subprocess.run([
                'wkhtmltopdf',
                '--page-size', 'A4',
                '--margin-top', '20mm',
                '--margin-bottom', '20mm',
                '--margin-left', '20mm',
                '--margin-right', '20mm',
                '--print-media-type',
                html_file, pdf_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ PDF created successfully: {pdf_file}")
                return pdf_file
            else:
                print(f"❌ wkhtmltopdf failed: {result.stderr}")
        
    except FileNotFoundError:
        pass
    
    # Try pandoc
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("🔄 Converting with pandoc...")
            result = subprocess.run([
                'pandoc', 'SETUP_GUIDE_MACOS.md',
                '-o', pdf_file,
                '--pdf-engine=xelatex'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ PDF created successfully: {pdf_file}")
                return pdf_file
            else:
                print(f"❌ pandoc failed: {result.stderr}")
        
    except FileNotFoundError:
        pass
    
    return None

def main():
    """Main conversion function"""
    
    md_file = "SETUP_GUIDE_MACOS.md"
    
    if not os.path.exists(md_file):
        print(f"❌ Error: {md_file} not found!")
        sys.exit(1)
    
    print(f"📖 Converting {md_file} to PDF...")
    print()
    
    # Convert to HTML
    html_file = markdown_to_html(md_file)
    
    # Try automated conversion
    pdf_file = try_automated_pdf_conversion(html_file)
    
    if not pdf_file:
        # Provide manual instructions
        html_to_pdf_instructions(html_file)
    
    print()
    print("🎉 Conversion process complete!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Simple PDF Generator using reportlab
Creates a basic PDF from the markdown content
"""

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

import re
import os

def create_simple_pdf():
    """Create a simple PDF version using reportlab if available"""
    
    if not REPORTLAB_AVAILABLE:
        print("❌ reportlab not available. Installing...")
        os.system("pip3 install reportlab")
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
        except ImportError:
            print("❌ reportlab installation failed. Using text-based approach.")
            return create_text_pdf()
    
    # Read the markdown file
    with open("SETUP_GUIDE_MACOS.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate("SETUP_GUIDE_MACOS.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=12,
    )
    
    story = []
    
    # Split content into lines
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('# '):
            # Main title
            title = line[2:].strip()
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
        elif line.startswith('## '):
            # Section heading
            heading = line[3:].strip()
            story.append(Paragraph(heading, heading_style))
            story.append(Spacer(1, 6))
            
        elif line.startswith('### '):
            # Subsection
            subheading = line[4:].strip()
            story.append(Paragraph(subheading, styles['Heading3']))
            story.append(Spacer(1, 6))
            
        elif line.startswith('```'):
            # Code block (skip for now)
            continue
            
        elif line.startswith('- ') or line.startswith('* '):
            # Bullet point
            bullet = line[2:].strip()
            story.append(Paragraph(f"• {bullet}", styles['Normal']))
            
        elif line and not line.startswith('#'):
            # Regular paragraph
            # Remove markdown formatting
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\\1</b>', line)
            clean_line = re.sub(r'\*(.*?)\*', r'<i>\\1</i>', clean_line)
            clean_line = re.sub(r'`(.*?)`', r'<font name="Courier">\\1</font>', clean_line)
            
            if clean_line:
                story.append(Paragraph(clean_line, styles['Normal']))
                story.append(Spacer(1, 6))
    
    # Build PDF
    doc.build(story)
    return "SETUP_GUIDE_MACOS.pdf"

def create_text_pdf():
    """Fallback: create a text-based PDF instructions"""
    
    content = """
PDF Generation Instructions
===========================

The HTML version (SETUP_GUIDE_MACOS.html) has been created successfully.

To convert to PDF manually:

1. USING SAFARI (RECOMMENDED):
   - Open SETUP_GUIDE_MACOS.html in Safari
   - Press Cmd+P
   - In the print dialog, click "PDF" dropdown (bottom left)
   - Select "Save as PDF"
   - Choose filename: SETUP_GUIDE_MACOS.pdf
   - Click Save

2. USING CHROME:
   - Open SETUP_GUIDE_MACOS.html in Chrome
   - Press Cmd+P
   - In "Destination", click "Change"
   - Select "Save as PDF"
   - Click "Save"

3. USING COMMAND LINE (if tools available):
   - Install: brew install wkhtmltopdf
   - Run: wkhtmltopdf SETUP_GUIDE_MACOS.html SETUP_GUIDE_MACOS.pdf

The HTML file includes professional styling and is optimized for PDF printing.
"""
    
    with open("PDF_INSTRUCTIONS.txt", "w") as f:
        f.write(content)
    
    print("📝 Created PDF_INSTRUCTIONS.txt with manual conversion steps")
    return "PDF_INSTRUCTIONS.txt"

def main():
    print("🔄 Attempting PDF generation...")
    
    try:
        pdf_file = create_simple_pdf()
        print(f"✅ PDF created: {pdf_file}")
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        print("📝 Creating instruction file instead...")
        create_text_pdf()

if __name__ == "__main__":
    main()
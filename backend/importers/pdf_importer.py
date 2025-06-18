
"""
backend/importers/pdf_importer.py

Utilities to extract content from any PDF into ContentItems.
"""

import pdfplumber
import re
from models import ContentItem
from typing import List
import logging

logger = logging.getLogger(__name__)

def extract_chapters(pdf_path: str, num_chapters: int = 365) -> List[ContentItem]:
    """
    Extracts content from a PDF file using multiple strategies.
    
    First tries to find chapters, then falls back to page-based extraction.

    Args:
        pdf_path: Local filesystem path to the PDF.
        num_chapters: Maximum number of sections to extract.

    Returns:
        List of ContentItem objects for each section.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Extract all text from PDF
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n\n"
            
            if not full_text.strip():
                return [ContentItem(
                    title="Empty PDF",
                    content="No text content could be extracted from this PDF.",
                    content_type="blog",
                    source_url=None,
                    author=""
                )]
            
            # Try different extraction strategies
            items = []
            
            # Strategy 1: Look for chapter markers
            items = _extract_by_chapters(full_text, num_chapters)
            
            # Strategy 2: If no chapters found, try section headers
            if not items:
                items = _extract_by_headers(full_text, num_chapters)
            
            # Strategy 3: If no sections found, split by pages or content length
            if not items:
                items = _extract_by_pages(pdf, num_chapters)
            
            return items
            
    except Exception as e:
        logger.error(f"Error extracting from PDF {pdf_path}: {e}")
        return [ContentItem(
            title="PDF Processing Error",
            content=f"Error occurred while processing PDF: {str(e)}",
            content_type="blog",
            source_url=None,
            author=""
        )]

def _extract_by_chapters(text: str, max_sections: int) -> List[ContentItem]:
    """Extract content by looking for chapter markers."""
    items = []
    
    # Look for various chapter patterns
    chapter_patterns = [
        r'Chapter\s+(\d+)',
        r'CHAPTER\s+(\d+)', 
        r'Ch\.\s*(\d+)',
        r'Section\s+(\d+)',
        r'Part\s+(\d+)',
        r'(\d+)\.\s*[A-Z]'  # 1. Introduction, 2. Background, etc.
    ]
    
    for pattern in chapter_patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if len(matches) >= 2:  # Need at least 2 chapters to split
            for i, match in enumerate(matches[:max_sections]):
                start_pos = match.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                chapter_text = text[start_pos:end_pos].strip()
                chapter_num = match.group(1) if match.groups() else str(i + 1)
                
                # Extract title from first line or use chapter number
                lines = chapter_text.split('\n')
                title = f"Chapter {chapter_num}"
                if len(lines) > 1:
                    first_line = lines[0].strip()
                    if len(first_line) < 100:  # Likely a title
                        title = first_line
                
                items.append(ContentItem(
                    title=title,
                    content=chapter_text,
                    content_type="blog",
                    source_url=None,
                    author=""
                ))
            break
    
    return items

def _extract_by_headers(text: str, max_sections: int) -> List[ContentItem]:
    """Extract content by looking for section headers."""
    items = []
    
    # Look for lines that might be headers (short lines followed by content)
    lines = text.split('\n')
    potential_headers = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if (line and len(line) < 80 and 
            not line.endswith('.') and 
            not line.endswith(',') and
            len(line.split()) < 10):
            potential_headers.append((i, line))
    
    if len(potential_headers) >= 2:
        for i, (line_idx, header) in enumerate(potential_headers[:max_sections]):
            start_line = line_idx
            end_line = potential_headers[i + 1][0] if i + 1 < len(potential_headers) else len(lines)
            
            section_lines = lines[start_line:end_line]
            section_text = '\n'.join(section_lines).strip()
            
            items.append(ContentItem(
                title=header,
                content=section_text,
                content_type="blog",
                source_url=None,
                author=""
            ))
    
    return items

def _extract_by_pages(pdf, max_sections: int) -> List[ContentItem]:
    """Extract content by grouping pages."""
    items = []
    total_pages = len(pdf.pages)
    
    if total_pages <= max_sections:
        # One item per page
        for i, page in enumerate(pdf.pages[:max_sections]):
            page_text = page.extract_text()
            if page_text:
                items.append(ContentItem(
                    title=f"Page {i + 1}",
                    content=page_text,
                    content_type="blog",
                    source_url=None,
                    author=""
                ))
    else:
        # Group pages
        pages_per_section = max(1, total_pages // max_sections)
        
        for section_num in range(max_sections):
            start_page = section_num * pages_per_section
            end_page = min((section_num + 1) * pages_per_section, total_pages)
            
            section_text = ""
            for page_idx in range(start_page, end_page):
                page_text = pdf.pages[page_idx].extract_text()
                if page_text:
                    section_text += page_text + "\n\n"
            
            if section_text.strip():
                items.append(ContentItem(
                    title=f"Section {section_num + 1} (Pages {start_page + 1}-{end_page})",
                    content=section_text.strip(),
                    content_type="blog",
                    source_url=None,
                    author=""
                ))
    
    return items

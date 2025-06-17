
"""
@author Huy Le (huyisme-005)
backend/utils/html2md.py

Wrapper over html2text to convert HTML to Markdown consistently.
"""

import html2text

def convert(html: str) -> str:
    """
    Convert raw HTML string into Markdown.

    Args:
        html: HTML content.

    Returns:
        Markdown-formatted text.
    """
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0
    h.unicode_snob = True
    h.escape_snob = True
    markdown = h.handle(html)
    
    # Clean up formatting
    import re
    markdown = markdown.strip()
    # Replace multiple consecutive newlines with proper paragraph breaks
    markdown = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown)
    # Ensure proper spacing after headers
    markdown = re.sub(r'(#{1,6}[^\n]*)\n([^\n#])', r'\1\n\n\2', markdown)
    # Ensure proper spacing after lists
    markdown = re.sub(r'(\*[^\n]*)\n([^\n\*\s])', r'\1\n\n\2', markdown)
    
    return markdown

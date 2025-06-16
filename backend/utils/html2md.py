
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
    return h.handle(html)

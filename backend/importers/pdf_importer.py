"""
backend/importers/pdf_importer.py

Utilities to extract chapters from a PDF into ContentItems.
"""

import pdfplumber
from models import ContentItem

def extract_chapters(pdf_path: str, num_chapters: int = 8):
    """
    Extracts the first N chapters from a PDF file.

    Assumes chapter headings start with "Chapter X".

    Args:
        pdf_path: Local filesystem path to the PDF.
        num_chapters: Number of chapters to extract.

    Returns:
        List of ContentItem objects for each chapter.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n\n".join(p.extract_text() or "" for p in pdf.pages)
    parts = text.split("Chapter ")[1:num_chapters+1]
    items = []
    for part in parts:
        header, *body = part.split("\n", 1)
        title = f"Chapter {header.strip().split()[0]}"
        content = f"# Chapter {header.strip()}\n\n{body[0].strip() if body else ''}"
        items.append(ContentItem(
            title=title,
            content=content,
            content_type="book"
        ))
    return items

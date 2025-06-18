"""
backend/scrapers/interviewing_guides.py

Scraper for the /learn#interview-guides section on interviewing.io.
"""

import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from models import ContentItem

BASE = "https://interviewing.io"

class InterviewingGuidesScraper(BaseScraper):
    """
    Scrapes every interview guide page under /learn#interview-guides.

    - discover_links: finds guide URLs.
    - parse_page: returns ContentItem with Markdown content.
    """

    def __init__(self, url: str = None):
        self.url = url

    def discover_links(self):
        """Fetches /learn and extracts all interview-guide links, starting from self.url if provided."""
        url = self.url or BASE + "/learn"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        return [BASE + a["href"] for a in soup.select("section#interview-guides a")]

    def parse_page(self, url: str) -> ContentItem:
        """Parses one interview guide into a ContentItem."""
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Extract title with fallback
        title = "Untitled"
        title_elem = soup.select_one("h1")
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract content with multiple selectors and fallback
        content = ""
        selectors = [".guide-content", "main", "article", ".content", ".post-content", "body"]
        
        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                body_html = str(content_elem)
                from utils.html2md import convert
                content = convert(body_html).strip()
                if content and len(content) > 50:  # Ensure meaningful content
                    break
        
        # Fallback: extract all paragraph text
        if not content or len(content) < 50:
            paragraphs = soup.find_all(['p', 'div', 'span'])
            text_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    text_parts.append(text)
            content = '\n\n'.join(text_parts)
        
        return ContentItem(
            title=title,
            content=content if content else f"Could not extract content from {url}",
            content_type="other",
            source_url=url
        )

"""
backend/scrapers/interviewing_topics.py

Scraper for interviewing.io company guides under /topics.
"""

import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from models import ContentItem

BASE = "https://interviewing.io"

class InterviewingTopicsScraper(BaseScraper):
    """
    Scrapes all company guide pages from /topics#companies.

    - discover_links: extracts each company guide URL.
    - parse_page: converts guide HTML into Markdown ContentItem.
    """

    def __init__(self, url: str = None):
        self.url = url

    def discover_links(self):
        """Fetches /topics and returns all company guide links, starting from self.url if provided."""
        url = self.url or BASE + "/topics"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        return [BASE + a["href"] for a in soup.select("section#companies a")]

    def parse_page(self, url: str) -> ContentItem:
        """Parses a company guide page into ContentItem."""
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

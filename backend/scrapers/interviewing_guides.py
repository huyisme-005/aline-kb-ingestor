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

    def discover_links(self):
        """Fetches /learn and extracts all interview-guide links."""
        resp = requests.get(f"{BASE}/learn")
        soup = BeautifulSoup(resp.text, "html.parser")
        return [BASE + a["href"] for a in soup.select("section#interview-guides a")]

    def parse_page(self, url: str) -> ContentItem:
        """Parses one interview guide into a ContentItem."""
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.select_one("h1").get_text(strip=True)
        body_html = str(soup.select_one(".guide-content"))
        from utils.html2md import convert
        markdown = convert(body_html)
        return ContentItem(
            title=title,
            content=markdown,
            content_type="other",
            source_url=url
        )

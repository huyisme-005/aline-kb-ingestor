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

    def discover_links(self):
        """Fetches /topics and returns all company guide links."""
        resp = requests.get(f"{BASE}/topics")
        soup = BeautifulSoup(resp.text, "html.parser")
        return [BASE + a["href"] for a in soup.select("section#companies a")]

    def parse_page(self, url: str) -> ContentItem:
        """Parses a company guide page into ContentItem."""
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

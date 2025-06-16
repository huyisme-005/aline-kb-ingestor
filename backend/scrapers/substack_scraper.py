"""
backend/scrapers/substack_scraper.py

Generic Substack scraper for any substack.com blog.
"""

import requests
from bs4 import BeautifulSoup
import html2text
from base_scraper import BaseScraper
from models import ContentItem

class SubstackScraper(BaseScraper):
    """
    Scraper plugin for Substack publications.

    Args:
        base_url: Root URL of the Substack (e.g. https://foo.substack.com)

    Methods:
        discover_links: reads the /archive page for all post URLs.
        parse_page: extracts title and content into a ContentItem.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    def discover_links(self):
        """Fetch /archive and collect all post URLs."""
        resp = requests.get(self.base_url + "/archive")
        soup = BeautifulSoup(resp.text, "html.parser")
        return [a["href"] for a in soup.select(".post-preview-title a")]

    def parse_page(self, url: str) -> ContentItem:
        """Parse a Substack post into a ContentItem."""
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.select_one("h1.post-title").get_text(strip=True)
        body_html = str(soup.select_one(".post-content"))
        markdown = html2text.html2text(body_html)
        return ContentItem(
            title=title,
            content=markdown,
            content_type="blog",
            source_url=url
        )

"""
backend/scrapers/nil_mamano_dsa.py

Scraper for Nil Mamano's DS&A category blog posts.
"""

import requests
from bs4 import BeautifulSoup
import html2text
from base_scraper import BaseScraper
from models import ContentItem

class NilMamanoDSAScraper(BaseScraper):
    """
    Crawls the DS&A category on nilmamano.com and extracts each post.

    - discover_links: paginates through /blog/category/dsa pages.
    - parse_page: extracts title, author, and Markdown content.
    """

    BASE = "https://nilmamano.com"

    def discover_links(self):
        """Discover all DS&A post URLs by iterating pages."""
        page = 1
        urls = []
        while True:
            resp = requests.get(f"{self.BASE}/blog/category/dsa/page/{page}")
            soup = BeautifulSoup(resp.text, "html.parser")
            posts = soup.select(".post-title a")
            if not posts:
                break
            urls.extend([a["href"] for a in posts])
            page += 1
        return urls

    def parse_page(self, url: str) -> ContentItem:
        """Parse a single DS&A post into a ContentItem."""
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.select_one("h1.entry-title").get_text(strip=True)
        body_html = str(soup.select_one(".entry-content"))
        markdown = html2text.html2text(body_html)
        return ContentItem(
            title=title,
            content=markdown,
            content_type="blog",
            source_url=url,
            author="Nil Mamano"
        )


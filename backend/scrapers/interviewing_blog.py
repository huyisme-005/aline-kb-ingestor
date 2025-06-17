"""
backend/scrapers/interviewing_blog.py

Scraper for the interviewing.io blog section.
"""

import requests
from bs4 import BeautifulSoup
import html2text
from base_scraper import BaseScraper
from models import ContentItem
from utils.html2md import convert

BASE = "https://interviewing.io"

class InterviewingBlogScraper(BaseScraper):
    """
    Scrapes every post under /blog on interviewing.io.

    Methods:
        discover_links: paginates through /blog pages to collect post URLs.
        parse_page: fetches a post URL and extracts title, author, and content.
    """

    def discover_links(self):
        """Collects all blog post URLs by paginating until no more posts."""
        page = 1
        urls = []
        while True:
            resp = requests.get(f"{BASE}/blog?page={page}")
            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a["href"] for a in soup.select("a.post-link")]
            if not links:
                break
            urls.extend(links)
            page += 1
        return [BASE + u for u in urls]

    def parse_page(self, url: str) -> ContentItem:
        """Parses a single blog post into a ContentItem."""
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.select_one("h1.post-title").get_text(strip=True)
        author_tag = soup.select_one(".post-author")
        author = author_tag.get_text(strip=True) if author_tag else ""
        body_html = str(soup.select_one(".post-content"))
        markdown = html2text.html2text(body_html)
        return ContentItem(
            title=title,
            content=markdown,
            content_type="blog",
            source_url=url,
            author=author
        )

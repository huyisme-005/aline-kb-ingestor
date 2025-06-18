"""
backend/scrapers/nil_mamano_dsa.py

Scraper for Nil Mamano's DS&A category blog posts.
"""

import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from models import ContentItem
from utils.html2md import convert

class NilMamanoDSAScraper(BaseScraper):
    """
    Crawls the DS&A category on nilmamano.com and extracts each post.

    - discover_links: paginates through /blog/category/dsa pages.
    - parse_page: extracts title, author, and Markdown content.
    """

    BASE = "https://nilmamano.com"

    def __init__(self, url: str = None):
        self.url = url

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
        """Parses a single blog post into ContentItem."""
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title with fallback
        title = "Untitled"
        title_elem = soup.select_one("h1.entry-title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract content with multiple selectors and fallback
        content = ""
        selectors = [".entry-content", "main", "article", ".content", ".post-content", ".blog-content", "body"]

        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                body_html = str(content_elem)
                 
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
            content_type="blog",
            source_url=url,
            author="Nil Mamano"
        )
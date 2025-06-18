"""
backend/scrapers/interviewing_blog.py

Scraper for the interviewing.io blog section.
"""

import requests
from bs4 import BeautifulSoup
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
        """Parses a blog post page into ContentItem."""
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title with fallback
        title = "Untitled"
        title_elem = soup.select_one("h1")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Extract content with multiple selectors and fallback
        content = ""
        selectors = [".post-content", "main", "article", ".content", ".blog-content", ".entry-content", "body"]

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
            source_url=url
        )

"""
backend/scrapers/generic_scraper.py

Generic scraper for any website content.
"""

import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from models import ContentItem
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class GenericScraper(BaseScraper):
    """
    Generic scraper that can extract content from any website.
    
    Attempts to find and extract meaningful content from web pages
    using common HTML patterns and heuristics.
    """
    
    def __init__(self, url: str):
        self.base_url = url
        self.domain = urlparse(url).netloc
        
    def discover_links(self):
        """
        For a generic scraper, we'll try to find internal links
        but default to just the provided URL if that fails.
        """
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            links = []
            # Try to find article links, blog post links, etc.
            for selector in [
                "a[href*='article']", "a[href*='post']", "a[href*='blog']",
                "a.post-link", "a.article-link", "article a", ".content a",
                "main a", "#content a"
            ]:
                found_links = soup.select(selector)
                for link in found_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        if self.domain in full_url and full_url not in links:
                            links.append(full_url)
            
            # If no specific links found, just return the base URL
            if not links:
                links = [self.base_url]
                
            # Limit to prevent overwhelming scraping
            return links[:20]
            
        except Exception as e:
            logger.warning(f"Could not discover links from {self.base_url}: {e}")
            return [self.base_url]
    
    def parse_page(self, url: str) -> ContentItem:
        """
        Parse any web page and extract meaningful content.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Extract author if available
            author = self._extract_author(soup)
            
            return ContentItem(
                title=title,
                content=content,
                content_type="web_content",
                source_url=url,
                author=author
            )
            
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return ContentItem(
                title=f"Failed to parse: {url}",
                content=f"Error occurred while parsing this page: {str(e)}",
                content_type="error",
                source_url=url,
                author=""
            )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title using multiple strategies."""
        # Try various title selectors
        for selector in ["h1", "title", ".title", ".page-title", "header h1", "article h1"]:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title:
                    return title
        
        return "Untitled Page"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information if available."""
        for selector in [
            ".author", ".by-author", "[rel='author']", ".post-author", 
            ".article-author", "meta[name='author']"
        ]:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    return element.get("content", "")
                else:
                    author = element.get_text(strip=True)
                    if author:
                        return author
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using heuristics."""
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "sidebar", "aside"]):
            element.decompose()
        
        # Try to find main content area
        content_element = None
        for selector in [
            "article", "main", ".content", ".post-content", ".article-content",
            ".entry-content", "#content", ".main-content", ".post-body"
        ]:
            element = soup.select_one(selector)
            if element:
                content_element = element
                break
        
        # If no specific content area found, use body but filter out navigation
        if not content_element:
            content_element = soup.find("body")
            if content_element:
                # Remove likely navigation and sidebar elements
                for unwanted in content_element.find_all(["nav", "aside", "footer", "header"]):
                    unwanted.decompose()
        
        if content_element:
            # Convert to markdown
            html_content = str(content_element)
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0
            h.unicode_snob = True
            h.escape_snob = True
            markdown = h.handle(html_content)
            # Clean up and normalize whitespace while preserving structure
            content = markdown.strip()
            # Replace multiple consecutive newlines with double newlines for proper paragraphs
            import re
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
            # Ensure proper spacing after headers and lists
            content = re.sub(r'(#{1,6}[^\n]*)\n([^\n#])', r'\1\n\n\2', content)
            content = re.sub(r'(\*[^\n]*)\n([^\n\*\s])', r'\1\n\n\2', content)
            
            # If content is too short, try to get more text
            if len(content) < 100:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all(['p', 'div', 'span'])
                text_content = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        text_content.append(text)
                
                if text_content:
                    content = '\n\n'.join(text_content[:10])  # Limit to first 10 meaningful paragraphs
            
            return content if content else "Could not extract meaningful content from this page."
        
        return "Could not extract content from this page."

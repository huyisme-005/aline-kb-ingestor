
"""
backend/scrapers/generic_scraper.py

Generic scraper for any website content.
"""

import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from models import ContentItem
from urllib.parse import urljoin, urlparse
from utils.html2md import convert
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
        # Remove unwanted elements first
        for element in soup(["script", "style", "nav", "footer", "header", "sidebar", "aside", "noscript", "iframe", "form"]):
            element.decompose()
        
        # Try to find main content area with comprehensive selectors
        content_element = None
        selectors = [
            "article", "main", ".content", ".post-content", ".article-content",
            ".entry-content", "#content", ".main-content", ".post-body",
            ".guide-content", ".blog-content", ".text-content", ".markup",
            ".container", ".wrapper", ".page-content", ".body",
            "[role='main']", ".primary-content", ".article", ".post",
            ".section-content", ".chapter", ".documentation"
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                content_element = element
                break
        
        # If no specific content area found, use body but filter out navigation
        if not content_element:
            content_element = soup.find("body")
            if content_element:
                # Remove likely navigation and sidebar elements
                for unwanted in content_element.find_all(["nav", "aside", "footer", "header", "form", "button", "menu"]):
                    unwanted.decompose()
        
        content = ""
        
        if content_element:
            # First try: Convert HTML to markdown
            html_content = str(content_element)
            try:
                markdown = convert(html_content)
                content = markdown.strip()
            except Exception as e:
                logger.warning(f"Markdown conversion failed: {e}")
                content = ""
            
            # If markdown conversion didn't work or content is too short, extract text directly
            if not content or len(content) < 100:
                # Get all text content with better filtering
                text_elements = content_element.find_all(['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'section'])
                text_parts = []
                
                for elem in text_elements:
                    text = elem.get_text(strip=True)
                    # Filter out short text, navigation items, and common non-content text
                    if (text and len(text) > 20 and 
                        not any(skip in text.lower() for skip in [
                            'cookie', 'privacy', 'subscribe', 'newsletter', 'advertisement',
                            'sign up', 'log in', 'menu', 'search', 'share', 'follow',
                            'copyright', '©', 'all rights reserved'
                        ]) and
                        not text.isupper() and  # Skip all-caps headings/navigation
                        '.' in text):  # Prefer text with sentences
                        text_parts.append(text)
                
                if text_parts:
                    content = '\n\n'.join(text_parts[:30])  # Get more content
            
            # Ultimate fallback: just get all paragraph text
            if not content or len(content) < 50:
                paragraphs = soup.find_all(['p', 'div'])
                para_texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 30:  # Longer minimum for paragraphs
                        para_texts.append(text)
                
                if para_texts:
                    content = '\n\n'.join(para_texts[:15])
            
            # Ensure we have meaningful content
            if content and len(content) > 50:
                return content
            else:
                return f"Extracted limited content from page. Content length: {len(content)} characters."
        
        return "Could not extract content from this page."

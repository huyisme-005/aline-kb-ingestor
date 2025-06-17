"""
backend/scrapers/substack_scraper.py

Generic Substack scraper for any substack.com blog.
"""

import requests
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
from models import ContentItem
import logging

logger = logging.getLogger(__name__)

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
        super().__init__()
        self.base_url = base_url.rstrip('/')
        logger.info(f"Initialized SubstackScraper with base_url: {self.base_url}")

    def discover_links(self):
        """Fetch /archive and collect all post URLs."""
        try:
            archive_url = f"{self.base_url}/archive"
            logger.info(f"Fetching archive from: {archive_url}")
            
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            resp = requests.get(archive_url, headers=headers, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Try multiple selectors as Substack structure can vary
            post_links = []
            
            # Common Substack post link selectors
            selectors = [
                "a[href*='/p/']",  # Most common pattern
                ".post-preview-title a",
                ".post-title a",
                "h3 a[href*='/p/']",
                "h2 a[href*='/p/']",
                "a.post-preview-title"
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    logger.info(f"Found {len(links)} posts using selector: {selector}")
                    post_links = [a.get("href") for a in links if a.get("href")]
                    break
            
            if not post_links:
                logger.warning("No post links found with any selector")
                return []
            
            # Convert relative URLs to absolute
            absolute_links = []
            for link in post_links:
                if link.startswith('/'):
                    absolute_links.append(self.base_url + link)
                elif link.startswith('http'):
                    absolute_links.append(link)
                else:
                    absolute_links.append(f"{self.base_url}/{link}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in absolute_links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            logger.info(f"Discovered {len(unique_links)} unique post URLs")
            return unique_links[:20]  # Limit to first 20 posts to avoid overloading
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch archive page: {e}")
            return []
        except Exception as e:
            logger.error(f"Error discovering links: {e}")
            return []

    def parse_page(self, url: str) -> ContentItem:
        """Parse a Substack post into a ContentItem."""
        try:
            logger.info(f"Parsing page: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Extract title
            title = "Untitled"
            title_selectors = [
                "h1.post-title",
                "h1",
                ".post-title",
                "h1.entry-title",
                "[data-testid='post-title']"
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract content
            content = ""
            content_selectors = [
                ".post-content",
                ".markup",
                ".body",
                "[data-testid='post-content']",
                ".available-content",
                "article"
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    body_html = str(content_elem)
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    h.ignore_images = False
                    h.body_width = 0
                    h.unicode_snob = True
                    h.escape_snob = True
                    content = h.handle(body_html)
                    # Clean up formatting
                    import re
                    content = content.strip()
                    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
                    content = re.sub(r'(#{1,6}[^\n]*)\n([^\n#])', r'\1\n\n\2', content)
                    break
            
            if not content:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Extract author if available
            author = ""
            author_selectors = [
                ".author-name",
                ".byline-name",
                "[data-testid='author-name']",
                ".post-author"
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            logger.info(f"Successfully parsed: {title[:50]}...")
            
            return ContentItem(
                title=title,
                content=content,
                content_type="blog",
                source_url=url,
                author=author
            )
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {url}: {e}")
            # Return a minimal ContentItem for failed requests
            return ContentItem(
                title=f"Failed to fetch: {url}",
                content=f"Error fetching content: {str(e)}",
                content_type="blog",
                source_url=url,
                author=""
            )
        except Exception as e:
            logger.error(f"Error parsing page {url}: {e}")
            return ContentItem(
                title=f"Parse error: {url}",
                content=f"Error parsing content: {str(e)}",
                content_type="blog",
                source_url=url,
                author=""
            )
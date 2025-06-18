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
import re

logger = logging.getLogger(__name__)

class GenericScraper(BaseScraper):
    """
    Generic scraper that can extract content from any website.
    
    Attempts to find and extract meaningful content from web pages
    using comprehensive HTML patterns and heuristics.
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
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.base_url, timeout=15, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            links = []
            # Try to find article links, blog post links, etc.
            for selector in [
                "a[href*='article']", "a[href*='post']", "a[href*='blog']",
                "a.post-link", "a.article-link", "article a", ".content a",
                "main a", "#content a", ".entry-title a", ".post-title a",
                "h1 a", "h2 a", "h3 a", ".blog-post a", ".news-item a"
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
            return links[:25]
            
        except Exception as e:
            logger.warning(f"Could not discover links from {self.base_url}: {e}")
            return [self.base_url]
    
    def parse_page(self, url: str) -> ContentItem:
        """
        Parse any web page and extract meaningful content using comprehensive strategies.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            # Try multiple times with different approaches if needed
            response = None
            for attempt in range(2):
                try:
                    response = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
                    response.raise_for_status()
                    break
                except requests.exceptions.SSLError:
                    # Try without SSL verification as fallback
                    if attempt == 0:
                        response = requests.get(url, timeout=20, headers=headers, allow_redirects=True, verify=False)
                        response.raise_for_status()
                        break
                except:
                    if attempt == 1:
                        raise
            
            # Try different parsers if one fails
            soup = None
            for parser in ['html.parser', 'lxml', 'html5lib']:
                try:
                    soup = BeautifulSoup(response.text, parser)
                    break
                except:
                    continue
            
            if not soup:
                soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content using multiple strategies
            content = self._extract_content_comprehensive(soup)
            
            # If still no content, try one more aggressive approach
            if not content or len(content) < 50:
                content = self._extract_fallback_content(soup)
            
            # Extract author if available
            author = self._extract_author(soup)
            
            # Determine content_type
            content_type = "book" if ("book" in title.lower() or "book" in url.lower() or ".pdf" in url.lower()) else "web_content"

            return ContentItem(
                title=title,
                content=content,
                content_type=content_type,
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
        # Try various title selectors in order of preference
        title_selectors = [
            "h1.entry-title", "h1.post-title", "h1.article-title", 
            "h1", ".title", ".page-title", "header h1", "article h1",
            ".post-header h1", ".content-header h1", "title",
            "[property='og:title']", "[name='twitter:title']"
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    title = element.get("content", "")
                elif element.get("property") == "og:title":
                    title = element.get("content", "")
                elif element.get("name") == "twitter:title":
                    title = element.get("content", "")
                else:
                    title = element.get_text(strip=True)
                
                if title and len(title) > 2:
                    return title
        
        return "Untitled Page"
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information if available."""
        author_selectors = [
            ".author", ".by-author", "[rel='author']", ".post-author", 
            ".article-author", "meta[name='author']", ".byline",
            ".author-name", ".writer", ".contributor", ".post-byline"
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == "meta":
                    return element.get("content", "")
                else:
                    author = element.get_text(strip=True)
                    if author and len(author) < 100:  # Reasonable author name length
                        return author
        return ""
    
    def _extract_content_comprehensive(self, soup: BeautifulSoup) -> str:
        """Extract main content using comprehensive strategies."""
        # Clone soup to avoid modifying original
        working_soup = BeautifulSoup(str(soup), "html.parser")
        
        # Remove unwanted elements first
        unwanted_selectors = [
            "script", "style", "nav", "footer", "header", "sidebar", 
            "aside", "noscript", "iframe", "form", "button", "input",
            ".advertisement", ".ad", ".ads", ".promo", ".popup",
            ".cookie", ".newsletter", ".subscription", ".social-share",
            ".related-posts", ".comments", ".comment-form", ".navigation",
            ".menu", ".breadcrumb", ".share", ".social", ".widget",
            "[role='navigation']", "[role='banner']", "[role='contentinfo']"
        ]
        
        for selector in unwanted_selectors:
            try:
                elements = working_soup.select(selector)
                for element in elements:
                    element.decompose()
            except:
                pass
        
        # Strategy 1: Try JSON-LD structured data first
        content = self._extract_from_json_ld(working_soup)
        if content and len(content) > 200:
            return content
        
        # Strategy 2: Try to extract using readability heuristics
        content = self._extract_by_readability(working_soup)
        if content and len(content) > 200:
            return content
        
        # Strategy 3: Try common content selectors
        content = self._extract_by_selectors(working_soup)
        if content and len(content) > 100:
            return content
        
        # Strategy 4: Extract by analyzing text density
        content = self._extract_by_text_density(working_soup)
        if content and len(content) > 100:
            return content
        
        # Strategy 5: Fallback to paragraph extraction
        content = self._extract_paragraphs(working_soup)
        if content and len(content) > 50:
            return content
        
        # Strategy 6: Ultimate fallback - get all visible text
        content = self._extract_all_text(working_soup)
        if content and len(content) > 30:
            return content
        
        return "Could not extract meaningful content from this page."
    
    def _extract_from_json_ld(self, soup: BeautifulSoup) -> str:
        """Extract content from JSON-LD structured data."""
        try:
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        # Look for article content
                        if item.get('@type') in ['Article', 'NewsArticle', 'BlogPosting']:
                            content = item.get('articleBody', '')
                            if content and len(content) > 200:
                                return content
                            
                            # Try description as fallback
                            description = item.get('description', '')
                            if description and len(description) > 100:
                                return description
                except:
                    continue
        except:
            pass
        return ""
    
    def _extract_by_readability(self, soup: BeautifulSoup) -> str:
        """Extract content using readability-style heuristics."""
        # Look for elements with high text-to-tag ratio
        best_element = None
        best_score = 0
        
        for element in soup.find_all(['div', 'article', 'section', 'main']):
            text = element.get_text(strip=True)
            if len(text) < 100:
                continue
                
            # Calculate score based on text length and tag density
            tag_count = len(element.find_all())
            text_length = len(text)
            score = text_length / max(tag_count, 1)
            
            # Bonus for semantic elements
            if element.name in ['article', 'main']:
                score *= 1.5
            
            # Bonus for content-related classes/ids
            class_id = ' '.join(element.get('class', []) + [element.get('id', '')])
            if any(term in class_id.lower() for term in ['content', 'post', 'article', 'entry', 'body']):
                score *= 1.3
            
            if score > best_score:
                best_score = score
                best_element = element
        
        if best_element:
            try:
                html_content = str(best_element)
                return convert(html_content).strip()
            except:
                return best_element.get_text(strip=True)
        
        return ""
    
    def _extract_by_selectors(self, soup: BeautifulSoup) -> str:
        """Extract content using comprehensive selectors."""
        content_selectors = [
            # Article and main content
            "article", "main", "[role='main']",
            
            # Common content classes
            ".content", ".post-content", ".article-content", ".entry-content",
            ".main-content", ".post-body", ".article-body", ".story-body",
            
            # News and media specific
            ".story", ".article-text", ".news-content", ".media-story-body",
            ".story-content", ".article-wrap", ".news-story", 
            
            # Blog specific
            ".blog-content", ".post", ".entry", ".blog-post",
            
            # Documentation and guides
            ".guide-content", ".documentation", ".docs", ".manual",
            
            # Generic content containers
            "#content", "#main", ".page-content", ".primary-content",
            ".text-content", ".markup", ".prose", ".copy", ".editorial",
            
            # Layout containers that often contain content
            ".container .content", ".wrapper .content", ".layout-content",
            ".site-content", ".page-wrapper", ".content-wrapper",
            
            # Specific to some CMSs
            ".field-content", ".node-content", ".wysiwyg"
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Check if element has substantial content
                text = element.get_text(strip=True)
                if len(text) > 200:
                    try:
                        html_content = str(element)
                        content = convert(html_content).strip()
                        if content and len(content) > 100:
                            return content
                    except:
                        pass
                    
                    # Fallback to text extraction
                    return self._clean_text(text)
        
        return ""
    
    def _extract_by_text_density(self, soup: BeautifulSoup) -> str:
        """Extract content by finding areas with high text density."""
        # Find all container elements
        containers = soup.find_all(['div', 'section', 'article', 'main', 'body'])
        
        best_container = None
        best_density = 0
        
        for container in containers:
            # Calculate text density (text length / HTML length)
            text = container.get_text(strip=True)
            html = str(container)
            
            if len(text) < 200:
                continue
                
            density = len(text) / len(html)
            
            # Bonus for containers with many paragraphs
            paragraph_count = len(container.find_all('p'))
            if paragraph_count > 3:
                density *= (1 + paragraph_count * 0.1)
            
            if density > best_density:
                best_density = density
                best_container = container
        
        if best_container:
            try:
                html_content = str(best_container)
                return convert(html_content).strip()
            except:
                return self._clean_text(best_container.get_text(strip=True))
        
        return ""
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> str:
        """Extract all meaningful paragraphs."""
        # Look for paragraphs and other text containers
        text_elements = soup.find_all(['p', 'div', 'section', 'article', 'span', 'blockquote', 'li'])
        meaningful_text = []
        seen_text = set()
        
        for element in text_elements:
            text = element.get_text(strip=True)
            
            # Skip if we've seen this text before (avoid duplicates)
            if text in seen_text:
                continue
            
            # Filter criteria for meaningful content
            if (text and len(text) > 20 and 
                not self._is_navigation_text(text) and
                self._has_sentence_structure(text)):
                meaningful_text.append(text)
                seen_text.add(text)
        
        if meaningful_text:
            # Sort by length to prioritize longer, more substantial content
            meaningful_text.sort(key=len, reverse=True)
            return '\n\n'.join(meaningful_text[:30])
        
        return ""
    
    def _has_sentence_structure(self, text: str) -> bool:
        """Check if text has sentence-like structure."""
        # Look for sentence ending punctuation
        if any(char in text for char in '.!?'):
            return True
        
        # Look for multiple words and reasonable length
        words = text.split()
        if len(words) >= 5 and len(text) >= 50:
            return True
            
        return False
    
    def _extract_all_text(self, soup: BeautifulSoup) -> str:
        """Ultimate fallback - extract all visible text."""
        # Get all text, then filter
        all_text = soup.get_text(separator='\n', strip=True)
        lines = all_text.split('\n')
        
        meaningful_lines = []
        for line in lines:
            line = line.strip()
            if (line and len(line) > 20 and 
                not self._is_navigation_text(line)):
                meaningful_lines.append(line)
        
        if meaningful_lines:
            return '\n'.join(meaningful_lines[:100])
        
        return all_text[:2000] if all_text else ""
    
    def _is_navigation_text(self, text: str) -> bool:
        """Check if text is likely navigation/menu content."""
        nav_indicators = [
            'home', 'about', 'contact', 'menu', 'search', 'login', 'signup',
            'subscribe', 'newsletter', 'follow', 'share', 'tweet', 'facebook',
            'cookie', 'privacy', 'terms', 'copyright', '©', 'all rights reserved',
            'read more', 'continue reading', 'click here', 'learn more'
        ]
        
        text_lower = text.lower()
        
        # Check for navigation indicators
        nav_count = sum(1 for indicator in nav_indicators if indicator in text_lower)
        if nav_count > 2:
            return True
        
        # Check if text is too short or all caps (likely navigation)
        if len(text) < 10 or text.isupper():
            return True
        
        # Check if text lacks sentence structure
        if '.' not in text and '!' not in text and '?' not in text and len(text) < 100:
            return True
        
        return False
    
    def _extract_fallback_content(self, soup: BeautifulSoup) -> str:
        """Last resort content extraction - get any meaningful text."""
        try:
            # Remove all script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text from body or html
            body = soup.find('body') or soup
            text = body.get_text()
            
            # Split into lines and filter
            lines = text.split('\n')
            meaningful_lines = []
            
            for line in lines:
                line = line.strip()
                if (line and len(line) > 15 and 
                    not line.isdigit() and 
                    not self._is_navigation_text(line)):
                    meaningful_lines.append(line)
            
            if meaningful_lines:
                # Take the longest lines as they're likely content
                meaningful_lines.sort(key=len, reverse=True)
                return '\n\n'.join(meaningful_lines[:20])
            
            return text[:1000] if text else ""
        except:
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and format extracted text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common unwanted patterns
        text = re.sub(r'\[.*?\]', '', text)  # Remove [brackets]
        text = re.sub(r'\{.*?\}', '', text)  # Remove {braces}
        
        # Ensure proper line breaks for readability
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\n\2', text)
        
        return text.strip()

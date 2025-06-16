"""
@author Huy Le (huyisme-005)
@file backend/base_scraper.py

Abstract base class defining the scraper plugin interface.
"""

from abc import ABC, abstractmethod
from typing import List
from models import ContentItem

class BaseScraper(ABC):
    """
    BaseScraper: contract for all scraping plugins.

    Subclasses must implement:
    - discover_links(): list of URLs to parse
    - parse_page(url): returns a ContentItem for that URL
    """

    @abstractmethod
    def discover_links(self) -> List[str]:
        """
        Discover all source URLs to scrape.

        Returns:
            A list of full URLs as strings.
        """
        pass

    @abstractmethod
    def parse_page(self, url: str) -> ContentItem:
        """
        Fetches and parses a given URL into a ContentItem.

        Args:
            url: Full URL of the page to parse.

        Returns:
            A populated ContentItem.
        """
        pass

    def run(self, team_id: str) -> dict:
        """
        Execute full scrape: discover links + parse each.

        Args:
            team_id: The team/user ID to attach to each item.

        Returns:
            A dict matching the KBPayload model.
        """
        items = []
        for url in self.discover_links():
            try:
                item = self.parse_page(url)
                item.user_id = team_id
                items.append(item)
            except Exception as e:
                # Logging here if desired
                print(f"Error parsing {url}: {e}")
        return {"team_id": team_id, "items": [i.dict() for i in items]}

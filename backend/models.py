"""
@author Huy Le (huyisme-005)
@file backend/models.py

Defines the Pydantic data models for KB injection payloads.
"""

from pydantic import BaseModel, HttpUrl
from typing import Literal, Optional, List

class ContentItem(BaseModel):
    """
    Represents a single piece of content to ingest.

    Attributes:
        title: Human-readable title of the content.
        content: Full Markdown-formatted body text.
        content_type: One of the supported content types.
        source_url: (Optional) URL where the content originated.
        author: (Optional) Name of the content's author.
        user_id: (Optional) ID of the user/team owning this content.
    """
    title: str
    content: str
    content_type: Literal[
        "blog", "podcast_transcript", "call_transcript",
        "linkedin_post", "reddit_comment", "book", "other"
    ]
    source_url: Optional[HttpUrl] = None
    author: Optional[str] = ""
    user_id: Optional[str] = ""

class KBPayload(BaseModel):
    """
    Wrapper for a batch of ContentItems destined for the KB.

    Attributes:
        team_id: Identifier for the target team/user.
        items: List of ContentItem objects.
    """
    team_id: str
    items: List[ContentItem]

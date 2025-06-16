"""
@author HUy Le (huyisme-005)
backend/api/main.py

FastAPI application exposing ingestion endpoints for URLs and PDFs.
"""

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from scrapers.interviewing_blog import InterviewingBlogScraper
from scrapers.interviewing_topics import InterviewingTopicsScraper
from scrapers.interviewing_guides import InterviewingGuidesScraper
from scrapers.nil_mamano_dsa import NilMamanoDSAScraper
from importers.pdf_importer import extract_chapters
from api.tasks import ingest_payload

app = FastAPI(title="Aline KB Ingestor")

@app.post("/ingest/url", status_code=202)
async def ingest_url(
    team_id: str = Form(...),
    source_url: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    """
    Ingest a web page by URL.

    Chooses the appropriate scraper based on URL pattern,
    then queues a background job to persist the payload.

    Returns:
        JSON indicating queue status and item count.
    """
    if "interviewing.io/blog" in source_url:
        scraper = InterviewingBlogScraper()
    elif "interviewing.io/topics" in source_url:
        scraper = InterviewingTopicsScraper()
    elif "interviewing.io/learn" in source_url:
        scraper = InterviewingGuidesScraper()
    elif "nilmamano.com/blog/category/dsa" in source_url:
        scraper = NilMamanoDSAScraper()
    else:
        return {"error": "Unsupported URL"}

    payload = scraper.run(team_id)
    background_tasks.add_task(ingest_payload, payload)
    return {"status": "queued", "items": len(payload["items"])}

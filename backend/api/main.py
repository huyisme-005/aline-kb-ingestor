"""
@author HUy Le (huyisme-005)
backend/api/main.py

FastAPI application exposing ingestion endpoints for URLs and PDFs.
"""

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from backend.scrapers.interviewing_blog import InterviewingBlogScraper
from backend.scrapers.interviewing_topics import InterviewingTopicsScraper
from backend.scrapers.interviewing_guides import InterviewingGuidesScraper
from backend.scrapers.nil_mamano_dsa import NilMamanoDSAScraper
from backend.scrapers.substack_scraper import SubstackScraper
from backend.scrapers.google_drive_scraper import GoogleDriveScraper
from backend.scrapers.generic_scraper import GenericScraper
from backend.importers.pdf_importer import extract_chapters
from api.tasks import ingest_payload
import os
import tempfile
import logging
from urllib.parse import urlparse
import re
import json
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with root_path for Lambda
stage = os.environ.get('STAGE', 'dev')
root_path = f"/{stage}" if stage != 'dev' else ""

app = FastAPI(
    title="Aline KB Ingestor",
    description="A tool to ingest technical content into a JSON knowledgebase for AI comment generation",
    version="0.1.0",
    root_path=root_path
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

def get_scraper_for_url(url: str):
    """
    Determine the appropriate scraper based on URL pattern.
    Always instantiate with the url argument for consistency.
    """
    if "substack.com" in url:
        return SubstackScraper(url)
    if "interviewing.io/blog" in url:
        return InterviewingBlogScraper(url)
    if "interviewing.io/topics" in url:
        return InterviewingTopicsScraper(url)
    if "interviewing.io/learn" in url:
        return InterviewingGuidesScraper(url)
    if "nilmamano.com/blog/category/dsa" in url:
        return NilMamanoDSAScraper(url)
    if "drive.google.com/drive/folders" in url or "drive.google.com/file/d/" in url:
        return GoogleDriveScraper(url)
    return GenericScraper(url)

@app.post("/ingest/url")
async def ingest_url(
    team_id: str = Form(...),
    source_url: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    try:
        logger.info(f"Ingesting URL: {source_url} for team: {team_id}")
        # Validate URL format using regex
        url_pattern = re.compile(
            r'^(http|https)://[a-zA-Z0-9-._~%]+(?:\.[a-zA-Z0-9-._~%]+)+.*$', 
            re.IGNORECASE
        )
        if not url_pattern.match(source_url):
            raise HTTPException(status_code=400, detail="Invalid URL format. URL must include protocol (http/https) and a valid domain.")
        parsed_url = urlparse(source_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise HTTPException(status_code=400, detail="Invalid URL format. URL must include protocol (http/https)")
        # Determine scraper based on URL pattern
        scraper = get_scraper_for_url(source_url)
        # Initialize and run the scraper
        logger.info(f"Using scraper: {scraper.__class__.__name__}")
        payload = scraper.run(team_id)
        if not payload.get("items"):
            return JSONResponse(status_code=200, content={"team_id": team_id, "items": [], "message": "No content found to ingest", "source_url": source_url})
        # Queue background task for ingestion (optional)
        if background_tasks:
            background_tasks.add_task(ingest_payload, payload)
        logger.info(f"Successfully ingested {len(payload['items'])} items")
        return {"team_id": team_id, "items": payload["items"], "source_url": source_url, "message": f"Successfully ingested {len(payload['items'])} items"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed for {source_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/ingest/pdf")
async def ingest_pdf(
    team_id: str = Form(...),
    file: UploadFile = File(...),
    num_chapters: int = Form(None),
    background_tasks: BackgroundTasks = None
):
    # Validate and process the incoming PDF file
    try:
        logger.info(f"Ingesting PDF: {file.filename} for team: {team_id}")
        
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > 50:  # Size check
            raise HTTPException(status_code=400, detail=f"File too large: {file_size_mb:.1f}MB. Maximum size: 50MB")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            logger.info(f"Extracting {num_chapters} chapters from PDF.")
            items = extract_chapters(tmp_path, num_chapters)

            payload = {
                "team_id": team_id,
                "items": [item.dict() for item in items]
            }

            if not payload["items"]:
                return JSONResponse(status_code=200, content={"team_id": team_id, "items": [], "message": "No chapters found in PDF", "filename": file.filename})

            if background_tasks:
                background_tasks.add_task(ingest_payload, payload)

            logger.info(f"Successfully extracted {len(payload['items'])} chapters")
            return {"team_id": team_id, "items": payload["items"], "filename": file.filename, "message": f"Successfully extracted {len(payload['items'])} chapters"}

        finally:
            os.unlink(tmp_path)  # Clean up temporary file
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF ingestion failed for {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF ingestion failed: {str(e)}")

@app.get("/scrapers")
async def list_scrapers():
    """
    List all available scrapers and their supported URL patterns.
    
    Returns:
        Dictionary of available scrapers and their details.
    """
    scrapers_info = {
        "interviewing_blog": {
            "class": InterviewingBlogScraper,
            "pattern": "interviewing.io/blog",
            "description": "Scrapes content from interviewing.io blog.",
        },
        "interviewing_topics": {
            "class": InterviewingTopicsScraper,
            "pattern": "interviewing.io/topics",
            "description": "Scrapes information about interview topics from interviewing.io.",
        },
        "interviewing_guides": {
            "class": InterviewingGuidesScraper,
            "pattern": "interviewing.io/learn",
            "description": "Scrapes interview guide information.",
        },
        "nilmamano": {
            "class": NilMamanoDSAScraper,
            "pattern": "nilmamano.com/blog/category/dsa",
            "description": "Scrapes NIL Mamano DSA blog.",
        },
        "google_drive": {
            "class": GoogleDriveScraper,
            "pattern": "drive.google.com",
            "description": "Scrapes content from Google Drive.",
        },
        "generic": {
            "class": GenericScraper,
            "pattern": "*",
            "description": "Generic scraper for any website.",
        },
        "substack": {
            "class": SubstackScraper,
            "pattern": "*.substack.com",
            "description": "Scrapes content from Substack publications.",
        },
    }
    return {"scrapers": scrapers_info, "total_scrapers": len(scrapers_info)}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "aline-kb-ingestor",
                "stage": os.environ.get('STAGE', 'dev')
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Aline KB Ingestor API",
        "docs": "/docs",
        "health": "/health",
        "stage": os.environ.get('STAGE', 'dev')
    }

# Create handler for AWS Lambda
handler = Mangum(app, lifespan="off")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
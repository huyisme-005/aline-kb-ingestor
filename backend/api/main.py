from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import BaseModel
from urllib.parse import urlparse
import json
import logging
import os
import re
from typing import Optional, List, Dict, Any

from backend.importers.pdf_importer import extract_chapters
from backend.scrapers.generic_scraper import GenericScraper
from backend.scrapers.google_drive_scraper import GoogleDriveScraper
from backend.scrapers.interviewing_blog import InterviewingBlogScraper
from backend.scrapers.interviewing_guides import InterviewingGuidesScraper
from backend.scrapers.interviewing_topics import InterviewingTopicsScraper
from backend.scrapers.nil_mamano_dsa import NilMamanoDSABlogScraper
from backend.scrapers.substack_scraper import SubstackScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aline KB Ingestor API", version="1.0.0")

# More flexible CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Utility Functions ---

def get_scraper_for_url(url: str):
    if "interviewing.io/blog" in url:
        return InterviewingBlogScraper(url)
    if "interviewing.io/topics" in url:
        return InterviewingTopicsScraper(url)
    if "interviewing.io/guides" in url:
        return InterviewingGuidesScraper(url)
    if "nilmamano.com/blog/category/dsa" in url:
        return NilMamanoDSABlogScraper(url)
    if "drive.google.com" in url:
        return GoogleDriveScraper(url)
    if "substack.com" in url:
        return SubstackScraper(url)
    return GenericScraper(url)

# --- API Endpoints ---

@app.get("/")
async def root():
    logger.info("Root endpoint was called")
    return {"message": "Aline KB Ingestor API is running!"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint was called")
    return {"status": "healthy", "stage": os.getenv("STAGE", "dev")}

@app.post("/ingest")
async def ingest(
    team_id: str = Form("aline123"),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    logger.info(f"Ingest request for team '{team_id}' with url='{url}', file='{file.filename if file else None}'")

    try:
        if url:
            # --- URL Ingestion Logic ---
            logger.info(f"Handling URL ingestion for: {url}")
            url_pattern = re.compile(r'^(http|https)://[a-zA-Z0-9-._~%]+', re.IGNORECASE)
            if not url_pattern.match(url):
                raise HTTPException(status_code=400, detail="Invalid URL format.")

            scraper = get_scraper_for_url(url)
            logger.info(f"Using scraper: {scraper.__class__.__name__}")
            payload = scraper.run(team_id)

            if not payload.get("items"):
                return JSONResponse(status_code=200, content={"team_id": team_id, "items": [], "message": "No content found to ingest."})
            
            return {"team_id": team_id, "items": payload["items"], "message": f"Successfully ingested {len(payload['items'])} items."}

        elif file:
            # --- PDF File Ingestion Logic ---
            logger.info(f"Handling file upload: {file.filename}")
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are supported.")

            # Save file temporarily
            tmp_path = f"/tmp/{file.filename}"
            with open(tmp_path, "wb") as buffer:
                buffer.write(await file.read())

            try:
                items = extract_chapters(tmp_path)
                if not items:
                    return JSONResponse(status_code=200, content={"team_id": team_id, "items": [], "message": "No chapters found in PDF."})

                payload = {"team_id": team_id, "items": items}
                return {"team_id": team_id, "items": items, "message": f"Successfully extracted {len(items)} chapters."}
            finally:
                os.unlink(tmp_path)

        else:
            raise HTTPException(status_code=400, detail="No content provided. Please provide a 'url' or 'file'.")

    except HTTPException as he:
        logger.warning(f"HTTP exception during ingestion: {he.detail}")
        raise he
    except Exception as e:
        logger.exception("An unexpected error occurred during ingestion")
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")


# --- Lambda Handler Initialization ---

try:
    handler = Mangum(app, lifespan="off")
except Exception as e:
    logger.exception("Failed to initialize Mangum handler")
    def handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Internal Server Error: Failed to initialize application."})
        }
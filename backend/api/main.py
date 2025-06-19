"""
@author HUy Le (huyisme-005)
backend/api/main.py

FastAPI application exposing ingestion endpoints for URLs and PDFs.
"""

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from scrapers.interviewing_blog import InterviewingBlogScraper
from scrapers.interviewing_topics import InterviewingTopicsScraper
from scrapers.interviewing_guides import InterviewingGuidesScraper
from scrapers.nil_mamano_dsa import NilMamanoDSAScraper
from scrapers.substack_scraper import SubstackScraper
from scrapers.google_drive_scraper import GoogleDriveScraper
from scrapers.generic_scraper import GenericScraper
from importers.pdf_importer import extract_chapters
from api.tasks import ingest_payload
import os
import tempfile
import logging
from urllib.parse import urlparse  # Ensured urlparse is utilized
import re  # Utilized for URL validation in ingestion functions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aline KB Ingestor",
    description="A tool to ingest technical content into a JSON knowledgebase for AI comment generation",
    version="0.1.0"
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://0.0.0.0:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://0.0.0.0:3001", 
        "http://127.0.0.1:3001",
        "http://0.0.0.0:8080", 
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
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
    """
    Health check endpoint.
    
    Returns:
        API health status.
    """
    return {"status": "healthy", "service": "aline-kb-ingestor"}

@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Basic API information and available endpoints.
    """
    return {
        "message": "Aline KB Ingestor API",
        "version": "0.1.0",
        "status": "healthy",
        "description": "Now supports ANY website URL and ALL PDF types"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

# Add Mangum handler for AWS Lambda
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    # Mangum not available, create a dummy handler
    def handler(event, context):
        return {"statusCode": 500, "body": "Mangum not available"}
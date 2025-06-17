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
from importers.pdf_importer import extract_chapters
from api.tasks import ingest_payload
import os
import tempfile
import logging
from urllib.parse import urlparse

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
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",
        "http://localhost:8080",  # Alternative frontend port
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Supported URL patterns and their corresponding scrapers
URL_SCRAPER_MAP = {
    "interviewing.io/blog": InterviewingBlogScraper,
    "interviewing.io/topics": InterviewingTopicsScraper,
    "interviewing.io/learn": InterviewingGuidesScraper,
    "nilmamano.com/blog/category/dsa": NilMamanoDSAScraper,
}

def get_scraper_for_url(url: str):
    """
    Determine the appropriate scraper based on URL pattern.
    
    Args:
        url: The URL to check
        
    Returns:
        Scraper class if supported, None otherwise
    """
    for pattern, scraper_class in URL_SCRAPER_MAP.items():
        if pattern in url:
            return scraper_class
    return None

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
        "endpoints": {
            "ingest_url": "/ingest/url",
            "ingest_pdf": "/ingest/pdf",
            "health": "/health",
            "scrapers": "/scrapers"
        },
        "supported_sources": list(URL_SCRAPER_MAP.keys())
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        API health status.
    """
    return {
        "status": "healthy", 
        "service": "aline-kb-ingestor",
        "supported_patterns": list(URL_SCRAPER_MAP.keys())
    }

@app.post("/ingest/url")
async def ingest_url(
    team_id: str = Form(...),
    source_url: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    """
    Ingest a web page by URL.

    Chooses the appropriate scraper based on URL pattern,
    then returns the payload directly (and optionally queues background job).

    Args:
        team_id: The team/user ID to attach to the content.
        source_url: The URL to scrape and ingest.
        background_tasks: FastAPI background tasks handler.

    Returns:
        JSON payload with team_id and scraped items.
    """
    try:
        logger.info(f"Ingesting URL: {source_url} for team: {team_id}")
        
        # Validate URL format
        try:
            parsed_url = urlparse(source_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid URL format. URL must include protocol (http/https)"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid URL format: {str(e)}"
            )
        
        # Determine scraper based on URL pattern
        scraper_class = get_scraper_for_url(source_url)
        
        if not scraper_class:
            supported_patterns = list(URL_SCRAPER_MAP.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported URL: {source_url}. Supported patterns: {', '.join(supported_patterns)}"
            )

        # Initialize and run scraper
        scraper = scraper_class()
        logger.info(f"Using scraper: {scraper_class.__name__}")
        
        payload = scraper.run(team_id)
        
        if not payload or not payload.get("items"):
            return JSONResponse(
                status_code=200,
                content={
                    "team_id": team_id, 
                    "items": [], 
                    "message": "No content found to ingest",
                    "source_url": source_url
                }
            )

        # Queue background task for ingestion (optional)
        if background_tasks:
            background_tasks.add_task(ingest_payload, payload)
        
        logger.info(f"Successfully ingested {len(payload['items'])} items")
        
        # Return the actual payload
        return {
            "team_id": team_id,
            "items": payload["items"],
            "source_url": source_url,
            "message": f"Successfully ingested {len(payload['items'])} items"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Ingestion failed for {source_url}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ingestion failed: {str(e)}"
        )

@app.post("/ingest/pdf")
async def ingest_pdf(
    team_id: str = Form(...),
    file: UploadFile = File(...),
    num_chapters: int = Form(8),
    background_tasks: BackgroundTasks = None
):
    """
    Ingest content from an uploaded PDF file.
    
    Args:
        team_id: The team/user ID to attach to the content.
        file: The uploaded PDF file.
        num_chapters: Number of chapters to extract (default: 8).
        background_tasks: FastAPI background tasks handler.
        
    Returns:
        JSON payload with team_id and extracted items.
    """
    try:
        logger.info(f"Ingesting PDF: {file.filename} for team: {team_id}")
        
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail="Only PDF files are supported"
            )
        
        # Check file size (optional - set a reasonable limit)
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > 50:  # 50MB limit
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.1f}MB. Maximum size: 50MB"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Extract chapters from PDF
            logger.info(f"Extracting {num_chapters} chapters from PDF")
            items = extract_chapters(tmp_path, num_chapters)
            
            # Create payload
            payload = {
                "team_id": team_id,
                "items": [item.dict() for item in items]
            }
            
            if not payload["items"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "team_id": team_id, 
                        "items": [], 
                        "message": "No chapters found in PDF",
                        "filename": file.filename
                    }
                )
            
            # Queue background task for ingestion (optional)
            if background_tasks:
                background_tasks.add_task(ingest_payload, payload)
            
            logger.info(f"Successfully extracted {len(payload['items'])} chapters")
            
            # Return the actual payload
            return {
                "team_id": team_id,
                "items": payload["items"],
                "filename": file.filename,
                "message": f"Successfully extracted {len(payload['items'])} chapters"
            }
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {tmp_path}: {e}")
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"PDF ingestion failed for {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"PDF ingestion failed: {str(e)}"
        )

@app.get("/scrapers")
async def list_scrapers():
    """
    List all available scrapers and their supported URL patterns.
    
    Returns:
        Dictionary of available scrapers and their details.
    """
    scrapers_info = {}
    
    for pattern, scraper_class in URL_SCRAPER_MAP.items():
        scrapers_info[pattern.replace(".", "_").replace("/", "_")] = {
            "class": scraper_class.__name__,
            "pattern": pattern,
            "description": f"Scrapes content from {pattern}",
            "example_url": f"https://{pattern}"
        }
    
    return {
        "scrapers": scrapers_info,
        "total_scrapers": len(URL_SCRAPER_MAP),
        "supported_patterns": list(URL_SCRAPER_MAP.keys())
    }
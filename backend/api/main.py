"""
@author HUy Le (huyisme-005)
backend/api/main.py

FastAPI application exposing ingestion endpoints for URLs and PDFs.
"""

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from scrapers.interviewing_blog import InterviewingBlogScraper
from scrapers.interviewing_topics import InterviewingTopicsScraper
from scrapers.interviewing_guides import InterviewingGuidesScraper
from scrapers.nil_mamano_dsa import NilMamanoDSAScraper
from importers.pdf_importer import extract_chapters
from api.tasks import ingest_payload
import os
import tempfile

app = FastAPI(
    title="Aline KB Ingestor",
    description="A tool to ingest technical content into a JSON knowledgebase for AI comment generation",
    version="0.1.0"
)

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
        "endpoints": {
            "ingest_url": "/ingest/url",
            "ingest_pdf": "/ingest/pdf",
            "health": "/health"
        },
        "supported_sources": [
            "interviewing.io/blog",
            "interviewing.io/topics", 
            "interviewing.io/learn",
            "nilmamano.com/blog/category/dsa"
        ]
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        API health status.
    """
    return {"status": "healthy", "service": "aline-kb-ingestor"}

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
        # Determine scraper based on URL pattern
        if "interviewing.io/blog" in source_url:
            scraper = InterviewingBlogScraper()
        elif "interviewing.io/topics" in source_url:
            scraper = InterviewingTopicsScraper()
        elif "interviewing.io/learn" in source_url:
            scraper = InterviewingGuidesScraper()
        elif "nilmamano.com/blog/category/dsa" in source_url:
            scraper = NilMamanoDSAScraper()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported URL: {source_url}. Supported domains: interviewing.io, nilmamano.com"
            )

        # Run scraper and get payload
        payload = scraper.run(team_id)
        
        if not payload["items"]:
            return JSONResponse(
                status_code=200,
                content={"team_id": team_id, "items": [], "message": "No content found to ingest"}
            )

        # Queue background task for ingestion (optional)
        if background_tasks:
            background_tasks.add_task(ingest_payload, payload)
        
        # Return the actual payload instead of just status
        return {
            "team_id": team_id,
            "items": payload["items"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

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
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Extract chapters from PDF
            items = extract_chapters(tmp_path, num_chapters)
            
            # Create payload
            payload = {
                "team_id": team_id,
                "items": [item.dict() for item in items]
            }
            
            if not payload["items"]:
                return JSONResponse(
                    status_code=200,
                    content={"team_id": team_id, "items": [], "message": "No chapters found in PDF"}
                )
            
            # Queue background task for ingestion (optional)
            if background_tasks:
                background_tasks.add_task(ingest_payload, payload)
            
            # Return the actual payload instead of just status
            return {
                "team_id": team_id,
                "items": payload["items"]
            }
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF ingestion failed: {str(e)}")

@app.get("/scrapers")
async def list_scrapers():
    """
    List all available scrapers and their supported URL patterns.
    
    Returns:
        Dictionary of available scrapers and their details.
    """
    return {
        "scrapers": {
            "interviewing_blog": {
                "class": "InterviewingBlogScraper",
                "pattern": "interviewing.io/blog",
                "description": "Scrapes blog posts from interviewing.io"
            },
            "interviewing_topics": {
                "class": "InterviewingTopicsScraper", 
                "pattern": "interviewing.io/topics",
                "description": "Scrapes company guides from interviewing.io"
            },
            "interviewing_guides": {
                "class": "InterviewingGuidesScraper",
                "pattern": "interviewing.io/learn", 
                "description": "Scrapes interview guides from interviewing.io"
            },
            "nil_mamano_dsa": {
                "class": "NilMamanoDSAScraper",
                "pattern": "nilmamano.com/blog/category/dsa",
                "description": "Scrapes DS&A posts from Nil Mamano's blog"
            }
        }
    }
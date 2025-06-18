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
from urllib.parse import urlparse
import re  # Keeping this import used

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
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "http://localhost:8080", 
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.post("/ingest/pdf")
async def ingest_pdf(
    team_id: str = Form(...),
    file: UploadFile = File(...),
    num_chapters: int = Form(None),
    background_tasks: BackgroundTasks = None
):
    """
    Ingest content from an uploaded PDF file.
    
    Args:
        team_id: The team/user ID to attach to the content.
        file: The uploaded PDF file.
        num_chapters: Number of chapters to extract (None for unlimited).
        background_tasks: FastAPI background tasks handler.
        
    Returns:
        JSON payload with team_id and extracted items.
    """
    try:
        logger.info(f"Ingesting PDF: {file.filename} for team: {team_id}")
        
        # Validate file type
        if not re.match(r".+\.pdf$", file.filename, re.IGNORECASE):
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
            chapters_msg = "all available chapters" if num_chapters is None else f"{num_chapters} chapters"
            logger.info(f"Extracting {chapters_msg} from PDF")
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
        "supported_patterns": get_supported_patterns()
    }

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
        "description": "Now supports ANY website URL and ALL PDF types",
        "endpoints": {
            "ingest_url": "/ingest/url",
            "ingest_pdf": "/ingest/pdf",
            "health": "/health",
            "scrapers": "/scrapers"
        },
        "supported_sources": "All websites and PDF files"
    }
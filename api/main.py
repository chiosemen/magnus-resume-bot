"""
FastAPI application for Magnus Resume Bot - Vercel compatible.

This module provides a REST API with:
- CORS support for cross-origin requests
- Job search, matching, and tracking endpoints
- Static file serving for dashboard
- Environment variable configuration
- Comprehensive error handling middleware
- Production-ready logging
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.models.database import get_database, db_session
    from src.models.job_scraper import JobScraper
except ImportError:
    logging.warning("Could not import local modules. Some features may be unavailable.")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
class Config:
    """Application configuration from environment variables."""

    APP_NAME: str = os.getenv("APP_NAME", "Magnus Resume Bot API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # Database
    DATABASE_PATH: Optional[str] = os.getenv("DATABASE_PATH")

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

    # File upload
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".doc", ".txt"]


config = Config()

# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="API for automated job searching, resume matching, and application tracking",
    debug=config.DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error Handling Middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """
    Global error handling middleware.

    Catches all exceptions and returns appropriate error responses.
    """
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(e) if config.DEBUG else "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Request/Response Models
class JobSearchRequest(BaseModel):
    """Request model for job search."""
    search_term: str = Field(..., min_length=1, max_length=200)
    location: str = Field(default="", max_length=200)
    sites: List[str] = Field(default=["indeed", "linkedin"])
    results_wanted: int = Field(default=10, ge=1, le=100)
    hours_old: int = Field(default=72, ge=1, le=720)

    @validator('sites')
    def validate_sites(cls, v):
        allowed_sites = ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"]
        for site in v:
            if site not in allowed_sites:
                raise ValueError(f"Invalid site: {site}. Allowed: {allowed_sites}")
        return v


class JobMatchRequest(BaseModel):
    """Request model for job matching."""
    job_id: int = Field(..., gt=0)
    resume_id: Optional[int] = Field(None, gt=0)
    resume_text: Optional[str] = None


class ApplicationCreateRequest(BaseModel):
    """Request model for creating application."""
    job_id: int = Field(..., gt=0)
    resume_id: Optional[int] = None
    notes: Optional[str] = None


class ApplicationUpdateRequest(BaseModel):
    """Request model for updating application."""
    status: Optional[str] = None
    notes: Optional[str] = None
    match_score: Optional[float] = Field(None, ge=0, le=100)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    timestamp: str


# Health Check Endpoint
@app.get("/", response_model=HealthResponse, tags=["Health"])
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns service status and version information.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": config.APP_VERSION
    }


# Job Search Endpoints
@app.post("/api/jobs/search", tags=["Jobs"])
async def search_jobs(request: JobSearchRequest):
    """
    Search for jobs across multiple platforms.

    Args:
        request: Job search parameters

    Returns:
        Dictionary with job listings from each platform
    """
    try:
        logger.info(f"Job search: {request.search_term} in {request.location}")

        scraper = JobScraper()
        results = await scraper.scrape_multiple_sites_async(
            sites=request.sites,
            search_term=request.search_term,
            location=request.location,
            results_wanted=request.results_wanted,
            hours_old=request.hours_old
        )

        # Convert DataFrames to dictionaries
        output = {}
        total_jobs = 0

        for site, df in results.items():
            if df is not None and not df.empty:
                jobs_list = df.to_dict('records')
                output[site] = {
                    "count": len(jobs_list),
                    "jobs": jobs_list
                }
                total_jobs += len(jobs_list)
            else:
                output[site] = {"count": 0, "jobs": []}

        return {
            "success": True,
            "total_jobs": total_jobs,
            "results": output,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs", tags=["Jobs"])
async def get_jobs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    company: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Retrieve jobs from database.

    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        company: Filter by company name
        location: Filter by location

    Returns:
        List of job records
    """
    try:
        with db_session() as db:
            query = "SELECT * FROM jobs WHERE 1=1"
            params = []

            if company:
                query += " AND company LIKE ?"
                params.append(f"%{company}%")

            if location:
                query += " AND location LIKE ?"
                params.append(f"%{location}%")

            query += " ORDER BY date_posted DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            jobs = db.execute_query(query, tuple(params))

            return {
                "success": True,
                "count": len(jobs),
                "jobs": [dict(job) for job in jobs],
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to retrieve jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}", tags=["Jobs"])
async def get_job(job_id: int):
    """
    Get a specific job by ID.

    Args:
        job_id: Job ID

    Returns:
        Job details
    """
    try:
        with db_session() as db:
            job = db.execute_query(
                "SELECT * FROM jobs WHERE id = ?",
                (job_id,),
                fetch_one=True
            )

            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            return {
                "success": True,
                "job": dict(job),
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Resume Endpoints
@app.post("/api/resumes/upload", tags=["Resumes"])
async def upload_resume(
    file: UploadFile = File(...),
    parse: bool = Form(default=True)
):
    """
    Upload a resume file.

    Args:
        file: Resume file (PDF, DOCX, DOC, TXT)
        parse: Whether to parse the resume content

    Returns:
        Resume ID and parsed content (if requested)
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {config.ALLOWED_EXTENSIONS}"
            )

        # Check file size
        content = await file.read()
        if len(content) > config.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {config.MAX_UPLOAD_SIZE} bytes"
            )

        # Save file
        upload_dir = Path(__file__).parent.parent / "data" / "resumes"
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / f"{datetime.now().timestamp()}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)

        # Store in database
        with db_session() as db:
            resume_id = db.execute_mutation(
                """
                INSERT INTO resumes (filename, file_path, file_type, uploaded_at)
                VALUES (?, ?, ?, ?)
                """,
                (file.filename, str(file_path), file_ext, datetime.utcnow())
            )

        logger.info(f"Resume uploaded: {file.filename} (ID: {resume_id})")

        return {
            "success": True,
            "resume_id": resume_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resumes", tags=["Resumes"])
async def get_resumes():
    """
    Get all uploaded resumes.

    Returns:
        List of resumes
    """
    try:
        with db_session() as db:
            resumes = db.execute_query("SELECT * FROM resumes ORDER BY uploaded_at DESC")

            return {
                "success": True,
                "count": len(resumes),
                "resumes": [dict(resume) for resume in resumes],
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to retrieve resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Application Tracking Endpoints
@app.post("/api/applications", tags=["Applications"])
async def create_application(request: ApplicationCreateRequest):
    """
    Create a new job application.

    Args:
        request: Application details

    Returns:
        Created application ID
    """
    try:
        with db_session() as db:
            # Verify job exists
            job = db.execute_query(
                "SELECT id FROM jobs WHERE id = ?",
                (request.job_id,),
                fetch_one=True
            )
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # Create application
            app_id = db.execute_mutation(
                """
                INSERT INTO applications (job_id, resume_id, notes, applied_at)
                VALUES (?, ?, ?, ?)
                """,
                (request.job_id, request.resume_id, request.notes, datetime.utcnow())
            )

            logger.info(f"Application created: ID {app_id} for job {request.job_id}")

            return {
                "success": True,
                "application_id": app_id,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications", tags=["Applications"])
async def get_applications(
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500)
):
    """
    Get all applications.

    Args:
        status: Filter by status
        limit: Maximum number of results

    Returns:
        List of applications
    """
    try:
        with db_session() as db:
            query = """
                SELECT
                    a.*,
                    j.title as job_title,
                    j.company as company,
                    j.location as location
                FROM applications a
                LEFT JOIN jobs j ON a.job_id = j.id
                WHERE 1=1
            """
            params = []

            if status:
                query += " AND a.status = ?"
                params.append(status)

            query += " ORDER BY a.applied_at DESC LIMIT ?"
            params.append(limit)

            applications = db.execute_query(query, tuple(params))

            return {
                "success": True,
                "count": len(applications),
                "applications": [dict(app) for app in applications],
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to retrieve applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/applications/{application_id}", tags=["Applications"])
async def update_application(application_id: int, request: ApplicationUpdateRequest):
    """
    Update an application.

    Args:
        application_id: Application ID
        request: Update fields

    Returns:
        Success status
    """
    try:
        with db_session() as db:
            # Build update query
            updates = []
            params = []

            if request.status:
                updates.append("status = ?")
                params.append(request.status)

            if request.notes is not None:
                updates.append("notes = ?")
                params.append(request.notes)

            if request.match_score is not None:
                updates.append("match_score = ?")
                params.append(request.match_score)

            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")

            params.append(application_id)
            query = f"UPDATE applications SET {', '.join(updates)} WHERE id = ?"

            rows_affected = db.execute_mutation(query, tuple(params))

            if rows_affected == 0:
                raise HTTPException(status_code=404, detail="Application not found")

            return {
                "success": True,
                "timestamp": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics Endpoint
@app.get("/api/stats", tags=["Statistics"])
async def get_statistics():
    """
    Get application statistics.

    Returns:
        Statistics summary
    """
    try:
        with db_session() as db:
            stats = {
                "total_jobs": db.execute_query(
                    "SELECT COUNT(*) as count FROM jobs",
                    fetch_one=True
                )["count"],
                "total_applications": db.execute_query(
                    "SELECT COUNT(*) as count FROM applications",
                    fetch_one=True
                )["count"],
                "total_resumes": db.execute_query(
                    "SELECT COUNT(*) as count FROM resumes",
                    fetch_one=True
                )["count"],
                "applications_by_status": {}
            }

            # Get status breakdown
            status_results = db.execute_query(
                "SELECT status, COUNT(*) as count FROM applications GROUP BY status"
            )

            for row in status_results:
                stats["applications_by_status"][row["status"]] = row["count"]

            return {
                "success": True,
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Static file serving (for dashboard)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/dashboard", tags=["Dashboard"])
    async def serve_dashboard():
        """Serve the dashboard HTML."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        raise HTTPException(status_code=404, detail="Dashboard not found")


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and resources on startup."""
    try:
        logger.info("Initializing application...")

        # Initialize database
        db = get_database(Path(config.DATABASE_PATH) if config.DATABASE_PATH else None)
        db.initialize_schema()

        logger.info("Application initialized successfully")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        logger.info("Shutting down application...")

        # Close database connections
        db = get_database()
        db.close()

        logger.info("Application shut down successfully")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

"""Models package for Magnus Resume Bot."""

from .database import Database, get_database, db_session
from .job_scraper import JobScraper, scrape_job

__all__ = [
    "Database",
    "get_database",
    "db_session",
    "JobScraper",
    "scrape_job"
]

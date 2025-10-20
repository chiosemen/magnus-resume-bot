"""
Job scraper module with rate limiting, exponential backoff, and async support.

This module provides a robust job scraping layer with:
- Exponential backoff retry logic
- Per-platform rate limiting
- Async/concurrent operations
- Comprehensive error handling
- Batch processing for efficiency
- Integration with jobspy library
"""

from __future__ import annotations

import asyncio
import time
import logging
from typing import List, Dict, Optional, Any, Callable, TYPE_CHECKING
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import random

if TYPE_CHECKING:
    import pandas as pd

try:
    from jobspy import scrape_jobs
    import pandas as pd
except ImportError:
    logging.warning("jobspy not installed. Install with: pip install jobspy")
    scrape_jobs = None
    pd = None  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobSite(Enum):
    """Supported job search platforms."""
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    ZIP_RECRUITER = "zip_recruiter"
    GLASSDOOR = "glassdoor"
    GOOGLE = "google"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration for a job site."""
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    min_delay_seconds: float = 1.0
    max_delay_seconds: float = 5.0


@dataclass
class RetryConfig:
    """Retry configuration with exponential backoff."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class RequestTracker:
    """Track requests for rate limiting."""
    minute_requests: List[datetime] = field(default_factory=list)
    hour_requests: List[datetime] = field(default_factory=list)
    last_request_time: Optional[datetime] = None


class RateLimiter:
    """
    Rate limiter with per-platform tracking.

    Implements token bucket algorithm with time-based windows.
    """

    def __init__(self):
        """Initialize rate limiter with platform-specific trackers."""
        self.trackers: Dict[str, RequestTracker] = {}
        self.configs: Dict[str, RateLimitConfig] = {
            JobSite.INDEED.value: RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                min_delay_seconds=2.0
            ),
            JobSite.LINKEDIN.value: RateLimitConfig(
                requests_per_minute=5,
                requests_per_hour=50,
                min_delay_seconds=3.0
            ),
            JobSite.ZIP_RECRUITER.value: RateLimitConfig(
                requests_per_minute=8,
                requests_per_hour=80,
                min_delay_seconds=2.0
            ),
            JobSite.GLASSDOOR.value: RateLimitConfig(
                requests_per_minute=6,
                requests_per_hour=60,
                min_delay_seconds=2.5
            ),
            JobSite.GOOGLE.value: RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                min_delay_seconds=1.5
            ),
        }

    def _get_tracker(self, platform: str) -> RequestTracker:
        """Get or create request tracker for platform."""
        if platform not in self.trackers:
            self.trackers[platform] = RequestTracker()
        return self.trackers[platform]

    def _clean_old_requests(
        self,
        requests: List[datetime],
        window_seconds: int
    ) -> List[datetime]:
        """Remove requests older than the time window."""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        return [req for req in requests if req > cutoff]

    async def acquire(self, platform: str) -> None:
        """
        Acquire permission to make a request (async).

        Blocks until rate limit allows the request.

        Args:
            platform: Job site platform name
        """
        config = self.configs.get(platform, RateLimitConfig())
        tracker = self._get_tracker(platform)

        while True:
            now = datetime.now()

            # Clean old requests
            tracker.minute_requests = self._clean_old_requests(
                tracker.minute_requests, 60
            )
            tracker.hour_requests = self._clean_old_requests(
                tracker.hour_requests, 3600
            )

            # Check rate limits
            minute_ok = len(tracker.minute_requests) < config.requests_per_minute
            hour_ok = len(tracker.hour_requests) < config.requests_per_hour

            # Check minimum delay since last request
            delay_ok = True
            if tracker.last_request_time:
                elapsed = (now - tracker.last_request_time).total_seconds()
                delay_ok = elapsed >= config.min_delay_seconds

            if minute_ok and hour_ok and delay_ok:
                # Grant permission
                tracker.minute_requests.append(now)
                tracker.hour_requests.append(now)
                tracker.last_request_time = now

                # Add random delay to avoid patterns
                jitter = random.uniform(0, 0.5)
                await asyncio.sleep(config.min_delay_seconds + jitter)
                break

            # Calculate wait time
            wait_times = []

            if not minute_ok and tracker.minute_requests:
                oldest = tracker.minute_requests[0]
                wait_times.append((oldest + timedelta(seconds=60) - now).total_seconds())

            if not hour_ok and tracker.hour_requests:
                oldest = tracker.hour_requests[0]
                wait_times.append((oldest + timedelta(seconds=3600) - now).total_seconds())

            if not delay_ok and tracker.last_request_time:
                wait_times.append(
                    config.min_delay_seconds - (now - tracker.last_request_time).total_seconds()
                )

            wait_time = max(wait_times) if wait_times else config.min_delay_seconds

            logger.info(f"Rate limit reached for {platform}, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

    def acquire_sync(self, platform: str) -> None:
        """
        Acquire permission to make a request (synchronous).

        Args:
            platform: Job site platform name
        """
        asyncio.run(self.acquire(platform))


class ExponentialBackoff:
    """Implement exponential backoff retry logic."""

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize exponential backoff.

        Args:
            config: Retry configuration
        """
        self.config = config or RetryConfig()

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )

        if self.config.jitter:
            # Add random jitter (0-50% of delay)
            delay += random.uniform(0, delay * 0.5)

        return delay

    async def retry_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry an async function with exponential backoff.

        Args:
            func: Async function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.config.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_retries} attempts failed")

        raise last_exception

    def retry_sync(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry a synchronous function with exponential backoff.

        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt < self.config.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.config.max_retries} attempts failed")

        raise last_exception


def retry_with_backoff(
    retry_config: Optional[RetryConfig] = None
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        retry_config: Retry configuration

    Example:
        @retry_with_backoff()
        async def fetch_jobs():
            return await scrape_jobs(...)
    """
    backoff = ExponentialBackoff(retry_config)

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await backoff.retry_async(func, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return backoff.retry_sync(func, *args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class JobScraper:
    """
    Main job scraper with rate limiting and retry logic.

    Provides high-level interface for scraping jobs from multiple platforms.
    """

    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize job scraper.

        Args:
            rate_limiter: Rate limiter instance
            retry_config: Retry configuration
        """
        self.rate_limiter = rate_limiter or RateLimiter()
        self.backoff = ExponentialBackoff(retry_config)

    async def scrape_jobs_async(
        self,
        site_name: str,
        search_term: str,
        location: str = "",
        results_wanted: int = 10,
        hours_old: int = 72,
        country_indeed: str = "USA",
        **kwargs
    ) -> Optional["pd.DataFrame"]:
        """
        Scrape jobs from a single platform (async).

        Args:
            site_name: Job site to scrape (indeed, linkedin, etc.)
            search_term: Job search query
            location: Job location
            results_wanted: Number of results to fetch
            hours_old: Maximum age of listings in hours
            country_indeed: Country for Indeed searches
            **kwargs: Additional arguments for jobspy

        Returns:
            DataFrame with job listings or None on failure
        """
        if scrape_jobs is None:
            logger.error("jobspy not installed")
            return None

        # Acquire rate limit permission
        await self.rate_limiter.acquire(site_name)

        async def _scrape():
            """Internal scrape function."""
            logger.info(
                f"Scraping {results_wanted} jobs from {site_name}: "
                f"'{search_term}' in '{location}'"
            )

            # jobspy is synchronous, run in executor
            loop = asyncio.get_event_loop()
            jobs_df = await loop.run_in_executor(
                None,
                lambda: scrape_jobs(
                    site_name=[site_name],
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    country_indeed=country_indeed,
                    **kwargs
                )
            )

            if jobs_df is not None and not jobs_df.empty:
                logger.info(f"Successfully scraped {len(jobs_df)} jobs from {site_name}")
                return jobs_df
            else:
                logger.warning(f"No jobs found on {site_name}")
                return None

        try:
            return await self.backoff.retry_async(_scrape)
        except Exception as e:
            logger.error(f"Failed to scrape {site_name}: {e}")
            return None

    def scrape_jobs_sync(
        self,
        site_name: str,
        search_term: str,
        location: str = "",
        results_wanted: int = 10,
        hours_old: int = 72,
        country_indeed: str = "USA",
        **kwargs
    ) -> Optional["pd.DataFrame"]:
        """
        Scrape jobs from a single platform (sync).

        Args:
            site_name: Job site to scrape
            search_term: Job search query
            location: Job location
            results_wanted: Number of results to fetch
            hours_old: Maximum age of listings in hours
            country_indeed: Country for Indeed searches
            **kwargs: Additional arguments for jobspy

        Returns:
            DataFrame with job listings or None on failure
        """
        return asyncio.run(
            self.scrape_jobs_async(
                site_name=site_name,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=country_indeed,
                **kwargs
            )
        )

    async def scrape_multiple_sites_async(
        self,
        sites: List[str],
        search_term: str,
        location: str = "",
        results_wanted: int = 10,
        hours_old: int = 72,
        **kwargs
    ) -> Dict[str, "pd.DataFrame"]:
        """
        Scrape jobs from multiple platforms concurrently.

        Args:
            sites: List of job sites to scrape
            search_term: Job search query
            location: Job location
            results_wanted: Number of results per site
            hours_old: Maximum age of listings
            **kwargs: Additional arguments for jobspy

        Returns:
            Dictionary mapping site names to DataFrames
        """
        tasks = [
            self.scrape_jobs_async(
                site_name=site,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                **kwargs
            )
            for site in sites
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for site, result in zip(sites, results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {site}: {result}")
            elif result is not None:
                output[site] = result

        return output

    def scrape_multiple_sites_sync(
        self,
        sites: List[str],
        search_term: str,
        location: str = "",
        results_wanted: int = 10,
        hours_old: int = 72,
        **kwargs
    ) -> Dict[str, "pd.DataFrame"]:
        """
        Scrape jobs from multiple platforms (sync).

        Args:
            sites: List of job sites to scrape
            search_term: Job search query
            location: Job location
            results_wanted: Number of results per site
            hours_old: Maximum age of listings
            **kwargs: Additional arguments

        Returns:
            Dictionary mapping site names to DataFrames
        """
        return asyncio.run(
            self.scrape_multiple_sites_async(
                sites=sites,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                **kwargs
            )
        )

    async def batch_scrape_async(
        self,
        queries: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> List[Optional["pd.DataFrame"]]:
        """
        Process multiple scrape queries in batches.

        Args:
            queries: List of query dictionaries with scrape parameters
            batch_size: Number of queries to process concurrently

        Returns:
            List of DataFrames (one per query)

        Example:
            queries = [
                {"site_name": "indeed", "search_term": "python", "location": "NYC"},
                {"site_name": "linkedin", "search_term": "data scientist", "location": "SF"},
            ]
        """
        results = []

        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} ({len(batch)} queries)")

            tasks = [self.scrape_jobs_async(**query) for query in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch query failed: {result}")
                    results.append(None)
                else:
                    results.append(result)

            # Delay between batches
            if i + batch_size < len(queries):
                await asyncio.sleep(2.0)

        return results

    def batch_scrape_sync(
        self,
        queries: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> List[Optional["pd.DataFrame"]]:
        """
        Process multiple scrape queries in batches (sync).

        Args:
            queries: List of query dictionaries
            batch_size: Batch size

        Returns:
            List of DataFrames
        """
        return asyncio.run(self.batch_scrape_async(queries, batch_size))


# Convenience functions
def scrape_job(
    site_name: str,
    search_term: str,
    location: str = "",
    results_wanted: int = 10,
    **kwargs
) -> Optional["pd.DataFrame"]:
    """
    Convenience function to scrape a single site.

    Args:
        site_name: Job site to scrape
        search_term: Search query
        location: Location
        results_wanted: Number of results
        **kwargs: Additional arguments

    Returns:
        DataFrame with results
    """
    scraper = JobScraper()
    return scraper.scrape_jobs_sync(
        site_name=site_name,
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        **kwargs
    )
if not jobs or len(jobs) == 0:
    print('[WARN] JobScraper: Fallback to mock data (scraping failed or empty results)')
    jobs = [
        {
            "title": "Scrum Master",
            "company": "TechCorp",
            "location": "Remote",
            "source": "MockDB",
            "posted_at": "2025-10-20",
            "url": "https://techcorp.com/jobs/scrum-master"
        },
        {
            "title": "Agile Coach",
            "company": "Velocity Labs",
            "location": "New York, NY",
            "source": "MockDB",
            "posted_at": "2025-10-19",
            "url": "https://velocitylabs.com/jobs/agile-coach"
        }
    ]
"""
Thread-safe SQLite database management module with connection pooling.

This module provides a robust database layer with:
- Thread-safe connection management
- Connection pooling for performance
- Context managers for safe resource handling
- Automatic schema creation and migration
- Performance indices
- Cross-platform path handling
"""

import sqlite3
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Any, List, Tuple
from queue import Queue, Empty
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionPool:
    """Thread-safe connection pool for SQLite database."""

    def __init__(self, database_path: Path, pool_size: int = 5):
        """
        Initialize connection pool.

        Args:
            database_path: Path to SQLite database file
            pool_size: Maximum number of connections in pool
        """
        self.database_path = database_path
        self.pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Create initial pool of connections."""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
        logger.info(f"Initialized connection pool with {self.pool_size} connections")

    def _create_connection(self) -> sqlite3.Connection:
        """
        Create a new database connection with optimizations.

        Returns:
            Configured SQLite connection
        """
        conn = sqlite3.connect(
            str(self.database_path),
            check_same_thread=False,
            timeout=30.0
        )
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Use WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        # Optimize for performance
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        # Return rows as dictionaries
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool as a context manager.

        Yields:
            SQLite connection from pool

        Example:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM jobs")
        """
        conn = None
        try:
            # Try to get connection from pool with timeout
            conn = self._pool.get(timeout=10.0)
            yield conn
        except Empty:
            # If pool is exhausted, create temporary connection
            logger.warning("Connection pool exhausted, creating temporary connection")
            conn = self._create_connection()
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    # Try to return connection to pool
                    self._pool.put_nowait(conn)
                except:
                    # If pool is full, close the connection
                    conn.close()

    def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        logger.info("Closed all database connections")


class Database:
    """Main database manager with schema management and query methods."""

    # Thread-local storage for connection pool
    _local = threading.local()
    _pool: Optional[ConnectionPool] = None
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            # Default to data directory in project root
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
            try:
                data_dir.mkdir(exist_ok=True)
            except (OSError, PermissionError):
                # On read-only filesystems (like Vercel), use /tmp
                data_dir = Path("/tmp")
            db_path = data_dir / "magnus_resume_bot.db"

        self.db_path = Path(db_path)
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Ensure database file and directory exist."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            # On read-only filesystems (like Vercel), /tmp is writable
            logger.warning(f"Could not create directory {self.db_path.parent}: {e}")

        if not self.db_path.exists():
            logger.info(f"Creating new database at {self.db_path}")

    def get_pool(self) -> ConnectionPool:
        """
        Get or create connection pool (singleton pattern).

        Returns:
            Connection pool instance
        """
        if Database._pool is None:
            with Database._lock:
                if Database._pool is None:
                    Database._pool = ConnectionPool(self.db_path)
        return Database._pool

    @contextmanager
    def get_connection(self):
        """
        Get a database connection as a context manager.

        Yields:
            SQLite connection
        """
        pool = self.get_pool()
        with pool.get_connection() as conn:
            yield conn

    def initialize_schema(self) -> None:
        """Create database schema with all required tables and indices."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    job_type TEXT,
                    date_posted DATE,
                    job_url TEXT UNIQUE,
                    description TEXT,
                    salary_min REAL,
                    salary_max REAL,
                    currency TEXT,
                    site TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create resumes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_path TEXT UNIQUE NOT NULL,
                    file_type TEXT NOT NULL,
                    content TEXT,
                    parsed_data TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    resume_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    match_score REAL,
                    notes TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL
                )
            """)

            # Create job_skills table for extracted skills
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    skill TEXT NOT NULL,
                    importance TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
                )
            """)

            # Create performance indices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_company
                ON jobs(company)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_location
                ON jobs(location)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_date_posted
                ON jobs(date_posted DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_title
                ON jobs(title)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_applications_status
                ON applications(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_applications_job_id
                ON applications(job_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_skills_job_id
                ON job_skills(job_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_skills_skill
                ON job_skills(skill)
            """)

            conn.commit()
            logger.info("Database schema initialized successfully")

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False
    ) -> Any:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: If True, return single row; otherwise return all rows

        Returns:
            Query results as Row objects or list of Row objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())

            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()

    def execute_mutation(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            ID of last inserted row or number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """
        Execute a query multiple times with different parameters.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def close(self) -> None:
        """Close all database connections."""
        if Database._pool:
            Database._pool.close_all()
            Database._pool = None


# Global database instance
_db_instance: Optional[Database] = None
_db_lock = threading.Lock()


def get_database(db_path: Optional[Path] = None) -> Database:
    """
    Get or create global database instance (singleton).

    Args:
        db_path: Path to database file

    Returns:
        Database instance
    """
    global _db_instance

    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = Database(db_path)
                _db_instance.initialize_schema()

    return _db_instance


# Convenience context manager for queries
@contextmanager
def db_session(db_path: Optional[Path] = None):
    """
    Context manager for database operations.

    Args:
        db_path: Optional path to database file

    Yields:
        Database instance

    Example:
        with db_session() as db:
            jobs = db.execute_query("SELECT * FROM jobs")
    """
    db = get_database(db_path)
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise

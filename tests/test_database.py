"""
Basic tests for database module.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.database import Database, get_database


def test_database_initialization():
    """Test database can be initialized."""
    db = Database()
    assert db is not None
    assert db.db_path is not None
    print("✓ Database initialization test passed")


def test_database_schema():
    """Test database schema creation."""
    db = get_database()
    db.initialize_schema()

    # Check if tables exist
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row['name'] for row in cursor.fetchall()]

    expected_tables = ['jobs', 'resumes', 'applications', 'job_skills']
    for table in expected_tables:
        assert table in tables, f"Table {table} not found"

    print(f"✓ Database schema test passed - found tables: {', '.join(tables)}")


def test_database_connection_pool():
    """Test connection pool works."""
    db = get_database()
    pool = db.get_pool()
    assert pool is not None
    assert pool.pool_size > 0
    print("✓ Connection pool test passed")


if __name__ == "__main__":
    print("Running database tests...\n")
    test_database_initialization()
    test_database_schema()
    test_database_connection_pool()
    print("\n✓ All database tests passed!")

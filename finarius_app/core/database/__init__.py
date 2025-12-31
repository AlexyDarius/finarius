"""Database module for Finarius portfolio tracking application.

This module provides database connection management, schema initialization,
migration support, and utility functions for the SQLite database.
"""

from typing import Optional

from .connection import Database
from .schema import (
    create_accounts_table,
    create_transactions_table,
    create_prices_table,
    create_schema_version_table,
    create_all_tables,
)
from .migrations import (
    CURRENT_SCHEMA_VERSION,
    get_schema_version,
    set_schema_version,
    run_migrations,
)
from .utils import (
    get_db_path,
    backup_db,
    restore_db,
    vacuum_db,
    get_db_stats,
)

__all__ = [
    # Connection
    "Database",
    # Schema
    "create_accounts_table",
    "create_transactions_table",
    "create_prices_table",
    "create_schema_version_table",
    "create_all_tables",
    # Migrations
    "CURRENT_SCHEMA_VERSION",
    "get_schema_version",
    "set_schema_version",
    "run_migrations",
    # Utils
    "get_db_path",
    "backup_db",
    "restore_db",
    "vacuum_db",
    "get_db_stats",
    # Initialization
    "init_db",
    "close_db",
]


def init_db(db_path: Optional[str] = None) -> Database:
    """Initialize database and create all tables.

    This function creates the database file if it doesn't exist, sets up
    the schema version table, runs migrations, and creates all required tables.

    Args:
        db_path: Path to SQLite database file. Defaults to 'db.sqlite'.

    Returns:
        Database instance.

    Raises:
        sqlite3.Error: If database initialization fails.
    """
    import sqlite3
    import logging

    logger = logging.getLogger(__name__)

    db = Database(db_path)
    conn = db.get_connection()

    try:
        # Create schema_version table if it doesn't exist
        create_schema_version_table(conn)

        # Get current schema version
        current_version = get_schema_version(db)

        # Run migrations if needed
        if current_version < CURRENT_SCHEMA_VERSION:
            logger.info(
                f"Running migrations from version {current_version} to {CURRENT_SCHEMA_VERSION}"
            )
            run_migrations(db, current_version, CURRENT_SCHEMA_VERSION)

        # Create tables (idempotent - will not recreate if they exist)
        create_all_tables(conn)

        conn.commit()
        logger.info("Database initialized successfully")
        return db

    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error initializing database: {e}")
        raise


def close_db(db: Optional[Database] = None) -> None:
    """Close database connection.

    Args:
        db: Database instance. If None, closes the singleton instance.
    """
    if db:
        db.close()
    else:
        if Database._instance:
            Database._instance.close()
            Database._instance = None


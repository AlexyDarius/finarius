"""Database migration system module."""

import sqlite3
import logging
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .connection import Database

logger = logging.getLogger(__name__)

# Current database schema version
CURRENT_SCHEMA_VERSION = 1


def get_schema_version(db: "Database") -> int:
    """Get current database schema version.

    Args:
        db: Database instance.

    Returns:
        Current schema version, or 0 if not set.
    """
    try:
        row = db.fetchone("SELECT MAX(version) as version FROM schema_version")
        if row and row["version"] is not None:
            return row["version"]
        return 0
    except sqlite3.Error:
        return 0


def set_schema_version(db: "Database", version: int) -> None:
    """Set database schema version.

    Args:
        db: Database instance.
        version: Schema version number.
    """
    db.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (version, datetime.now().isoformat()),
    )


def run_migrations(db: "Database", from_version: int, to_version: int) -> None:
    """Run database migrations from one version to another.

    Args:
        db: Database instance.
        from_version: Current schema version.
        to_version: Target schema version.
    """
    from .schema import create_accounts_table, create_transactions_table, create_prices_table

    conn = db.get_connection()

    # Migration 1: Initial schema
    if from_version < 1 <= to_version:
        logger.info("Running migration 1: Initial schema")
        create_accounts_table(conn)
        create_transactions_table(conn)
        create_prices_table(conn)
        set_schema_version(db, 1)
        conn.commit()
        logger.info("Migration 1 completed")

    # Future migrations can be added here
    # if from_version < 2 <= to_version:
    #     logger.info("Running migration 2: ...")
    #     # Migration code here
    #     set_schema_version(db, 2)
    #     conn.commit()


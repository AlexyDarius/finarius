"""Database utility functions module."""

import sqlite3
import logging
import os
from typing import Optional, Dict, Any
import shutil

from .connection import Database

logger = logging.getLogger(__name__)


def get_db_path(db: Optional[Database] = None) -> str:
    """Get database file path.

    Args:
        db: Database instance. If None, uses singleton instance.

    Returns:
        Database file path.
    """
    if db:
        return db.db_path
    if Database._instance:
        return Database._instance.db_path
    return "db.sqlite"


def backup_db(db: Optional[Database] = None, backup_path: Optional[str] = None) -> str:
    """Create a backup of the database.

    Args:
        db: Database instance. If None, uses singleton instance.
        backup_path: Path for backup file. If None, generates timestamped name.

    Returns:
        Path to backup file.

    Raises:
        FileNotFoundError: If database file doesn't exist.
        IOError: If backup operation fails.
    """
    from datetime import datetime

    db_path = get_db_path(db)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"

    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    except IOError as e:
        logger.error(f"Error backing up database: {e}")
        raise


def restore_db(backup_path: str, db_path: Optional[str] = None) -> None:
    """Restore database from backup.

    Args:
        backup_path: Path to backup file.
        db_path: Path to restore to. If None, uses default path.

    Raises:
        FileNotFoundError: If backup file doesn't exist.
        IOError: If restore operation fails.
    """
    from . import init_db, close_db

    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    if db_path is None:
        db_path = get_db_path()

    try:
        # Close existing connection if any
        close_db()

        # Restore backup
        shutil.copy2(backup_path, db_path)
        logger.info(f"Database restored from: {backup_path}")

        # Reinitialize connection
        Database._instance = None
        init_db(db_path)

    except IOError as e:
        logger.error(f"Error restoring database: {e}")
        raise


def vacuum_db(db: Optional[Database] = None) -> None:
    """Optimize database by running VACUUM.

    Args:
        db: Database instance. If None, uses singleton instance.
    """
    try:
        if db:
            conn = db.get_connection()
        else:
            db = Database()
            conn = db.get_connection()

        conn.execute("VACUUM")
        conn.commit()
        logger.info("Database vacuum completed")
    except sqlite3.Error as e:
        logger.error(f"Error vacuuming database: {e}")
        raise


def get_db_stats(db: Optional[Database] = None) -> Dict[str, Any]:
    """Get database statistics.

    Args:
        db: Database instance. If None, uses singleton instance.

    Returns:
        Dictionary with database statistics.
    """
    from .migrations import get_schema_version

    if db is None:
        db = Database()

    stats: Dict[str, Any] = {}

    try:
        # Database file size
        db_path = get_db_path(db)
        if os.path.exists(db_path):
            stats["file_size_bytes"] = os.path.getsize(db_path)
            stats["file_size_mb"] = round(stats["file_size_bytes"] / (1024 * 1024), 2)

        # Table row counts
        conn = db.get_connection()
        stats["table_counts"] = {}

        for table in ["accounts", "transactions", "prices", "schema_version"]:
            try:
                row = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                stats["table_counts"][table] = row["count"] if row else 0
            except sqlite3.Error:
                stats["table_counts"][table] = 0

        # Schema version
        stats["schema_version"] = get_schema_version(db)

        # Database page count and size
        try:
            page_count = conn.execute("PRAGMA page_count").fetchone()
            page_size = conn.execute("PRAGMA page_size").fetchone()
            if page_count and page_size:
                stats["page_count"] = page_count[0]
                stats["page_size"] = page_size[0]
                stats["estimated_size_bytes"] = stats["page_count"] * stats["page_size"]
        except sqlite3.Error:
            pass

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        stats["error"] = str(e)

    return stats


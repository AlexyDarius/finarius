"""Database connection management module."""

import sqlite3
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager with singleton pattern.

    This class manages SQLite database connections, provides connection pooling,
    and handles database initialization and migrations.
    """

    _instance: Optional["Database"] = None
    _connection: Optional[sqlite3.Connection] = None
    _db_path: Optional[str] = None

    def __new__(cls, db_path: Optional[str] = None) -> "Database":
        """Create or return existing Database instance (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db_path = db_path or "db.sqlite"
        return cls._instance

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize Database instance.

        Args:
            db_path: Path to SQLite database file. Defaults to 'db.sqlite'.
        """
        if db_path:
            self._db_path = db_path
        if self._connection is None:
            self._connection = self._create_connection()

    def _create_connection(self) -> sqlite3.Connection:
        """Create and configure SQLite database connection.

        Returns:
            Configured SQLite connection with foreign keys enabled.

        Raises:
            sqlite3.Error: If connection cannot be established.
        """
        try:
            conn = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
                timeout=30.0,
            )
            conn.row_factory = sqlite3.Row
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Database connection established: {self._db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error creating database connection: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns:
            Active SQLite connection.

        Raises:
            sqlite3.Error: If connection is not available.
        """
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection

    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Cursor object.

        Raises:
            sqlite3.Error: If query execution fails.
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise

    def executemany(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute a SQL query multiple times with different parameters.

        Args:
            query: SQL query string.
            params_list: List of parameter tuples.

        Returns:
            Cursor object.

        Raises:
            sqlite3.Error: If query execution fails.
        """
        try:
            conn = self.get_connection()
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            raise

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a query and fetch one row.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Row object or None if no results.
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a query and fetch all rows.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            List of row objects.
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()

    @property
    def db_path(self) -> str:
        """Get database file path."""
        return self._db_path or "db.sqlite"


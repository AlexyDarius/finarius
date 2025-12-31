"""Tests for database module."""

import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
from finarius_app.core.database import (
    Database,
    init_db,
    close_db,
    get_db_path,
    backup_db,
    restore_db,
    vacuum_db,
    get_db_stats,
    get_schema_version,
    set_schema_version,
    run_migrations,
    CURRENT_SCHEMA_VERSION,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)
    # Clean up singleton
    Database._instance = None
    Database._connection = None


@pytest.fixture
def db(temp_db_path):
    """Create a database instance for testing."""
    Database._instance = None
    Database._connection = None
    db_instance = init_db(temp_db_path)
    yield db_instance
    close_db(db_instance)
    Database._instance = None
    Database._connection = None


class TestDatabase:
    """Test Database class."""

    def test_singleton_pattern(self, temp_db_path):
        """Test that Database uses singleton pattern."""
        Database._instance = None
        Database._connection = None

        db1 = Database(temp_db_path)
        db2 = Database(temp_db_path)

        assert db1 is db2
        assert db1._db_path == temp_db_path

        close_db(db1)
        Database._instance = None
        Database._connection = None

    def test_connection_creation(self, temp_db_path):
        """Test database connection creation."""
        Database._instance = None
        Database._connection = None

        db = Database(temp_db_path)
        conn = db.get_connection()

        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)

        # Test foreign keys are enabled
        result = conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1

        close_db(db)
        Database._instance = None
        Database._connection = None

    def test_execute_query(self, db):
        """Test executing a query."""
        db.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
        db.execute("INSERT INTO test (name) VALUES (?)", ("test_name",))

        result = db.fetchone("SELECT name FROM test WHERE id = 1")
        assert result is not None
        assert result["name"] == "test_name"

    def test_executemany(self, db):
        """Test executing a query multiple times."""
        db.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")

        params = [("name1",), ("name2",), ("name3",)]
        db.executemany("INSERT INTO test (name) VALUES (?)", params)

        results = db.fetchall("SELECT name FROM test ORDER BY id")
        assert len(results) == 3
        assert results[0]["name"] == "name1"
        assert results[1]["name"] == "name2"
        assert results[2]["name"] == "name3"

    def test_fetchone(self, db):
        """Test fetching one row."""
        db.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")
        db.execute("INSERT INTO test (name) VALUES (?)", ("test",))

        result = db.fetchone("SELECT name FROM test WHERE id = 1")
        assert result is not None
        assert result["name"] == "test"

        result = db.fetchone("SELECT name FROM test WHERE id = 999")
        assert result is None

    def test_fetchall(self, db):
        """Test fetching all rows."""
        db.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)")

        for i in range(5):
            db.execute("INSERT INTO test (name) VALUES (?)", (f"name{i}",))

        results = db.fetchall("SELECT name FROM test ORDER BY id")
        assert len(results) == 5
        for i, row in enumerate(results):
            assert row["name"] == f"name{i}"

    def test_close_connection(self, temp_db_path):
        """Test closing database connection."""
        Database._instance = None
        Database._connection = None

        db = Database(temp_db_path)
        conn = db.get_connection()
        assert conn is not None

        db.close()
        assert db._connection is None

        Database._instance = None
        Database._connection = None


class TestDatabaseInitialization:
    """Test database initialization."""

    def test_init_db_creates_file(self, temp_db_path):
        """Test that init_db creates database file."""
        Database._instance = None
        Database._connection = None

        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

        db = init_db(temp_db_path)
        assert os.path.exists(temp_db_path)

        close_db(db)
        Database._instance = None
        Database._connection = None

    def test_init_db_creates_tables(self, db):
        """Test that init_db creates all required tables."""
        # Check accounts table
        result = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
        )
        assert result is not None

        # Check transactions table
        result = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
        )
        assert result is not None

        # Check prices table
        result = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='prices'"
        )
        assert result is not None

        # Check schema_version table
        result = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        assert result is not None

    def test_init_db_idempotent(self, temp_db_path):
        """Test that init_db can be called multiple times safely."""
        Database._instance = None
        Database._connection = None

        db1 = init_db(temp_db_path)
        db2 = init_db(temp_db_path)

        # Should not raise errors
        assert db1 is not None
        assert db2 is not None

        close_db(db1)
        Database._instance = None
        Database._connection = None


class TestAccountsTable:
    """Test accounts table schema."""

    def test_accounts_table_structure(self, db):
        """Test accounts table has correct structure."""
        # Get table info
        columns = db.fetchall("PRAGMA table_info(accounts)")

        column_names = [col["name"] for col in columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "currency" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names

        # Check primary key
        pk_columns = [col for col in columns if col["pk"] == 1]
        assert len(pk_columns) == 1
        assert pk_columns[0]["name"] == "id"

        # Check NOT NULL constraints
        name_col = next(col for col in columns if col["name"] == "name")
        assert name_col["notnull"] == 1

        currency_col = next(col for col in columns if col["name"] == "currency")
        assert currency_col["notnull"] == 1

    def test_accounts_unique_constraint(self, db):
        """Test accounts table unique constraint on name."""
        db.execute("INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "USD"))

        # Try to insert duplicate name
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "EUR")
            )

    def test_accounts_indexes(self, db):
        """Test accounts table indexes."""
        indexes = db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='accounts'"
        )
        index_names = [idx["name"] for idx in indexes]

        assert "idx_accounts_id" in index_names
        assert "idx_accounts_name" in index_names

    def test_accounts_default_currency(self, db):
        """Test accounts table default currency."""
        db.execute("INSERT INTO accounts (name) VALUES (?)", ("Test Account",))

        result = db.fetchone("SELECT currency FROM accounts WHERE name = 'Test Account'")
        assert result is not None
        assert result["currency"] == "USD"


class TestTransactionsTable:
    """Test transactions table schema."""

    def test_transactions_table_structure(self, db):
        """Test transactions table has correct structure."""
        columns = db.fetchall("PRAGMA table_info(transactions)")

        column_names = [col["name"] for col in columns]
        assert "id" in column_names
        assert "date" in column_names
        assert "account_id" in column_names
        assert "type" in column_names
        assert "symbol" in column_names
        assert "qty" in column_names
        assert "price" in column_names
        assert "fee" in column_names
        assert "notes" in column_names
        assert "created_at" in column_names

    def test_transactions_check_constraint(self, db):
        """Test transactions table CHECK constraint on type."""
        # Create a test account
        db.execute("INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "USD"))
        account_id = db.fetchone("SELECT id FROM accounts WHERE name = 'Test Account'")["id"]

        # Valid types should work
        valid_types = ["BUY", "SELL", "DIVIDEND", "DEPOSIT", "WITHDRAW"]
        for txn_type in valid_types:
            db.execute(
                "INSERT INTO transactions (date, account_id, type) VALUES (?, ?, ?)",
                ("2024-01-01", account_id, txn_type),
            )

        # Invalid type should fail
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO transactions (date, account_id, type) VALUES (?, ?, ?)",
                ("2024-01-01", account_id, "INVALID"),
            )

    def test_transactions_foreign_key(self, db):
        """Test transactions table foreign key constraint."""
        # Try to insert transaction with non-existent account_id
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO transactions (date, account_id, type) VALUES (?, ?, ?)",
                ("2024-01-01", 999, "BUY"),
            )

        # Create account and insert transaction
        db.execute("INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "USD"))
        account_id = db.fetchone("SELECT id FROM accounts WHERE name = 'Test Account'")["id"]

        db.execute(
            "INSERT INTO transactions (date, account_id, type) VALUES (?, ?, ?)",
            ("2024-01-01", account_id, "BUY"),
        )

        # Verify transaction was created
        result = db.fetchone("SELECT * FROM transactions WHERE account_id = ?", (account_id,))
        assert result is not None

    def test_transactions_indexes(self, db):
        """Test transactions table indexes."""
        indexes = db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='transactions'"
        )
        index_names = [idx["name"] for idx in indexes]

        assert "idx_transactions_date" in index_names
        assert "idx_transactions_account_id" in index_names
        assert "idx_transactions_symbol" in index_names
        assert "idx_transactions_type" in index_names
        assert "idx_transactions_account_date" in index_names

    def test_transactions_default_fee(self, db):
        """Test transactions table default fee."""
        db.execute("INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "USD"))
        account_id = db.fetchone("SELECT id FROM accounts WHERE name = 'Test Account'")["id"]

        db.execute(
            "INSERT INTO transactions (date, account_id, type) VALUES (?, ?, ?)",
            ("2024-01-01", account_id, "BUY"),
        )

        result = db.fetchone("SELECT fee FROM transactions WHERE account_id = ?", (account_id,))
        assert result is not None
        assert result["fee"] == 0.0


class TestPricesTable:
    """Test prices table schema."""

    def test_prices_table_structure(self, db):
        """Test prices table has correct structure."""
        columns = db.fetchall("PRAGMA table_info(prices)")

        column_names = [col["name"] for col in columns]
        assert "symbol" in column_names
        assert "date" in column_names
        assert "close" in column_names
        assert "open" in column_names
        assert "high" in column_names
        assert "low" in column_names
        assert "volume" in column_names
        assert "created_at" in column_names

    def test_prices_primary_key(self, db):
        """Test prices table composite primary key."""
        # Insert a price
        db.execute(
            "INSERT INTO prices (symbol, date, close) VALUES (?, ?, ?)",
            ("AAPL", "2024-01-01", 150.0),
        )

        # Try to insert duplicate (same symbol and date)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO prices (symbol, date, close) VALUES (?, ?, ?)",
                ("AAPL", "2024-01-01", 151.0),
            )

        # Different date should work
        db.execute(
            "INSERT INTO prices (symbol, date, close) VALUES (?, ?, ?)",
            ("AAPL", "2024-01-02", 151.0),
        )

    def test_prices_indexes(self, db):
        """Test prices table indexes."""
        indexes = db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='prices'"
        )
        index_names = [idx["name"] for idx in indexes]

        assert "idx_prices_symbol" in index_names
        assert "idx_prices_date" in index_names
        assert "idx_prices_symbol_date" in index_names


class TestMigrationSystem:
    """Test database migration system."""

    def test_schema_version_table(self, db):
        """Test schema_version table exists and works."""
        # Check table exists
        result = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        assert result is not None

        # Check initial version
        version = get_schema_version(db)
        assert version == CURRENT_SCHEMA_VERSION

    def test_set_schema_version(self, db):
        """Test setting schema version."""
        set_schema_version(db, 2)
        version = get_schema_version(db)
        assert version == 2

    def test_migrations_run_on_init(self, temp_db_path):
        """Test that migrations run when initializing database."""
        Database._instance = None
        Database._connection = None

        # Remove schema_version table if it exists
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

        db = init_db(temp_db_path)
        version = get_schema_version(db)
        assert version == CURRENT_SCHEMA_VERSION

        close_db(db)
        Database._instance = None
        Database._connection = None


class TestDatabaseUtilities:
    """Test database utility functions."""

    def test_get_db_path(self, temp_db_path):
        """Test getting database path."""
        Database._instance = None
        Database._connection = None

        db = Database(temp_db_path)
        path = get_db_path(db)
        assert path == temp_db_path

        close_db(db)
        Database._instance = None
        Database._connection = None

    def test_backup_db(self, db, temp_db_path):
        """Test database backup."""
        # Insert some test data
        db.execute("INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "USD"))

        backup_path = backup_db(db)
        assert os.path.exists(backup_path)

        # Verify backup contains data
        import sqlite3

        backup_conn = sqlite3.connect(backup_path)
        result = backup_conn.execute("SELECT COUNT(*) FROM accounts").fetchone()
        assert result[0] > 0
        backup_conn.close()

        # Cleanup
        os.unlink(backup_path)

    def test_restore_db(self, db, temp_db_path):
        """Test database restore."""
        # Insert test data
        db.execute("INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "USD"))

        # Create backup
        backup_path = backup_db(db)

        # Delete original database
        close_db(db)
        Database._instance = None
        Database._connection = None
        os.unlink(temp_db_path)

        # Restore from backup
        restore_db(backup_path, temp_db_path)

        # Verify data was restored
        restored_db = Database(temp_db_path)
        result = restored_db.fetchone("SELECT COUNT(*) as count FROM accounts")
        assert result["count"] > 0

        close_db(restored_db)
        Database._instance = None
        Database._connection = None

        # Cleanup
        os.unlink(backup_path)

    def test_vacuum_db(self, db):
        """Test database vacuum."""
        # Should not raise errors
        vacuum_db(db)

    def test_get_db_stats(self, db):
        """Test getting database statistics."""
        # Insert some test data
        db.execute("INSERT INTO accounts (name, currency) VALUES (?, ?)", ("Test Account", "USD"))

        stats = get_db_stats(db)

        assert "file_size_bytes" in stats
        assert "table_counts" in stats
        assert "schema_version" in stats
        assert stats["table_counts"]["accounts"] > 0
        assert stats["schema_version"] == CURRENT_SCHEMA_VERSION

    def test_close_db(self, temp_db_path):
        """Test close_db function."""
        Database._instance = None
        Database._connection = None

        db = Database(temp_db_path)
        assert db._connection is not None

        close_db(db)
        assert db._connection is None

        Database._instance = None
        Database._connection = None


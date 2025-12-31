"""Database schema definition module."""

import sqlite3


def create_accounts_table(conn: sqlite3.Connection) -> None:
    """Create accounts table with constraints and indexes.

    Args:
        conn: SQLite connection.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            currency TEXT NOT NULL DEFAULT 'USD',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_accounts_id ON accounts(id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_accounts_name ON accounts(name)")


def create_transactions_table(conn: sqlite3.Connection) -> None:
    """Create transactions table with constraints and indexes.

    Args:
        conn: SQLite connection.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            account_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('BUY', 'SELL', 'DIVIDEND', 'DEPOSIT', 'WITHDRAW')),
            symbol TEXT,
            qty REAL,
            price REAL,
            fee REAL DEFAULT 0.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_symbol ON transactions(symbol)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_account_date ON transactions(account_id, date)"
    )


def create_prices_table(conn: sqlite3.Connection) -> None:
    """Create prices table with constraints and indexes.

    Args:
        conn: SQLite connection.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            close REAL NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            volume INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, date)
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices(symbol)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON prices(symbol, date DESC)")


def create_schema_version_table(conn: sqlite3.Connection) -> None:
    """Create schema_version table for tracking migrations.

    Args:
        conn: SQLite connection.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def create_all_tables(conn: sqlite3.Connection) -> None:
    """Create all database tables.

    Args:
        conn: SQLite connection.
    """
    create_schema_version_table(conn)
    create_accounts_table(conn)
    create_transactions_table(conn)
    create_prices_table(conn)


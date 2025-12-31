"""Query helper functions for Finarius models."""

from typing import Optional, List, Any
from datetime import date

from ..database import Database
from .account import Account
from .transaction import Transaction
from .price import Price


def get_account_by_id(account_id: int, db: Optional[Database] = None) -> Optional[Account]:
    """Get account by ID.

    Args:
        account_id: Account ID.
        db: Database instance. If None, creates a new instance.

    Returns:
        Account instance or None if not found.
    """
    if db is None:
        db = Database()

    result = db.fetchone("SELECT * FROM accounts WHERE id = ?", (account_id,))
    if result:
        return Account(
            name=result["name"],
            currency=result["currency"],
            account_id=result["id"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
        )
    return None


def get_account_by_name(name: str, db: Optional[Database] = None) -> Optional[Account]:
    """Get account by name.

    Args:
        name: Account name.
        db: Database instance. If None, creates a new instance.

    Returns:
        Account instance or None if not found.
    """
    if db is None:
        db = Database()

    result = db.fetchone("SELECT * FROM accounts WHERE name = ?", (name,))
    if result:
        return Account(
            name=result["name"],
            currency=result["currency"],
            account_id=result["id"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
        )
    return None


def get_all_accounts(db: Optional[Database] = None) -> List[Account]:
    """Get all accounts.

    Args:
        db: Database instance. If None, creates a new instance.

    Returns:
        List of Account instances.
    """
    if db is None:
        db = Database()

    results = db.fetchall("SELECT * FROM accounts ORDER BY name")
    return [
        Account(
            name=row["name"],
            currency=row["currency"],
            account_id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in results
    ]


def get_transaction_by_id(transaction_id: int, db: Optional[Database] = None) -> Optional[Transaction]:
    """Get transaction by ID.

    Args:
        transaction_id: Transaction ID.
        db: Database instance. If None, creates a new instance.

    Returns:
        Transaction instance or None if not found.
    """
    if db is None:
        db = Database()

    result = db.fetchone("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    if result:
        return Transaction.from_dict(dict(result))
    return None


def get_transactions_by_account(
    account_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Optional[Database] = None,
) -> List[Transaction]:
    """Get transactions for an account, optionally filtered by date range.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive). If None, no start limit.
        end_date: End date (inclusive). If None, no end limit.
        db: Database instance. If None, creates a new instance.

    Returns:
        List of Transaction instances.
    """
    if db is None:
        db = Database()

    query = "SELECT * FROM transactions WHERE account_id = ?"
    params: List[Any] = [account_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat() if isinstance(start_date, date) else str(start_date))
    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat() if isinstance(end_date, date) else str(end_date))

    query += " ORDER BY date DESC, id DESC"

    results = db.fetchall(query, tuple(params))
    return [Transaction.from_dict(dict(row)) for row in results]


def get_transactions_by_symbol(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Optional[Database] = None,
) -> List[Transaction]:
    """Get transactions for a symbol, optionally filtered by date range.

    Args:
        symbol: Stock symbol.
        start_date: Start date (inclusive). If None, no start limit.
        end_date: End date (inclusive). If None, no end limit.
        db: Database instance. If None, creates a new instance.

    Returns:
        List of Transaction instances.
    """
    if db is None:
        db = Database()

    query = "SELECT * FROM transactions WHERE symbol = ?"
    params: List[Any] = [symbol.upper()]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat() if isinstance(start_date, date) else str(start_date))
    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat() if isinstance(end_date, date) else str(end_date))

    query += " ORDER BY date DESC, id DESC"

    results = db.fetchall(query, tuple(params))
    return [Transaction.from_dict(dict(row)) for row in results]


def get_price(symbol: str, price_date: date, db: Optional[Database] = None) -> Optional[Price]:
    """Get price for symbol and date.

    Args:
        symbol: Stock symbol.
        price_date: Price date.
        db: Database instance. If None, creates a new instance.

    Returns:
        Price instance or None if not found.
    """
    if db is None:
        db = Database()

    date_str = price_date.isoformat() if isinstance(price_date, date) else str(price_date)
    result = db.fetchone(
        "SELECT * FROM prices WHERE symbol = ? AND date = ?",
        (symbol.upper(), date_str),
    )
    if result:
        return Price.from_dict(dict(result))
    return None


def get_prices(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Optional[Database] = None,
) -> List[Price]:
    """Get price range for symbol.

    Args:
        symbol: Stock symbol.
        start_date: Start date (inclusive). If None, no start limit.
        end_date: End date (inclusive). If None, no end limit.
        db: Database instance. If None, creates a new instance.

    Returns:
        List of Price instances, ordered by date ascending.
    """
    if db is None:
        db = Database()

    query = "SELECT * FROM prices WHERE symbol = ?"
    params: List[Any] = [symbol.upper()]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat() if isinstance(start_date, date) else str(start_date))
    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat() if isinstance(end_date, date) else str(end_date))

    query += " ORDER BY date ASC"

    results = db.fetchall(query, tuple(params))
    return [Price.from_dict(dict(row)) for row in results]


def get_latest_price(symbol: str, db: Optional[Database] = None) -> Optional[Price]:
    """Get most recent price for symbol.

    Args:
        symbol: Stock symbol.
        db: Database instance. If None, creates a new instance.

    Returns:
        Price instance or None if not found.
    """
    if db is None:
        db = Database()

    result = db.fetchone(
        "SELECT * FROM prices WHERE symbol = ? ORDER BY date DESC LIMIT 1",
        (symbol.upper(),),
    )
    if result:
        return Price.from_dict(dict(result))
    return None


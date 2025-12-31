"""Dividend analytics module.

This module handles calculation of dividend-related metrics including
dividend history, yield, and income.
"""

from typing import Dict, Optional, List, Any
from datetime import date
import logging

from ..database import Database
from ..prices.downloader import PriceDownloader
from ..models.queries import get_price
from ..engine.cash_flows import get_cash_flows
from ..engine.positions import get_positions

logger = logging.getLogger(__name__)


def get_dividend_history(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> List[Dict[str, Any]]:
    """Get all dividend transactions in date range.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        List of dividend dictionaries with date, symbol, amount, etc.
    """
    if db is None:
        from ..database import Database

        db = Database()

    cash_flows = get_cash_flows(account_id, start_date, end_date, db)
    dividends = [cf for cf in cash_flows if cf["type"] == "DIVIDEND"]

    return dividends


def calculate_dividend_yield(
    account_id: int,
    yield_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate dividend yield for portfolio.

    Dividend yield = Annual dividends / Portfolio value

    Args:
        account_id: Account ID.
        yield_date: Date to calculate yield.
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dividend yield as decimal (e.g., 0.03 for 3%).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    from datetime import timedelta
    from ..engine.portfolio_value import calculate_portfolio_value

    # Get dividends in last year
    one_year_ago = yield_date - timedelta(days=365)
    dividends = get_dividend_history(account_id, one_year_ago, yield_date, db)
    annual_dividends = sum(d["amount"] for d in dividends)

    # Get portfolio value
    portfolio_value = calculate_portfolio_value(
        account_id, yield_date, db, price_downloader
    )

    if portfolio_value == 0:
        return 0.0

    return annual_dividends / portfolio_value


def calculate_dividend_income(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> float:
    """Calculate total dividend income in date range.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Total dividend income.
    """
    if db is None:
        from ..database import Database

        db = Database()

    dividends = get_dividend_history(account_id, start_date, end_date, db)
    return sum(d["amount"] for d in dividends)


def get_dividend_by_symbol(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[str, float]:
    """Get dividend income broken down by symbol.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary mapping symbol -> dividend income.
    """
    if db is None:
        from ..database import Database

        db = Database()

    dividends = get_dividend_history(account_id, start_date, end_date, db)
    by_symbol: Dict[str, float] = {}

    for div in dividends:
        symbol = div.get("symbol")
        if symbol:
            symbol = symbol.upper()
            if symbol not in by_symbol:
                by_symbol[symbol] = 0.0
            by_symbol[symbol] += div["amount"]

    return by_symbol


def calculate_dividend_yield_by_symbol(
    symbol: str,
    account_id: int,
    yield_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate dividend yield for specific symbol.

    Args:
        symbol: Stock symbol.
        account_id: Account ID.
        yield_date: Date to calculate yield.
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dividend yield as decimal (e.g., 0.03 for 3%).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    from datetime import timedelta

    # Get dividends for this symbol in last year
    one_year_ago = yield_date - timedelta(days=365)
    dividends = get_dividend_history(account_id, one_year_ago, yield_date, db)
    symbol_dividends = [
        d for d in dividends if d.get("symbol", "").upper() == symbol.upper()
    ]
    annual_dividends = sum(d["amount"] for d in symbol_dividends)

    # Get position value
    positions = get_positions(account_id, yield_date, db)
    if symbol.upper() not in positions:
        return 0.0

    position = positions[symbol.upper()]
    qty = position["qty"]

    if qty <= 0:
        return 0.0

    # Get current price
    price_obj = get_price(symbol, yield_date, db)

    if price_obj is None and price_downloader:
        try:
            price_obj = price_downloader.download_price(symbol, yield_date)
        except Exception as e:
            logger.warning(
                f"Could not download price for {symbol} on {yield_date}: {e}"
            )

    if price_obj is None:
        return 0.0

    position_value = qty * price_obj.close

    if position_value == 0:
        return 0.0

    return annual_dividends / position_value


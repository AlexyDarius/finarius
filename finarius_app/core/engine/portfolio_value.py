"""Portfolio value calculation module.

This module handles calculation of portfolio values at specific dates
and over time, including getting prices and calculating total values.
"""

from typing import Dict, Optional, List
from datetime import date, timedelta
import logging

from ..database import Database
from ..prices.downloader import PriceDownloader
from ..models.queries import get_price, get_latest_price
from .positions import get_positions

logger = logging.getLogger(__name__)


def calculate_portfolio_value(
    account_id: int,
    value_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate portfolio value at date.

    Gets positions, retrieves prices for all symbols, and calculates
    total portfolio value.

    Args:
        account_id: Account ID.
        value_date: Date to calculate value.
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Total portfolio value.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    positions = get_positions(account_id, value_date, db)
    total_value = 0.0

    for symbol, position in positions.items():
        qty = position["qty"]
        if qty <= 0:
            continue

        # Try to get price from database first
        price_obj = get_price(symbol, value_date, db)

        # If not found and we have a downloader, try to download
        if price_obj is None and price_downloader:
            try:
                price_obj = price_downloader.download_price(symbol, value_date)
            except Exception as e:
                logger.warning(
                    f"Could not download price for {symbol} on {value_date}: {e}"
                )

        if price_obj is None:
            logger.warning(
                f"No price available for {symbol} on {value_date}, "
                f"using cost basis as value"
            )
            # Use cost basis if price not available
            total_value += position["cost_basis"]
        else:
            # Use market price
            total_value += qty * price_obj.close

    return total_value


def calculate_portfolio_value_over_time(
    account_id: int,
    start_date: date,
    end_date: date,
    frequency: str = "daily",
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Dict[date, float]:
    """Calculate portfolio value over time.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        frequency: Frequency of snapshots ('daily', 'weekly', 'monthly').
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> portfolio value.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    values: Dict[date, float] = {}
    current_date = start_date

    # Determine date increment based on frequency
    if frequency == "daily":
        delta = timedelta(days=1)
    elif frequency == "weekly":
        delta = timedelta(weeks=1)
    elif frequency == "monthly":
        # Approximate monthly (30 days)
        delta = timedelta(days=30)
    else:
        logger.warning(f"Unknown frequency '{frequency}', using daily")
        delta = timedelta(days=1)

    while current_date <= end_date:
        value = calculate_portfolio_value(
            account_id, current_date, db, price_downloader
        )
        values[current_date] = value
        current_date += delta

    return values


def get_portfolio_breakdown(
    account_id: int,
    breakdown_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Dict[str, Dict[str, float]]:
    """Get portfolio breakdown by symbol.

    Args:
        account_id: Account ID.
        breakdown_date: Date for breakdown.
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dictionary mapping symbol -> {
            'qty': float,
            'cost_basis': float,
            'current_value': float,
            'unrealized_gain': float
        }
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    positions = get_positions(account_id, breakdown_date, db)
    breakdown: Dict[str, Dict[str, float]] = {}

    for symbol, position in positions.items():
        qty = position["qty"]
        cost_basis = position["cost_basis"]

        if qty <= 0:
            continue

        # Get current price
        price_obj = get_price(symbol, breakdown_date, db)

        # If not found, try to download
        if price_obj is None and price_downloader:
            try:
                price_obj = price_downloader.download_price(symbol, breakdown_date)
            except Exception as e:
                logger.warning(
                    f"Could not download price for {symbol} on {breakdown_date}: {e}"
                )

        current_price = price_obj.close if price_obj else position["avg_price"]
        current_value = qty * current_price
        unrealized_gain = current_value - cost_basis

        breakdown[symbol] = {
            "qty": qty,
            "cost_basis": cost_basis,
            "current_value": current_value,
            "unrealized_gain": unrealized_gain,
        }

    return breakdown


"""Unrealized gains/losses calculation module.

This module handles calculation of unrealized gains and losses from current
positions by comparing market value to cost basis.
"""

from typing import Dict, Optional
from datetime import date
import logging

from ..database import Database
from ..prices.downloader import PriceDownloader
from ..models.queries import get_price
from ..engine.positions import get_positions

logger = logging.getLogger(__name__)


def calculate_unrealized_gains(
    account_id: int,
    gains_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> float:
    """Calculate unrealized gains/losses for account at date.

    Calculates unrealized PnL by comparing current market value
    of positions to their cost basis.

    Args:
        account_id: Account ID.
        gains_date: Date to calculate unrealized gains.
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Total unrealized gains (positive) or losses (negative).
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    positions = get_positions(account_id, gains_date, db)
    total_unrealized = 0.0

    for symbol, position in positions.items():
        qty = position["qty"]
        cost_basis = position["cost_basis"]

        if qty <= 0:
            continue

        # Get current market price
        price_obj = get_price(symbol, gains_date, db)

        if price_obj is None and price_downloader:
            try:
                price_obj = price_downloader.download_price(symbol, gains_date)
            except Exception as e:
                logger.warning(
                    f"Could not download price for {symbol} on {gains_date}: {e}"
                )

        if price_obj is None:
            # No price available, skip this position
            continue

        current_value = qty * price_obj.close
        unrealized = current_value - cost_basis
        total_unrealized += unrealized

    return total_unrealized


def get_unrealized_gains_by_symbol(
    account_id: int,
    gains_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Dict[str, float]:
    """Get unrealized gains/losses broken down by symbol.

    Args:
        account_id: Account ID.
        gains_date: Date to calculate unrealized gains.
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dictionary mapping symbol -> unrealized gain/loss.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    positions = get_positions(account_id, gains_date, db)
    gains_by_symbol: Dict[str, float] = {}

    for symbol, position in positions.items():
        qty = position["qty"]
        cost_basis = position["cost_basis"]

        if qty <= 0:
            continue

        price_obj = get_price(symbol, gains_date, db)

        if price_obj is None and price_downloader:
            try:
                price_obj = price_downloader.download_price(symbol, gains_date)
            except Exception as e:
                logger.warning(
                    f"Could not download price for {symbol} on {gains_date}: {e}"
                )

        if price_obj is None:
            continue

        current_value = qty * price_obj.close
        unrealized = current_value - cost_basis
        gains_by_symbol[symbol] = unrealized

    return gains_by_symbol


def get_unrealized_gains_history(
    account_id: int,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
    price_downloader: Optional[PriceDownloader] = None,
) -> Dict[date, float]:
    """Get unrealized gains history over time.

    Args:
        account_id: Account ID.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.
        price_downloader: PriceDownloader instance. If None, creates a new instance.

    Returns:
        Dictionary mapping date -> unrealized gains at that date.
    """
    if db is None:
        from ..database import Database

        db = Database()

    if price_downloader is None:
        from ..prices.downloader import PriceDownloader

        price_downloader = PriceDownloader(db=db)

    from datetime import timedelta

    history: Dict[date, float] = {}
    current_date = start_date

    while current_date <= end_date:
        unrealized = calculate_unrealized_gains(
            account_id, current_date, db, price_downloader
        )
        history[current_date] = unrealized
        current_date += timedelta(days=1)

    return history


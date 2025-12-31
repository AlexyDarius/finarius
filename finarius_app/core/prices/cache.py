"""Price caching utilities for price downloader."""

import logging
from typing import Optional, Dict, Any
from datetime import date, datetime, timedelta

from ..database import Database
from ..models.price import Price
from ..models.queries import get_price as get_price_from_db

logger = logging.getLogger(__name__)

# Default cache expiration: 1 day for historical prices, 1 hour for latest prices
CACHE_EXPIRATION_HISTORICAL = timedelta(days=1)
CACHE_EXPIRATION_LATEST = timedelta(hours=1)


def is_price_cached(
    symbol: str,
    price_date: date,
    db: Optional[Database] = None,
    max_age: Optional[timedelta] = None,
) -> bool:
    """Check if price is cached in database.

    Args:
        symbol: Stock symbol.
        price_date: Price date.
        db: Database instance. If None, creates a new instance.
        max_age: Maximum age of cached data. If None, uses default expiration.

    Returns:
        True if price is cached and not expired, False otherwise.
    """
    if db is None:
        db = Database()

    cached_price = get_price_from_db(symbol, price_date, db)

    if cached_price is None:
        return False

    # Check expiration if max_age is provided
    if max_age is not None and cached_price.created_at:
        try:
            created_at = datetime.fromisoformat(cached_price.created_at.replace("Z", "+00:00"))
            # Handle timezone-naive datetime
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=None)

            age = datetime.now() - created_at.replace(tzinfo=None)
            if age > max_age:
                logger.debug(
                    f"Cached price for {symbol} on {price_date} is expired (age: {age})"
                )
                return False
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error checking cache expiration: {e}")
            # If we can't parse the date, assume it's valid
            return True

    return True


def get_cached_price(
    symbol: str,
    price_date: date,
    db: Optional[Database] = None,
) -> Optional[Price]:
    """Get cached price from database.

    Args:
        symbol: Stock symbol.
        price_date: Price date.
        db: Database instance. If None, creates a new instance.

    Returns:
        Price instance if found, None otherwise.
    """
    if db is None:
        db = Database()

    return get_price_from_db(symbol, price_date, db)


def update_price_cache(
    symbol: str,
    price_date: date,
    price_data: Dict[str, Any],
    db: Optional[Database] = None,
) -> Price:
    """Update price cache in database.

    Args:
        symbol: Stock symbol.
        price_date: Price date.
        price_data: Dictionary with price data (close, open, high, low, volume).
        db: Database instance. If None, creates a new instance.

    Returns:
        Saved Price instance.
    """
    if db is None:
        db = Database()

    price = Price(
        symbol=symbol,
        date=price_date,
        close=price_data.get("close", price_data.get("Close", 0.0)),
        open_price=price_data.get("open", price_data.get("Open")),
        high=price_data.get("high", price_data.get("High")),
        low=price_data.get("low", price_data.get("Low")),
        volume=price_data.get("volume", price_data.get("Volume")),
    )

    price.save(db)
    logger.debug(f"Cached price: {symbol} on {price_date}")

    return price


def invalidate_price_cache(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Optional[Database] = None,
) -> int:
    """Invalidate cached prices for a symbol.

    Args:
        symbol: Stock symbol.
        start_date: Start date (inclusive). If None, invalidate all.
        end_date: End date (inclusive). If None, invalidate all.
        db: Database instance. If None, creates a new instance.

    Returns:
        Number of prices invalidated (deleted).
    """
    if db is None:
        db = Database()

    query = "DELETE FROM prices WHERE symbol = ?"
    params: list = [symbol.upper()]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat())
    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat())

    cursor = db.execute(query, tuple(params))
    count = cursor.rowcount
    logger.info(f"Invalidated {count} cached prices for {symbol}")
    return count


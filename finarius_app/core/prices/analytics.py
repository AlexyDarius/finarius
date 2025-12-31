"""Price analytics utilities for calculating returns and statistics."""

import logging
from typing import Optional, List, Dict, Any
from datetime import date, timedelta
import statistics

from ..database import Database
from ..models.queries import get_prices, get_latest_price

logger = logging.getLogger(__name__)


def get_price_history(
    symbol: str,
    days: int = 30,
    db: Optional[Database] = None,
) -> List[Dict[str, Any]]:
    """Get price history for a symbol.

    Args:
        symbol: Stock symbol.
        days: Number of days of history to retrieve.
        db: Database instance. If None, creates a new instance.

    Returns:
        List of dictionaries with price data, ordered by date ascending.
        Each dict contains: date, close, open, high, low, volume
    """
    if db is None:
        db = Database()

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    prices = get_prices(symbol, start_date, end_date, db)

    return [
        {
            "date": p.date.isoformat() if isinstance(p.date, date) else str(p.date),
            "close": p.close,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "volume": p.volume,
        }
        for p in prices
    ]


def calculate_returns(
    symbol: str,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[str, Any]:
    """Calculate returns for a symbol over a date range.

    Args:
        symbol: Stock symbol.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary with return calculations:
        - absolute_return: float - Absolute price change
        - percentage_return: float - Percentage return
        - start_price: float - Price at start date
        - end_price: float - Price at end date
        - days: int - Number of days
    """
    if db is None:
        db = Database()

    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")

    # Get prices at start and end dates
    prices = get_prices(symbol, start_date, end_date, db)

    if len(prices) < 2:
        # Try to get closest available prices
        start_price_obj = get_prices(symbol, None, start_date, db)
        end_price_obj = get_prices(symbol, end_date, None, db)

        if not start_price_obj:
            raise ValueError(f"No price data available for {symbol} at or before {start_date}")
        if not end_price_obj:
            raise ValueError(f"No price data available for {symbol} at or after {end_date}")

        start_price = start_price_obj[-1].close if start_price_obj else None
        end_price = end_price_obj[0].close if end_price_obj else None
    else:
        # Use first and last prices
        start_price = prices[0].close
        end_price = prices[-1].close

    if start_price is None or end_price is None:
        raise ValueError(f"Insufficient price data for {symbol}")

    if start_price == 0:
        raise ValueError(f"Start price is zero for {symbol}")

    absolute_return = end_price - start_price
    percentage_return = (absolute_return / start_price) * 100.0
    days = (end_date - start_date).days

    return {
        "symbol": symbol.upper(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "start_price": start_price,
        "end_price": end_price,
        "absolute_return": absolute_return,
        "percentage_return": percentage_return,
        "days": days,
    }


def get_price_statistics(
    symbol: str,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[str, Any]:
    """Get price statistics for a symbol over a date range.

    Args:
        symbol: Stock symbol.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary with statistics:
        - min: float - Minimum price
        - max: float - Maximum price
        - mean: float - Average price
        - median: float - Median price
        - std_dev: float - Standard deviation
        - count: int - Number of data points
    """
    if db is None:
        db = Database()

    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")

    prices = get_prices(symbol, start_date, end_date, db)

    if not prices:
        raise ValueError(f"No price data available for {symbol} between {start_date} and {end_date}")

    close_prices = [p.close for p in prices if p.close is not None]

    if not close_prices:
        raise ValueError(f"No valid price data for {symbol}")

    stats = {
        "symbol": symbol.upper(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "min": min(close_prices),
        "max": max(close_prices),
        "mean": statistics.mean(close_prices),
        "median": statistics.median(close_prices),
        "count": len(close_prices),
    }

    # Calculate standard deviation if we have enough data points
    if len(close_prices) > 1:
        stats["std_dev"] = statistics.stdev(close_prices)
    else:
        stats["std_dev"] = 0.0

    return stats


def calculate_daily_returns(
    symbol: str,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> List[Dict[str, Any]]:
    """Calculate daily returns for a symbol.

    Args:
        symbol: Stock symbol.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        List of dictionaries with daily return data:
        - date: str - Date
        - price: float - Closing price
        - daily_return: float - Daily return percentage
        - absolute_change: float - Absolute price change
    """
    if db is None:
        db = Database()

    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")

    prices = get_prices(symbol, start_date, end_date, db)

    if len(prices) < 2:
        return []

    daily_returns = []
    for i in range(1, len(prices)):
        prev_price = prices[i - 1].close
        curr_price = prices[i].close
        price_date = prices[i].date

        if prev_price is None or curr_price is None or prev_price == 0:
            continue

        absolute_change = curr_price - prev_price
        daily_return = (absolute_change / prev_price) * 100.0

        daily_returns.append({
            "date": price_date.isoformat() if isinstance(price_date, date) else str(price_date),
            "price": curr_price,
            "daily_return": daily_return,
            "absolute_change": absolute_change,
        })

    return daily_returns


def get_price_range(
    symbol: str,
    start_date: date,
    end_date: date,
    db: Optional[Database] = None,
) -> Dict[str, Any]:
    """Get price range information (high, low, first, last) for a symbol.

    Args:
        symbol: Stock symbol.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
        db: Database instance. If None, creates a new instance.

    Returns:
        Dictionary with range information:
        - first_price: float - First price in range
        - last_price: float - Last price in range
        - high: float - Highest price in range
        - low: float - Lowest price in range
        - price_range: float - Difference between high and low
    """
    if db is None:
        db = Database()

    if start_date > end_date:
        raise ValueError("start_date must be <= end_date")

    prices = get_prices(symbol, start_date, end_date, db)

    if not prices:
        raise ValueError(f"No price data available for {symbol} between {start_date} and {end_date}")

    close_prices = [p.close for p in prices if p.close is not None]

    if not close_prices:
        raise ValueError(f"No valid price data for {symbol}")

    return {
        "symbol": symbol.upper(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "first_price": close_prices[0],
        "last_price": close_prices[-1],
        "high": max(close_prices),
        "low": min(close_prices),
        "price_range": max(close_prices) - min(close_prices),
        "count": len(close_prices),
    }


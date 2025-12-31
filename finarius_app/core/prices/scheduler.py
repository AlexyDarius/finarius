"""Price update scheduler for managing automatic price updates."""

import logging
from typing import Optional, List, Set, Dict, Any, Callable
from datetime import date, datetime, timedelta

from ..database import Database
from .downloader import PriceDownloader
from .exceptions import PriceDownloadError

logger = logging.getLogger(__name__)


def get_all_portfolio_symbols(
    db: Optional[Database] = None,
    account_id: Optional[int] = None,
) -> Set[str]:
    """Get all unique symbols from transactions in the portfolio.

    Args:
        db: Database instance. If None, creates a new instance.
        account_id: Optional account ID to filter by. If None, gets all symbols.

    Returns:
        Set of unique symbol strings (uppercase).
    """
    if db is None:
        db = Database()

    if account_id is not None:
        query = """
            SELECT DISTINCT symbol
            FROM transactions
            WHERE symbol IS NOT NULL
            AND account_id = ?
            ORDER BY symbol
        """
        results = db.fetchall(query, (account_id,))
    else:
        query = """
            SELECT DISTINCT symbol
            FROM transactions
            WHERE symbol IS NOT NULL
            ORDER BY symbol
        """
        results = db.fetchall(query)

    symbols = {row["symbol"].upper() for row in results if row["symbol"]}
    logger.debug(f"Found {len(symbols)} unique symbols in portfolio")
    return symbols


def get_last_update_time(
    symbol: str,
    db: Optional[Database] = None,
) -> Optional[datetime]:
    """Get the last update time for a symbol.

    Args:
        symbol: Stock symbol.
        db: Database instance. If None, creates a new instance.

    Returns:
        Datetime of last update or None if no prices exist.
    """
    if db is None:
        db = Database()

    result = db.fetchone(
        """
        SELECT MAX(created_at) as last_update
        FROM prices
        WHERE symbol = ?
        """,
        (symbol.upper(),),
    )

    if result and result["last_update"]:
        try:
            # Parse the timestamp
            timestamp_str = result["last_update"]
            # Handle both with and without timezone
            if "T" in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing last update time for {symbol}: {e}")
            return None

    return None


def update_prices_for_symbol(
    symbol: str,
    downloader: Optional[PriceDownloader] = None,
    db: Optional[Database] = None,
    days_back: int = 365,
    force_update: bool = False,
) -> Dict[str, Any]:
    """Update prices for a specific symbol.

    Args:
        symbol: Stock symbol to update.
        downloader: PriceDownloader instance. If None, creates a new instance.
        db: Database instance. If None, creates a new instance.
        days_back: Number of days back to update prices (default: 365).
        force_update: If True, update even if recently updated.

    Returns:
        Dictionary with update results:
        - success: bool
        - symbol: str
        - prices_downloaded: int
        - error: Optional[str]
    """
    if db is None:
        db = Database()

    if downloader is None:
        downloader = PriceDownloader(db=db)

    result = {
        "success": False,
        "symbol": symbol.upper(),
        "prices_downloaded": 0,
        "error": None,
    }

    try:
        # Check last update time if not forcing
        if not force_update:
            last_update = get_last_update_time(symbol, db)
            if last_update:
                # Don't update if updated within last hour
                if datetime.now() - last_update.replace(tzinfo=None) < timedelta(hours=1):
                    logger.debug(f"Skipping {symbol}: updated recently")
                    result["success"] = True
                    return result

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)

        # Download prices
        logger.info(f"Updating prices for {symbol} from {start_date} to {end_date}")
        prices = downloader.download_prices(symbol, start_date, end_date)

        result["success"] = True
        result["prices_downloaded"] = len(prices)
        logger.info(f"Updated {len(prices)} prices for {symbol}")

    except Exception as e:
        logger.error(f"Error updating prices for {symbol}: {e}")
        result["error"] = str(e)
        result["success"] = False

    return result


def update_all_prices(
    downloader: Optional[PriceDownloader] = None,
    db: Optional[Database] = None,
    account_id: Optional[int] = None,
    days_back: int = 365,
    force_update: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """Update prices for all symbols in the portfolio.

    Args:
        downloader: PriceDownloader instance. If None, creates a new instance.
        db: Database instance. If None, creates a new instance.
        account_id: Optional account ID to filter by. If None, updates all symbols.
        days_back: Number of days back to update prices (default: 365).
        force_update: If True, update even if recently updated.
        progress_callback: Optional callback(current, total, symbol) for progress.

    Returns:
        Dictionary with update results:
        - total_symbols: int
        - successful: int
        - failed: int
        - total_prices: int
        - results: List[Dict] - individual symbol results
    """
    if db is None:
        db = Database()

    if downloader is None:
        downloader = PriceDownloader(db=db)

    # Get all symbols
    symbols = get_all_portfolio_symbols(db, account_id)

    if not symbols:
        logger.warning("No symbols found in portfolio")
        return {
            "total_symbols": 0,
            "successful": 0,
            "failed": 0,
            "total_prices": 0,
            "results": [],
        }

    logger.info(f"Updating prices for {len(symbols)} symbols")

    results = []
    successful = 0
    failed = 0
    total_prices = 0

    for idx, symbol in enumerate(sorted(symbols), 1):
        if progress_callback:
            progress_callback(idx, len(symbols), symbol)

        result = update_prices_for_symbol(
            symbol, downloader, db, days_back, force_update
        )

        results.append(result)
        if result["success"]:
            successful += 1
            total_prices += result["prices_downloaded"]
        else:
            failed += 1

    summary = {
        "total_symbols": len(symbols),
        "successful": successful,
        "failed": failed,
        "total_prices": total_prices,
        "results": results,
    }

    logger.info(
        f"Price update complete: {successful} successful, {failed} failed, "
        f"{total_prices} total prices downloaded"
    )

    return summary


def schedule_daily_updates(
    downloader: Optional[PriceDownloader] = None,
    db: Optional[Database] = None,
    account_id: Optional[int] = None,
    update_time: Optional[str] = "09:00",
) -> None:
    """Schedule daily price updates.

    Note: This is a placeholder for future scheduling implementation.
    For now, it just logs the schedule. Actual scheduling would require
    a task scheduler like APScheduler or similar.

    Args:
        downloader: PriceDownloader instance. If None, creates a new instance.
        db: Database instance. If None, creates a new instance.
        account_id: Optional account ID to filter by.
        update_time: Time of day to run updates (HH:MM format).
    """
    logger.info(
        f"Scheduling daily price updates at {update_time} "
        f"(account_id: {account_id or 'all'})"
    )
    # TODO: Implement actual scheduling with APScheduler or similar
    # For now, this is just a placeholder
    logger.warning(
        "Daily scheduling not yet implemented. "
        "Use update_all_prices() manually or implement a scheduler."
    )


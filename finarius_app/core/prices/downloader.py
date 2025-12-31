"""Price downloader using yfinance."""

import time
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import date, datetime, timedelta

import yfinance as yf
import pandas as pd

from ..database import Database
from ..models.price import Price
from .exceptions import PriceDownloadError, SymbolNotFoundError, ValidationError
from .validation import validate_symbol, symbol_exists
from .cache import (
    is_price_cached,
    get_cached_price,
    update_price_cache,
    CACHE_EXPIRATION_HISTORICAL,
    CACHE_EXPIRATION_LATEST,
)
from .normalization import normalize_price_data

logger = logging.getLogger(__name__)

# Default rate limiting: 1 request per second
DEFAULT_RATE_LIMIT_DELAY = 1.0
# Default retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0


class PriceDownloader:
    """Download and manage market price data using yfinance.

    This class provides functionality to download price data from yfinance,
    with rate limiting, retry logic, caching, and error handling.
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        use_cache: bool = True,
    ) -> None:
        """Initialize PriceDownloader.

        Args:
            db: Database instance for caching. If None, creates a new instance.
            rate_limit_delay: Delay between requests in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Initial delay between retries in seconds.
            use_cache: Whether to use database cache.
        """
        self.db = db or Database()
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.use_cache = use_cache
        self._last_request_time: Optional[float] = None

    def _rate_limit(self) -> None:
        """Apply rate limiting to prevent too many requests."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _retry_with_backoff(
        self,
        func,
        *args,
        **kwargs,
    ) -> Any:
        """Execute function with exponential backoff retry logic.

        Args:
            func: Function to execute.
            *args: Positional arguments for function.
            **kwargs: Keyword arguments for function.

        Returns:
            Function result.

        Raises:
            PriceDownloadError: If all retries fail.
        """
        last_exception = None
        delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {self.max_retries} attempts failed")

        raise PriceDownloadError(
            f"Failed after {self.max_retries} attempts: {last_exception}"
        ) from last_exception

    def download_price(
        self,
        symbol: str,
        price_date: date,
        use_cache: Optional[bool] = None,
    ) -> Optional[Price]:
        """Download single price for symbol and date.

        Args:
            symbol: Stock symbol.
            price_date: Price date.
            use_cache: Override instance cache setting. If None, uses instance setting.

        Returns:
            Price instance or None if not available.

        Raises:
            ValidationError: If symbol format is invalid.
            PriceDownloadError: If download fails.
        """
        validate_symbol(symbol)
        symbol = symbol.strip().upper()

        cache_enabled = use_cache if use_cache is not None else self.use_cache

        # Check cache first
        if cache_enabled:
            cached_price = get_cached_price(symbol, price_date, self.db)
            if cached_price is not None:
                logger.debug(f"Using cached price for {symbol} on {price_date}")
                return cached_price

        def _download() -> Optional[Price]:
            self._rate_limit()

            try:
                ticker = yf.Ticker(symbol)
                # Download data for a small range around the date
                start = price_date - timedelta(days=5)
                end = price_date + timedelta(days=1)
                hist = ticker.history(start=start, end=end)

                if hist.empty:
                    logger.warning(f"No data available for {symbol} on {price_date}")
                    return None

                # Find the closest date (prefer exact match, then closest before)
                date_str = price_date.isoformat()
                if date_str in hist.index.strftime("%Y-%m-%d").values:
                    row = hist.loc[hist.index.strftime("%Y-%m-%d") == date_str].iloc[0]
                else:
                    # Get closest date before or on the requested date
                    before_dates = hist[hist.index.date <= price_date]
                    if before_dates.empty:
                        logger.warning(f"No data before or on {price_date} for {symbol}")
                        return None
                    row = before_dates.iloc[-1]

                # Normalize data
                price_data = normalize_price_data(row.to_dict(), symbol, price_date)
                if price_data is None:
                    return None

                # Create and save Price object
                price = Price(
                    symbol=symbol,
                    date=price_date,
                    close=price_data["close"],
                    open_price=price_data.get("open"),
                    high=price_data.get("high"),
                    low=price_data.get("low"),
                    volume=price_data.get("volume"),
                )

                if cache_enabled:
                    price.save(self.db)

                logger.info(f"Downloaded price for {symbol} on {price_date}: {price.close}")
                return price

            except Exception as e:
                logger.error(f"Error downloading price for {symbol} on {price_date}: {e}")
                raise

        try:
            return self._retry_with_backoff(_download)
        except PriceDownloadError:
            raise
        except Exception as e:
            raise PriceDownloadError(f"Failed to download price for {symbol}: {e}") from e

    def download_prices(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        use_cache: Optional[bool] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Price]:
        """Download price range for symbol.

        Args:
            symbol: Stock symbol.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            use_cache: Override instance cache setting.
            progress_callback: Optional callback(current, total) for progress tracking.

        Returns:
            List of Price instances.

        Raises:
            ValidationError: If symbol format is invalid.
            PriceDownloadError: If download fails.
        """
        validate_symbol(symbol)
        symbol = symbol.strip().upper()

        if start_date > end_date:
            raise ValidationError("start_date must be <= end_date")

        cache_enabled = use_cache if use_cache is not None else self.use_cache

        def _download() -> List[Price]:
            self._rate_limit()

            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date + timedelta(days=1))

                if hist.empty:
                    logger.warning(
                        f"No data available for {symbol} from {start_date} to {end_date}"
                    )
                    return []

                prices = []
                total_days = len(hist)
                current = 0

                for idx, row in hist.iterrows():
                    current += 1
                    if progress_callback:
                        progress_callback(current, total_days)

                    # Get date from index
                    if isinstance(idx, pd.Timestamp):
                        price_date = idx.date()
                    elif isinstance(idx, date):
                        price_date = idx
                    else:
                        continue

                    # Skip if outside range
                    if price_date < start_date or price_date > end_date:
                        continue

                    # Normalize data
                    price_data = normalize_price_data(row.to_dict(), symbol, price_date)
                    if price_data is None:
                        continue

                    # Create Price object
                    price = Price(
                        symbol=symbol,
                        date=price_date,
                        close=price_data["close"],
                        open_price=price_data.get("open"),
                        high=price_data.get("high"),
                        low=price_data.get("low"),
                        volume=price_data.get("volume"),
                    )

                    if cache_enabled:
                        price.save(self.db)

                    prices.append(price)

                logger.info(
                    f"Downloaded {len(prices)} prices for {symbol} "
                    f"from {start_date} to {end_date}"
                )
                return prices

            except Exception as e:
                logger.error(
                    f"Error downloading prices for {symbol} "
                    f"from {start_date} to {end_date}: {e}"
                )
                raise

        try:
            return self._retry_with_backoff(_download)
        except PriceDownloadError:
            raise
        except Exception as e:
            raise PriceDownloadError(
                f"Failed to download prices for {symbol}: {e}"
            ) from e

    def download_latest_price(
        self,
        symbol: str,
        use_cache: Optional[bool] = None,
    ) -> Optional[Price]:
        """Download current/latest price for symbol.

        Args:
            symbol: Stock symbol.
            use_cache: Override instance cache setting.

        Returns:
            Price instance or None if not available.

        Raises:
            ValidationError: If symbol format is invalid.
            PriceDownloadError: If download fails.
        """
        validate_symbol(symbol)
        symbol = symbol.strip().upper()

        cache_enabled = use_cache if use_cache is not None else self.use_cache

        # Check cache first (with shorter expiration for latest prices)
        if cache_enabled:
            today = date.today()
            cached_price = get_cached_price(symbol, today, self.db)
            if cached_price is not None:
                # Check if cache is still fresh (within 1 hour)
                if is_price_cached(symbol, today, self.db, CACHE_EXPIRATION_LATEST):
                    logger.debug(f"Using cached latest price for {symbol}")
                    return cached_price

        def _download() -> Optional[Price]:
            self._rate_limit()

            try:
                ticker = yf.Ticker(symbol)
                # Get latest data (last 5 days to ensure we get recent data)
                hist = ticker.history(period="5d")

                if hist.empty:
                    logger.warning(f"No data available for {symbol}")
                    return None

                # Get the most recent row
                row = hist.iloc[-1]
                price_date = hist.index[-1].date() if isinstance(hist.index[-1], pd.Timestamp) else date.today()

                # Normalize data
                price_data = normalize_price_data(row.to_dict(), symbol, price_date)
                if price_data is None:
                    return None

                # Create and save Price object
                price = Price(
                    symbol=symbol,
                    date=price_date,
                    close=price_data["close"],
                    open_price=price_data.get("open"),
                    high=price_data.get("high"),
                    low=price_data.get("low"),
                    volume=price_data.get("volume"),
                )

                if cache_enabled:
                    price.save(self.db)

                logger.info(f"Downloaded latest price for {symbol}: {price.close} on {price_date}")
                return price

            except Exception as e:
                logger.error(f"Error downloading latest price for {symbol}: {e}")
                raise

        try:
            return self._retry_with_backoff(_download)
        except PriceDownloadError:
            raise
        except Exception as e:
            raise PriceDownloadError(
                f"Failed to download latest price for {symbol}: {e}"
            ) from e

    def download_multiple_symbols(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        use_cache: Optional[bool] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, List[Price]]:
        """Download prices for multiple symbols.

        Args:
            symbols: List of stock symbols.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            use_cache: Override instance cache setting.
            progress_callback: Optional callback(current, total) for progress tracking.

        Returns:
            Dictionary mapping symbol -> list of Price instances.

        Raises:
            ValidationError: If any symbol format is invalid.
            PriceDownloadError: If download fails.
        """
        # Validate all symbols first
        for symbol in symbols:
            validate_symbol(symbol)

        if start_date > end_date:
            raise ValidationError("start_date must be <= end_date")

        results: Dict[str, List[Price]] = {}
        total = len(symbols)
        current = 0

        for symbol in symbols:
            current += 1
            if progress_callback:
                progress_callback(current, total)

            try:
                prices = self.download_prices(
                    symbol, start_date, end_date, use_cache=use_cache
                )
                results[symbol] = prices
            except Exception as e:
                logger.error(f"Error downloading prices for {symbol}: {e}")
                results[symbol] = []  # Empty list on error

        logger.info(f"Downloaded prices for {len(results)} symbols")
        return results


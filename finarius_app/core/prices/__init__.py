"""Price downloader module for Finarius portfolio tracking application.

This module provides functionality to download, cache, validate, and normalize
market price data from external sources.
"""

from .exceptions import (
    PriceDownloadError,
    SymbolNotFoundError,
    ValidationError,
    InsufficientDataError,
)
from .validation import validate_symbol, symbol_exists
from .cache import (
    is_price_cached,
    get_cached_price,
    update_price_cache,
)
from .normalization import normalize_price_data
from .downloader import PriceDownloader
from .scheduler import (
    get_all_portfolio_symbols,
    get_last_update_time,
    update_prices_for_symbol,
    update_all_prices,
    schedule_daily_updates,
)
from .analytics import (
    get_price_history,
    calculate_returns,
    get_price_statistics,
    calculate_daily_returns,
    get_price_range,
)

__all__ = [
    # Exceptions
    "PriceDownloadError",
    "SymbolNotFoundError",
    "ValidationError",
    "InsufficientDataError",
    # Validation
    "validate_symbol",
    "symbol_exists",
    # Caching
    "is_price_cached",
    "get_cached_price",
    "update_price_cache",
    # Normalization
    "normalize_price_data",
    # Main class
    "PriceDownloader",
    # Scheduler
    "get_all_portfolio_symbols",
    "get_last_update_time",
    "update_prices_for_symbol",
    "update_all_prices",
    "schedule_daily_updates",
    # Analytics
    "get_price_history",
    "calculate_returns",
    "get_price_statistics",
    "calculate_daily_returns",
    "get_price_range",
]


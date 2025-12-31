"""Price data normalization utilities."""

import logging
from typing import Dict, Any, Optional
from datetime import date

from .exceptions import InsufficientDataError

logger = logging.getLogger(__name__)


def normalize_price_data(
    raw_data: Dict[str, Any],
    symbol: str,
    price_date: date,
    handle_missing: str = "skip",
) -> Optional[Dict[str, Any]]:
    """Normalize price data from yfinance format.

    Args:
        raw_data: Raw price data from yfinance.
        symbol: Stock symbol (for logging).
        price_date: Price date (for logging).
        handle_missing: How to handle missing data: 'skip', 'raise', or 'fill_zero'.

    Returns:
        Normalized price data dictionary or None if skipped.

    Raises:
        InsufficientDataError: If required data is missing and handle_missing='raise'.
    """
    if not raw_data or not isinstance(raw_data, dict):
        if handle_missing == "raise":
            raise InsufficientDataError(
                f"No data available for {symbol} on {price_date}"
            )
        logger.warning(f"No data for {symbol} on {price_date}")
        return None

    # Normalize field names (yfinance uses different case conventions)
    normalized = {}

    # Close price is required
    close = raw_data.get("Close") or raw_data.get("close")
    if close is None or (isinstance(close, float) and close <= 0):
        if handle_missing == "raise":
            raise InsufficientDataError(
                f"Missing or invalid close price for {symbol} on {price_date}"
            )
        if handle_missing == "fill_zero":
            close = 0.0
        else:
            logger.warning(f"Missing close price for {symbol} on {price_date}")
            return None

    normalized["close"] = float(close)

    # Optional fields
    open_price = raw_data.get("Open") or raw_data.get("open")
    normalized["open"] = float(open_price) if open_price is not None else None

    high = raw_data.get("High") or raw_data.get("high")
    normalized["high"] = float(high) if high is not None else None

    low = raw_data.get("Low") or raw_data.get("low")
    normalized["low"] = float(low) if low is not None else None

    volume = raw_data.get("Volume") or raw_data.get("volume")
    normalized["volume"] = int(volume) if volume is not None else None

    # Validate data consistency
    if normalized["high"] is not None and normalized["low"] is not None:
        if normalized["high"] < normalized["low"]:
            logger.warning(
                f"Invalid price data for {symbol} on {price_date}: "
                f"high ({normalized['high']}) < low ({normalized['low']})"
            )
            # Swap if needed
            normalized["high"], normalized["low"] = normalized["low"], normalized["high"]

    if normalized["close"] is not None:
        if normalized["high"] is not None and normalized["close"] > normalized["high"]:
            logger.warning(
                f"Close price ({normalized['close']}) > high ({normalized['high']}) "
                f"for {symbol} on {price_date}"
            )
        if normalized["low"] is not None and normalized["close"] < normalized["low"]:
            logger.warning(
                f"Close price ({normalized['close']}) < low ({normalized['low']}) "
                f"for {symbol} on {price_date}"
            )

    return normalized


def handle_stock_split(
    prices: Dict[date, Dict[str, Any]],
    split_ratio: float,
    split_date: date,
) -> Dict[date, Dict[str, Any]]:
    """Adjust prices for stock split.

    Args:
        prices: Dictionary of date -> price data.
        split_ratio: Split ratio (e.g., 2.0 for 2:1 split).
        split_date: Date of the split.

    Returns:
        Adjusted prices dictionary.
    """
    adjusted = {}
    for price_date, price_data in prices.items():
        if price_date < split_date:
            # Adjust prices before split
            adjusted_data = price_data.copy()
            for key in ["close", "open", "high", "low"]:
                if adjusted_data.get(key) is not None:
                    adjusted_data[key] = adjusted_data[key] / split_ratio
            adjusted[price_date] = adjusted_data
        else:
            adjusted[price_date] = price_data

    logger.info(f"Adjusted prices for stock split on {split_date} with ratio {split_ratio}")
    return adjusted


def handle_dividend_adjustment(
    prices: Dict[date, Dict[str, Any]],
    dividend_amount: float,
    ex_dividend_date: date,
) -> Dict[date, Dict[str, Any]]:
    """Adjust prices for dividend (dividend-adjusted prices).

    Args:
        prices: Dictionary of date -> price data.
        dividend_amount: Dividend amount per share.
        ex_dividend_date: Ex-dividend date.

    Returns:
        Adjusted prices dictionary.
    """
    adjusted = {}
    for price_date, price_data in prices.items():
        if price_date < ex_dividend_date:
            # Adjust prices before ex-dividend date
            adjusted_data = price_data.copy()
            for key in ["close", "open", "high", "low"]:
                if adjusted_data.get(key) is not None:
                    adjusted_data[key] = adjusted_data[key] - dividend_amount
            adjusted[price_date] = adjusted_data
        else:
            adjusted[price_date] = price_data

    logger.debug(
        f"Adjusted prices for dividend of {dividend_amount} on {ex_dividend_date}"
    )
    return adjusted


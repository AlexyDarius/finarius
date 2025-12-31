"""Tests for prices module."""

import pytest
import tempfile
import os
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from finarius_app.core.database import init_db, Database
from finarius_app.core.prices import (
    PriceDownloader,
    validate_symbol,
    symbol_exists,
    is_price_cached,
    get_cached_price,
    update_price_cache,
    normalize_price_data,
    PriceDownloadError,
    SymbolNotFoundError,
    ValidationError,
    InsufficientDataError,
)
from finarius_app.core.models.price import Price


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)
    # Clean up singleton
    Database._instance = None
    Database._connection = None


@pytest.fixture
def db(temp_db_path):
    """Create a database instance for testing."""
    Database._instance = None
    Database._connection = None
    db_instance = init_db(temp_db_path)
    yield db_instance
    db_instance.close()
    Database._instance = None
    Database._connection = None


@pytest.fixture
def downloader(db):
    """Create a PriceDownloader instance for testing."""
    return PriceDownloader(db=db, rate_limit_delay=0.1, use_cache=True)


class TestSymbolValidation:
    """Test symbol validation functions."""

    def test_validate_symbol_valid(self):
        """Test validating valid symbols."""
        assert validate_symbol("AAPL") is True
        assert validate_symbol("MSFT") is True
        assert validate_symbol("BTC-USD") is True
        assert validate_symbol("TSLA") is True

    def test_validate_symbol_invalid_empty(self):
        """Test validating empty symbol."""
        with pytest.raises(ValidationError, match="non-empty"):
            validate_symbol("")

    def test_validate_symbol_invalid_whitespace(self):
        """Test validating whitespace-only symbol."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_symbol("   ")

    def test_validate_symbol_invalid_characters(self):
        """Test validating symbol with invalid characters."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_symbol("AAPL@")

    def test_validate_symbol_too_long(self):
        """Test validating symbol that's too long."""
        with pytest.raises(ValidationError, match="cannot exceed"):
            validate_symbol("A" * 21)

    def test_validate_symbol_not_string(self):
        """Test validating non-string symbol."""
        with pytest.raises(ValidationError):
            validate_symbol(123)

    @patch("finarius_app.core.prices.validation.yf.Ticker")
    def test_symbol_exists_valid(self, mock_ticker):
        """Test checking if valid symbol exists."""
        mock_info = {"symbol": "AAPL", "shortName": "Apple Inc."}
        mock_ticker.return_value.info = mock_info

        assert symbol_exists("AAPL") is True

    @patch("finarius_app.core.prices.validation.yf.Ticker")
    def test_symbol_exists_invalid(self, mock_ticker):
        """Test checking if invalid symbol exists."""
        mock_ticker.return_value.info = {}

        assert symbol_exists("INVALID") is False

    @patch("finarius_app.core.prices.validation.yf.Ticker")
    def test_symbol_exists_exception(self, mock_ticker):
        """Test symbol_exists handles exceptions."""
        mock_ticker.return_value.info = None
        mock_ticker.side_effect = Exception("Network error")

        assert symbol_exists("AAPL") is False


class TestPriceCaching:
    """Test price caching functions."""

    def test_is_price_cached_not_cached(self, db):
        """Test checking for non-cached price."""
        assert is_price_cached("AAPL", date(2024, 1, 1), db) is False

    def test_is_price_cached_cached(self, db):
        """Test checking for cached price."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.save(db)

        assert is_price_cached("AAPL", date(2024, 1, 1), db) is True

    def test_is_price_cached_expired(self, db):
        """Test checking for expired cached price."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.save(db)

        # Check with very short expiration
        assert (
            is_price_cached("AAPL", date(2024, 1, 1), db, max_age=timedelta(seconds=0))
            is False
        )

    def test_get_cached_price_not_found(self, db):
        """Test getting non-cached price."""
        assert get_cached_price("AAPL", date(2024, 1, 1), db) is None

    def test_get_cached_price_found(self, db):
        """Test getting cached price."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.save(db)

        cached = get_cached_price("AAPL", date(2024, 1, 1), db)
        assert cached is not None
        assert cached.symbol == "AAPL"
        assert cached.close == 150.0

    def test_update_price_cache(self, db):
        """Test updating price cache."""
        price_data = {
            "close": 150.0,
            "open": 149.0,
            "high": 151.0,
            "low": 148.0,
            "volume": 1000000,
        }

        price = update_price_cache("AAPL", date(2024, 1, 1), price_data, db)

        assert price.symbol == "AAPL"
        assert price.close == 150.0
        assert price.open == 149.0

        # Verify in database
        cached = get_cached_price("AAPL", date(2024, 1, 1), db)
        assert cached is not None
        assert cached.close == 150.0


class TestPriceNormalization:
    """Test price data normalization."""

    def test_normalize_price_data_valid(self):
        """Test normalizing valid price data."""
        raw_data = {
            "Close": 150.0,
            "Open": 149.0,
            "High": 151.0,
            "Low": 148.0,
            "Volume": 1000000,
        }

        normalized = normalize_price_data(raw_data, "AAPL", date(2024, 1, 1))

        assert normalized is not None
        assert normalized["close"] == 150.0
        assert normalized["open"] == 149.0
        assert normalized["high"] == 151.0
        assert normalized["low"] == 148.0
        assert normalized["volume"] == 1000000

    def test_normalize_price_data_lowercase(self):
        """Test normalizing price data with lowercase keys."""
        raw_data = {
            "close": 150.0,
            "open": 149.0,
            "high": 151.0,
            "low": 148.0,
            "volume": 1000000,
        }

        normalized = normalize_price_data(raw_data, "AAPL", date(2024, 1, 1))

        assert normalized is not None
        assert normalized["close"] == 150.0

    def test_normalize_price_data_missing_close(self):
        """Test normalizing price data with missing close."""
        raw_data = {"Open": 149.0}

        with pytest.raises(InsufficientDataError):
            normalize_price_data(
                raw_data, "AAPL", date(2024, 1, 1), handle_missing="raise"
            )

    def test_normalize_price_data_missing_close_skip(self):
        """Test normalizing price data with missing close (skip mode)."""
        raw_data = {"Open": 149.0}

        normalized = normalize_price_data(
            raw_data, "AAPL", date(2024, 1, 1), handle_missing="skip"
        )

        assert normalized is None

    def test_normalize_price_data_optional_fields(self):
        """Test normalizing price data with only required fields."""
        raw_data = {"Close": 150.0}

        normalized = normalize_price_data(raw_data, "AAPL", date(2024, 1, 1))

        assert normalized is not None
        assert normalized["close"] == 150.0
        assert normalized["open"] is None
        assert normalized["high"] is None
        assert normalized["low"] is None
        assert normalized["volume"] is None


class TestPriceDownloader:
    """Test PriceDownloader class."""

    def test_downloader_initialization(self, db):
        """Test initializing PriceDownloader."""
        downloader = PriceDownloader(db=db, rate_limit_delay=0.5)

        assert downloader.db == db
        assert downloader.rate_limit_delay == 0.5
        assert downloader.use_cache is True

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_price_success(self, mock_ticker, downloader):
        """Test downloading a single price successfully."""
        # Mock yfinance response
        mock_hist = pd.DataFrame(
            {
                "Close": [150.0],
                "Open": [149.0],
                "High": [151.0],
                "Low": [148.0],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([date(2024, 1, 1)]),
        )
        mock_ticker.return_value.history.return_value = mock_hist

        price = downloader.download_price("AAPL", date(2024, 1, 1))

        assert price is not None
        assert price.symbol == "AAPL"
        assert price.close == 150.0

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_price_from_cache(self, mock_ticker, downloader):
        """Test downloading price from cache."""
        # Pre-populate cache
        cached_price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        cached_price.save(downloader.db)

        price = downloader.download_price("AAPL", date(2024, 1, 1))

        assert price is not None
        assert price.close == 150.0
        # Should not call yfinance
        mock_ticker.assert_not_called()

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_price_no_data(self, mock_ticker, downloader):
        """Test downloading price when no data is available."""
        mock_hist = pd.DataFrame()
        mock_ticker.return_value.history.return_value = mock_hist

        price = downloader.download_price("AAPL", date(2024, 1, 1))

        assert price is None

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_prices_range(self, mock_ticker, downloader):
        """Test downloading price range."""
        # Mock yfinance response with multiple dates
        dates = pd.date_range(start="2024-01-01", end="2024-01-05", freq="D")
        mock_hist = pd.DataFrame(
            {
                "Close": [150.0, 151.0, 152.0, 153.0, 154.0],
                "Open": [149.0, 150.0, 151.0, 152.0, 153.0],
                "High": [151.0, 152.0, 153.0, 154.0, 155.0],
                "Low": [148.0, 149.0, 150.0, 151.0, 152.0],
                "Volume": [1000000] * 5,
            },
            index=dates,
        )
        mock_ticker.return_value.history.return_value = mock_hist

        prices = downloader.download_prices(
            "AAPL", date(2024, 1, 1), date(2024, 1, 5)
        )

        assert len(prices) == 5
        assert all(p.symbol == "AAPL" for p in prices)
        assert prices[0].close == 150.0
        assert prices[-1].close == 154.0

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_latest_price(self, mock_ticker, downloader):
        """Test downloading latest price."""
        dates = pd.date_range(start="2024-01-01", end="2024-01-05", freq="D")
        mock_hist = pd.DataFrame(
            {
                "Close": [150.0, 151.0, 152.0, 153.0, 154.0],
                "Open": [149.0, 150.0, 151.0, 152.0, 153.0],
                "High": [151.0, 152.0, 153.0, 154.0, 155.0],
                "Low": [148.0, 149.0, 150.0, 151.0, 152.0],
                "Volume": [1000000] * 5,
            },
            index=dates,
        )
        mock_ticker.return_value.history.return_value = mock_hist

        price = downloader.download_latest_price("AAPL")

        assert price is not None
        assert price.symbol == "AAPL"
        assert price.close == 154.0  # Latest price

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_multiple_symbols(self, mock_ticker, downloader):
        """Test downloading prices for multiple symbols."""
        # Mock responses for different symbols
        def mock_history(start=None, end=None, period=None):
            if period == "5d":
                dates = pd.date_range(start="2024-01-01", end="2024-01-05", freq="D")
            else:
                dates = pd.date_range(start=start, end=end, freq="D")
            return pd.DataFrame(
                {
                    "Close": [150.0] * len(dates),
                    "Open": [149.0] * len(dates),
                    "High": [151.0] * len(dates),
                    "Low": [148.0] * len(dates),
                    "Volume": [1000000] * len(dates),
                },
                index=dates,
            )

        mock_ticker.return_value.history = mock_history

        results = downloader.download_multiple_symbols(
            ["AAPL", "MSFT"], date(2024, 1, 1), date(2024, 1, 5)
        )

        assert "AAPL" in results
        assert "MSFT" in results
        assert len(results["AAPL"]) > 0
        assert len(results["MSFT"]) > 0

    def test_download_price_invalid_symbol(self, downloader):
        """Test downloading price with invalid symbol."""
        with pytest.raises(ValidationError):
            downloader.download_price("", date(2024, 1, 1))

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_price_retry_logic(self, mock_ticker, db):
        """Test retry logic on failures."""
        downloader = PriceDownloader(db=db, max_retries=3, retry_delay=0.1)

        # First two calls fail, third succeeds
        mock_hist = pd.DataFrame(
            {
                "Close": [150.0],
                "Open": [149.0],
                "High": [151.0],
                "Low": [148.0],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([date(2024, 1, 1)]),
        )

        call_count = 0

        def mock_history(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Network error")
            return mock_hist

        mock_ticker.return_value.history = mock_history

        price = downloader.download_price("AAPL", date(2024, 1, 1))

        assert price is not None
        assert call_count == 3

    @patch("finarius_app.core.prices.downloader.yf.Ticker")
    def test_download_price_all_retries_fail(self, mock_ticker, db):
        """Test that exception is raised when all retries fail."""
        downloader = PriceDownloader(db=db, max_retries=2, retry_delay=0.1)

        mock_ticker.return_value.history.side_effect = Exception("Network error")

        with pytest.raises(PriceDownloadError):
            downloader.download_price("AAPL", date(2024, 1, 1))

    def test_rate_limiting(self, db):
        """Test rate limiting functionality."""
        downloader = PriceDownloader(db=db, rate_limit_delay=0.2)

        import time

        start = time.time()
        downloader._rate_limit()
        downloader._rate_limit()
        elapsed = time.time() - start

        # Should have waited at least the rate limit delay
        assert elapsed >= 0.2


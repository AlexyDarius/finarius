"""Tests for price management utilities (scheduler and analytics)."""

import pytest
import tempfile
import os
from datetime import date, timedelta, datetime
from unittest.mock import Mock, patch, MagicMock

from finarius_app.core.database import init_db, Database
from finarius_app.core.models import Account, Transaction, Price
from finarius_app.core.prices import (
    PriceDownloader,
    get_all_portfolio_symbols,
    get_last_update_time,
    update_prices_for_symbol,
    update_all_prices,
    schedule_daily_updates,
    get_price_history,
    calculate_returns,
    get_price_statistics,
    calculate_daily_returns,
    get_price_range,
)


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
def sample_account(db):
    """Create a sample account for testing."""
    account = Account(name="Test Account", currency="USD")
    account.save(db)
    return account


@pytest.fixture
def sample_transactions(db, sample_account):
    """Create sample transactions for testing."""
    transactions = [
        Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        ),
        Transaction(
            date=date(2024, 1, 2),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="MSFT",
            qty=5.0,
            price=300.0,
        ),
        Transaction(
            date=date(2024, 1, 3),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=5.0,
            price=155.0,
        ),
    ]
    for txn in transactions:
        txn.save(db)
    return transactions


@pytest.fixture
def sample_prices(db):
    """Create sample prices for testing."""
    prices = []
    # Use dates relative to today so get_price_history works
    base_date = date.today() - timedelta(days=20)
    for i in range(10):
        price_date = base_date + timedelta(days=i)
        prices.append(
            Price(
                symbol="AAPL",
                date=price_date,
                close=150.0 + i * 2.0,
                open_price=149.0 + i * 2.0,
                high=151.0 + i * 2.0,
                low=148.0 + i * 2.0,
                volume=1000000,
            )
        )
        prices[-1].save(db)
    return prices


class TestPriceScheduler:
    """Test price update scheduler functions."""

    def test_get_all_portfolio_symbols(self, db, sample_transactions):
        """Test getting all portfolio symbols."""
        symbols = get_all_portfolio_symbols(db)

        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert len(symbols) == 2

    def test_get_all_portfolio_symbols_filtered_by_account(
        self, db, sample_account, sample_transactions
    ):
        """Test getting symbols filtered by account."""
        # Create another account with different transactions
        account2 = Account(name="Account 2", currency="USD")
        account2.save(db)

        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=account2.id,
            transaction_type="BUY",
            symbol="GOOGL",
            qty=1.0,
            price=100.0,
        )
        txn.save(db)

        symbols = get_all_portfolio_symbols(db, account_id=sample_account.id)
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" not in symbols

        symbols_all = get_all_portfolio_symbols(db)
        assert "GOOGL" in symbols_all

    def test_get_all_portfolio_symbols_empty(self, db):
        """Test getting symbols when portfolio is empty."""
        symbols = get_all_portfolio_symbols(db)
        assert len(symbols) == 0

    def test_get_last_update_time_no_prices(self, db):
        """Test getting last update time when no prices exist."""
        last_update = get_last_update_time("AAPL", db)
        assert last_update is None

    def test_get_last_update_time_with_prices(self, db, sample_prices):
        """Test getting last update time when prices exist."""
        last_update = get_last_update_time("AAPL", db)
        assert last_update is not None
        assert isinstance(last_update, datetime)

    @patch("finarius_app.core.prices.scheduler.PriceDownloader")
    def test_update_prices_for_symbol(self, mock_downloader_class, db):
        """Test updating prices for a symbol."""
        # Mock downloader
        mock_downloader = Mock(spec=PriceDownloader)
        mock_price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        mock_downloader.download_prices.return_value = [mock_price]
        mock_downloader_class.return_value = mock_downloader

        result = update_prices_for_symbol("AAPL", mock_downloader, db, days_back=30)

        assert result["success"] is True
        assert result["symbol"] == "AAPL"
        assert result["prices_downloaded"] == 1
        assert result["error"] is None

    @patch("finarius_app.core.prices.scheduler.PriceDownloader")
    def test_update_prices_for_symbol_error(self, mock_downloader_class, db):
        """Test updating prices when error occurs."""
        mock_downloader = Mock(spec=PriceDownloader)
        mock_downloader.download_prices.side_effect = Exception("Network error")
        mock_downloader_class.return_value = mock_downloader

        result = update_prices_for_symbol("AAPL", mock_downloader, db)

        assert result["success"] is False
        assert result["error"] is not None

    @patch("finarius_app.core.prices.scheduler.update_prices_for_symbol")
    def test_update_all_prices(self, mock_update, db, sample_transactions):
        """Test updating all prices."""
        # Mock individual updates
        mock_update.return_value = {
            "success": True,
            "symbol": "AAPL",
            "prices_downloaded": 10,
            "error": None,
        }

        result = update_all_prices(db=db)

        assert result["total_symbols"] == 2
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert result["total_prices"] == 20

    def test_schedule_daily_updates(self, db):
        """Test scheduling daily updates (placeholder)."""
        # This should not raise an error
        schedule_daily_updates(db=db, update_time="09:00")
        # Just verify it doesn't crash


class TestPriceAnalytics:
    """Test price analytics functions."""

    def test_get_price_history(self, db, sample_prices):
        """Test getting price history."""
        # Use enough days to include our sample prices (which start 20 days ago)
        history = get_price_history("AAPL", days=30, db=db)

        assert len(history) >= 10  # At least our 10 sample prices
        assert "date" in history[0]
        assert "close" in history[0]
        # Find our sample prices in the history
        sample_dates = {p.date for p in sample_prices}
        history_dates = {date.fromisoformat(h["date"]) for h in history}
        assert sample_dates.issubset(history_dates)

    def test_get_price_history_limited_days(self, db, sample_prices):
        """Test getting price history with limited days."""
        # Get history for enough days to include our sample prices
        history = get_price_history("AAPL", days=30, db=db)

        # Should have at least our 10 sample prices
        assert len(history) >= 10

    def test_get_price_history_no_data(self, db):
        """Test getting price history when no data exists."""
        history = get_price_history("NONEXISTENT", days=30, db=db)
        assert len(history) == 0

    def test_calculate_returns(self, db, sample_prices):
        """Test calculating returns."""
        # Use dates from sample_prices fixture
        start = sample_prices[0].date
        end = sample_prices[-1].date

        returns = calculate_returns("AAPL", start, end, db)

        assert returns["symbol"] == "AAPL"
        assert returns["start_price"] == 150.0
        assert returns["end_price"] == 168.0
        assert returns["absolute_return"] == 18.0
        assert returns["percentage_return"] == pytest.approx(12.0, rel=0.1)
        assert returns["days"] == 9

    def test_calculate_returns_invalid_dates(self, db):
        """Test calculating returns with invalid date range."""
        start = date(2024, 1, 10)
        end = date(2024, 1, 1)

        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            calculate_returns("AAPL", start, end, db)

    def test_calculate_returns_no_data(self, db):
        """Test calculating returns when no data exists."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)

        with pytest.raises(ValueError, match="No price data"):
            calculate_returns("NONEXISTENT", start, end, db)

    def test_get_price_statistics(self, db, sample_prices):
        """Test getting price statistics."""
        # Use dates from sample_prices fixture
        start = sample_prices[0].date
        end = sample_prices[-1].date

        stats = get_price_statistics("AAPL", start, end, db)

        assert stats["symbol"] == "AAPL"
        assert stats["min"] == 150.0
        assert stats["max"] == 168.0
        assert stats["mean"] == pytest.approx(159.0, rel=0.1)
        assert stats["median"] == pytest.approx(159.0, rel=0.1)
        assert stats["count"] == 10
        assert "std_dev" in stats

    def test_get_price_statistics_invalid_dates(self, db):
        """Test getting statistics with invalid date range."""
        start = date(2024, 1, 10)
        end = date(2024, 1, 1)

        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            get_price_statistics("AAPL", start, end, db)

    def test_get_price_statistics_no_data(self, db):
        """Test getting statistics when no data exists."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)

        with pytest.raises(ValueError, match="No price data"):
            get_price_statistics("NONEXISTENT", start, end, db)

    def test_calculate_daily_returns(self, db, sample_prices):
        """Test calculating daily returns."""
        # Use dates from sample_prices fixture
        start = sample_prices[0].date
        end = sample_prices[-1].date

        daily_returns = calculate_daily_returns("AAPL", start, end, db)

        assert len(daily_returns) == 9  # 10 prices = 9 daily returns
        assert "date" in daily_returns[0]
        assert "price" in daily_returns[0]
        assert "daily_return" in daily_returns[0]
        assert "absolute_change" in daily_returns[0]

        # First return should be from day 1 to day 2
        assert daily_returns[0]["absolute_change"] == 2.0

    def test_calculate_daily_returns_insufficient_data(self, db):
        """Test calculating daily returns with insufficient data."""
        # Create only one price
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.save(db)

        start = date(2024, 1, 1)
        end = date(2024, 1, 10)

        daily_returns = calculate_daily_returns("AAPL", start, end, db)
        assert len(daily_returns) == 0

    def test_get_price_range(self, db, sample_prices):
        """Test getting price range."""
        # Use dates from sample_prices fixture
        start = sample_prices[0].date
        end = sample_prices[-1].date

        price_range = get_price_range("AAPL", start, end, db)

        assert price_range["symbol"] == "AAPL"
        assert price_range["first_price"] == 150.0
        assert price_range["last_price"] == 168.0
        assert price_range["high"] == 168.0
        assert price_range["low"] == 150.0
        assert price_range["price_range"] == 18.0
        assert price_range["count"] == 10

    def test_get_price_range_invalid_dates(self, db):
        """Test getting price range with invalid date range."""
        start = date(2024, 1, 10)
        end = date(2024, 1, 1)

        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            get_price_range("AAPL", start, end, db)

    def test_get_price_range_no_data(self, db):
        """Test getting price range when no data exists."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 10)

        with pytest.raises(ValueError, match="No price data"):
            get_price_range("NONEXISTENT", start, end, db)


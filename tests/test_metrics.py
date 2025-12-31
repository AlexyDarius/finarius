"""Tests for metrics module."""

import pytest
import tempfile
import os
from datetime import date, timedelta
from unittest.mock import Mock, patch

from finarius_app.core.database import init_db, Database
from finarius_app.core.models import Account, Transaction, Price
from finarius_app.core.engine import PortfolioEngine
from finarius_app.core.metrics import (
    MetricsCalculator,
    calculate_realized_gains,
    get_realized_gains_by_symbol,
    calculate_unrealized_gains,
    get_unrealized_gains_by_symbol,
    calculate_total_return,
    calculate_total_return_percentage,
    calculate_cagr,
    calculate_irr,
    calculate_twrr,
    get_dividend_history,
    calculate_dividend_yield,
    calculate_dividend_income,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_volatility,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)
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


class TestRealizedGains:
    """Test realized gains calculation."""

    def test_calculate_realized_gains_no_sales(self, db, sample_account):
        """Test realized gains with no sales."""
        gains = calculate_realized_gains(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 31), db
        )
        assert gains == 0.0

    def test_calculate_realized_gains_single_sale(self, db, sample_account):
        """Test realized gains from single sale."""
        # BUY
        buy = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        buy.save(db)

        # SELL
        sell = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="AAPL",
            qty=5.0,
            price=160.0,
            fee=3.0,
        )
        sell.save(db)

        gains = calculate_realized_gains(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 31), db
        )

        # Cost basis: 5 * 150.5 (avg price including fee) = 752.5
        # Proceeds: 5 * 160 - 3 = 797
        # Gain: 797 - 752.5 = 44.5
        assert gains == pytest.approx(44.5, abs=0.1)

    def test_get_realized_gains_by_symbol(self, db, sample_account):
        """Test realized gains breakdown by symbol."""
        # BUY AAPL
        buy1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        buy1.save(db)

        # SELL AAPL
        sell1 = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="AAPL",
            qty=5.0,
            price=160.0,
        )
        sell1.save(db)

        # BUY MSFT
        buy2 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="MSFT",
            qty=5.0,
            price=300.0,
        )
        buy2.save(db)

        # SELL MSFT
        sell2 = Transaction(
            date=date(2024, 1, 20),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="MSFT",
            qty=3.0,
            price=310.0,
        )
        sell2.save(db)

        gains_by_symbol = get_realized_gains_by_symbol(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 31), db
        )

        assert "AAPL" in gains_by_symbol
        assert "MSFT" in gains_by_symbol


class TestUnrealizedGains:
    """Test unrealized gains calculation."""

    def test_calculate_unrealized_gains_no_positions(self, db, sample_account):
        """Test unrealized gains with no positions."""
        gains = calculate_unrealized_gains(sample_account.id, date.today(), db)
        assert gains == 0.0

    def test_calculate_unrealized_gains_with_price(self, db, sample_account):
        """Test unrealized gains calculation."""
        # BUY
        buy = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        buy.save(db)

        # Price
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=160.0)
        price.save(db)

        gains = calculate_unrealized_gains(
            sample_account.id, date(2024, 1, 1), db
        )

        # Cost basis: 1500 + 5 = 1505
        # Current value: 10 * 160 = 1600
        # Unrealized gain: 1600 - 1505 = 95
        assert gains == pytest.approx(95.0, abs=0.1)


class TestReturns:
    """Test return calculations."""

    def test_calculate_total_return(self, db, sample_account):
        """Test total return calculation."""
        # BUY
        buy = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        buy.save(db)

        # Prices
        price1 = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price1.save(db)
        price2 = Price(symbol="AAPL", date=date(2024, 1, 31), close=160.0)
        price2.save(db)

        total_return = calculate_total_return(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 31), db
        )

        # Should include unrealized gains
        assert total_return > 0

    def test_calculate_cagr(self, db, sample_account):
        """Test CAGR calculation."""
        # BUY
        buy = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        buy.save(db)

        # Prices
        price1 = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price1.save(db)
        price2 = Price(symbol="AAPL", date=date(2024, 12, 31), close=165.0)
        price2.save(db)

        cagr = calculate_cagr(
            sample_account.id, date(2024, 1, 1), date(2024, 12, 31), db
        )

        # Should be positive for growth
        assert cagr > 0

    def test_calculate_cagr_zero_start(self, db, sample_account):
        """Test CAGR with zero start value."""
        cagr = calculate_cagr(
            sample_account.id, date(2024, 1, 1), date(2024, 12, 31), db
        )
        assert cagr == 0.0


class TestDividends:
    """Test dividend analytics."""

    def test_get_dividend_history(self, db, sample_account):
        """Test getting dividend history."""
        # Dividend
        div = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="DIVIDEND",
            symbol="AAPL",
            qty=10.0,
            price=2.5,  # $2.50 per share
        )
        div.save(db)

        dividends = get_dividend_history(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 31), db
        )

        assert len(dividends) == 1
        assert dividends[0]["type"] == "DIVIDEND"
        assert dividends[0]["amount"] == pytest.approx(25.0)

    def test_calculate_dividend_income(self, db, sample_account):
        """Test dividend income calculation."""
        div1 = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="DIVIDEND",
            symbol="AAPL",
            qty=10.0,
            price=2.5,
        )
        div1.save(db)

        div2 = Transaction(
            date=date(2024, 2, 15),
            account_id=sample_account.id,
            transaction_type="DIVIDEND",
            symbol="AAPL",
            qty=10.0,
            price=2.5,
        )
        div2.save(db)

        income = calculate_dividend_income(
            sample_account.id, date(2024, 1, 1), date(2024, 2, 28), db
        )

        assert income == pytest.approx(50.0)


class TestRiskMetrics:
    """Test risk metrics calculations."""

    def test_calculate_max_drawdown(self, db, sample_account):
        """Test maximum drawdown calculation."""
        # Create transactions and prices over time
        buy = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        buy.save(db)

        # Prices showing a drawdown
        prices = [
            (date(2024, 1, 1), 150.0),
            (date(2024, 1, 2), 160.0),  # Peak
            (date(2024, 1, 3), 140.0),  # Trough (20% drawdown)
            (date(2024, 1, 4), 155.0),
        ]

        for price_date, price_value in prices:
            price = Price(symbol="AAPL", date=price_date, close=price_value)
            price.save(db)

        drawdown = calculate_max_drawdown(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 4), db
        )

        # Should detect the drawdown from 160 to 140
        assert drawdown > 0
        assert drawdown <= 1.0  # Should be between 0 and 1


class TestMetricsCalculator:
    """Test MetricsCalculator class."""

    def test_calculator_initialization(self, db):
        """Test MetricsCalculator initialization."""
        calculator = MetricsCalculator(db=db)
        assert calculator.db is not None
        assert calculator.portfolio_engine is not None

    def test_calculator_with_engine(self, db, sample_account):
        """Test MetricsCalculator with PortfolioEngine."""
        engine = PortfolioEngine(db=db)
        calculator = MetricsCalculator(portfolio_engine=engine)
        assert calculator.portfolio_engine is engine

    def test_calculator_realized_gains(self, db, sample_account):
        """Test calculator realized gains method."""
        buy = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        buy.save(db)

        sell = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="AAPL",
            qty=5.0,
            price=160.0,
        )
        sell.save(db)

        calculator = MetricsCalculator(db=db)
        gains = calculator.calculate_realized_gains(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 31)
        )

        assert gains > 0

    def test_calculator_clear_cache(self, db):
        """Test clearing calculator cache."""
        calculator = MetricsCalculator(db=db)
        calculator._cache["test"] = "value"
        calculator.clear_cache()
        assert len(calculator._cache) == 0


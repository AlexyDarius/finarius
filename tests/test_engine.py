"""Tests for portfolio engine module."""

import pytest
import tempfile
import os
from datetime import date, timedelta
from unittest.mock import Mock, patch

from finarius_app.core.database import init_db, Database
from finarius_app.core.models import Account, Transaction, Price
from finarius_app.core.engine import (
    PortfolioEngine,
    get_positions,
    get_all_positions,
    get_current_positions,
    get_position_history,
    calculate_pru,
    get_pru_history,
    calculate_portfolio_value,
    calculate_portfolio_value_over_time,
    get_portfolio_breakdown,
    get_cash_flows,
    calculate_net_cash_flow,
    get_cash_balance,
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
def sample_price_downloader():
    """Create a mock price downloader."""
    downloader = Mock()
    return downloader


class TestPositions:
    """Test position tracking functions."""

    def test_get_positions_empty(self, db, sample_account):
        """Test getting positions for empty portfolio."""
        positions = get_positions(sample_account.id, date.today(), db)
        assert positions == {}

    def test_get_positions_single_buy(self, db, sample_account):
        """Test getting positions after single BUY transaction."""
        # Create BUY transaction
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction.save(db)

        positions = get_positions(sample_account.id, date(2024, 1, 1), db)
        assert "AAPL" in positions
        assert positions["AAPL"]["qty"] == 10.0
        assert positions["AAPL"]["cost_basis"] == 1500.0 + 5.0  # qty * price + fee
        assert positions["AAPL"]["avg_price"] == pytest.approx(150.5)  # cost_basis / qty

    def test_get_positions_multiple_buys(self, db, sample_account):
        """Test getting positions after multiple BUY transactions."""
        # First BUY
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction1.save(db)

        # Second BUY
        transaction2 = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=5.0,
            price=160.0,
            fee=3.0,
        )
        transaction2.save(db)

        positions = get_positions(sample_account.id, date(2024, 1, 20), db)
        assert "AAPL" in positions
        assert positions["AAPL"]["qty"] == 15.0
        assert positions["AAPL"]["cost_basis"] == pytest.approx(1500.0 + 5.0 + 800.0 + 3.0)
        assert positions["AAPL"]["avg_price"] == pytest.approx(
            (1500.0 + 5.0 + 800.0 + 3.0) / 15.0
        )

    def test_get_positions_buy_and_sell(self, db, sample_account):
        """Test getting positions after BUY and SELL transactions."""
        # BUY
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction1.save(db)

        # SELL
        transaction2 = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="AAPL",
            qty=4.0,
            price=160.0,
            fee=3.0,
        )
        transaction2.save(db)

        positions = get_positions(sample_account.id, date(2024, 1, 20), db)
        assert "AAPL" in positions
        assert positions["AAPL"]["qty"] == 6.0  # 10 - 4
        # Cost basis should be reduced proportionally
        original_cost_basis = 1500.0 + 5.0
        avg_price = original_cost_basis / 10.0
        remaining_cost_basis = 6.0 * avg_price
        assert positions["AAPL"]["cost_basis"] == pytest.approx(remaining_cost_basis)
        assert positions["AAPL"]["avg_price"] == pytest.approx(avg_price)

    def test_get_positions_sell_all(self, db, sample_account):
        """Test getting positions after selling all shares."""
        # BUY
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction1.save(db)

        # SELL all
        transaction2 = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="AAPL",
            qty=10.0,
            price=160.0,
            fee=3.0,
        )
        transaction2.save(db)

        positions = get_positions(sample_account.id, date(2024, 1, 20), db)
        assert "AAPL" not in positions  # Should be removed when qty is 0

    def test_get_all_positions(self, db):
        """Test getting positions across all accounts."""
        account1 = Account(name="Account 1", currency="USD")
        account1.save(db)
        account2 = Account(name="Account 2", currency="USD")
        account2.save(db)

        # Add transactions to both accounts
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=account1.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        transaction1.save(db)

        transaction2 = Transaction(
            date=date(2024, 1, 1),
            account_id=account2.id,
            transaction_type="BUY",
            symbol="MSFT",
            qty=5.0,
            price=300.0,
        )
        transaction2.save(db)

        all_positions = get_all_positions(date(2024, 1, 1), db)
        assert account1.id in all_positions
        assert account2.id in all_positions
        assert "AAPL" in all_positions[account1.id]
        assert "MSFT" in all_positions[account2.id]

    def test_get_current_positions(self, db, sample_account):
        """Test getting current positions."""
        transaction = Transaction(
            date=date.today() - timedelta(days=10),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        transaction.save(db)

        positions = get_current_positions(sample_account.id, db)
        assert "AAPL" in positions

    def test_get_position_history(self, db, sample_account):
        """Test getting position history over time."""
        # BUY on day 1
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        transaction1.save(db)

        # SELL on day 5
        transaction2 = Transaction(
            date=date(2024, 1, 5),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="AAPL",
            qty=4.0,
            price=160.0,
        )
        transaction2.save(db)

        history = get_position_history(
            "AAPL", sample_account.id, date(2024, 1, 1), date(2024, 1, 10), db
        )

        assert date(2024, 1, 1) in history
        assert date(2024, 1, 5) in history
        assert date(2024, 1, 10) in history
        assert history[date(2024, 1, 1)]["qty"] == 10.0
        assert history[date(2024, 1, 5)]["qty"] == 6.0
        assert history[date(2024, 1, 10)]["qty"] == 6.0


class TestPRU:
    """Test PRU calculation functions."""

    def test_calculate_pru_no_position(self, db, sample_account):
        """Test PRU calculation with no position."""
        pru = calculate_pru("AAPL", sample_account.id, date.today(), db)
        assert pru == 0.0

    def test_calculate_pru_single_buy(self, db, sample_account):
        """Test PRU calculation after single BUY."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction.save(db)

        pru = calculate_pru("AAPL", sample_account.id, date(2024, 1, 1), db)
        expected_pru = (1500.0 + 5.0) / 10.0
        assert pru == pytest.approx(expected_pru)

    def test_calculate_pru_multiple_buys(self, db, sample_account):
        """Test PRU calculation after multiple BUYs."""
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction1.save(db)

        transaction2 = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=5.0,
            price=160.0,
            fee=3.0,
        )
        transaction2.save(db)

        pru = calculate_pru("AAPL", sample_account.id, date(2024, 1, 20), db)
        total_cost = 1500.0 + 5.0 + 800.0 + 3.0
        total_qty = 15.0
        expected_pru = total_cost / total_qty
        assert pru == pytest.approx(expected_pru)

    def test_get_pru_history(self, db, sample_account):
        """Test getting PRU history over time."""
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction1.save(db)

        transaction2 = Transaction(
            date=date(2024, 1, 15),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=5.0,
            price=160.0,
            fee=3.0,
        )
        transaction2.save(db)

        history = get_pru_history(
            "AAPL", sample_account.id, date(2024, 1, 1), date(2024, 1, 20), db
        )

        assert date(2024, 1, 1) in history
        assert date(2024, 1, 15) in history
        assert date(2024, 1, 20) in history


class TestPortfolioValue:
    """Test portfolio value calculation functions."""

    def test_calculate_portfolio_value_no_positions(self, db, sample_account):
        """Test portfolio value with no positions."""
        value = calculate_portfolio_value(sample_account.id, date.today(), db)
        assert value == 0.0

    def test_calculate_portfolio_value_with_price(self, db, sample_account):
        """Test portfolio value calculation with price data."""
        # Create transaction
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        transaction.save(db)

        # Create price
        price = Price(
            symbol="AAPL",
            date=date(2024, 1, 1),
            close=160.0,
        )
        price.save(db)

        value = calculate_portfolio_value(sample_account.id, date(2024, 1, 1), db)
        assert value == pytest.approx(10.0 * 160.0)

    @patch("finarius_app.core.engine.portfolio_value.PriceDownloader")
    def test_calculate_portfolio_value_no_price_uses_cost_basis(
        self, mock_downloader_class, db, sample_account
    ):
        """Test portfolio value falls back to cost basis when price unavailable."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction.save(db)

        # Mock price downloader to return None (no price available)
        mock_downloader = Mock()
        mock_downloader.download_price.return_value = None
        mock_downloader_class.return_value = mock_downloader

        value = calculate_portfolio_value(
            sample_account.id, date(2024, 1, 1), db, mock_downloader
        )
        # Should use cost basis when price not available
        assert value == pytest.approx(1500.0 + 5.0)

    @patch("finarius_app.core.engine.portfolio_value.PriceDownloader")
    def test_calculate_portfolio_value_downloads_price(
        self, mock_downloader_class, db, sample_account
    ):
        """Test portfolio value downloads price when not in database."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        transaction.save(db)

        # Mock price downloader
        mock_downloader = Mock()
        mock_price = Price(symbol="AAPL", date=date(2024, 1, 1), close=160.0)
        mock_downloader.download_price.return_value = mock_price
        mock_downloader_class.return_value = mock_downloader

        value = calculate_portfolio_value(
            sample_account.id, date(2024, 1, 1), db, mock_downloader
        )
        assert value == pytest.approx(10.0 * 160.0)
        mock_downloader.download_price.assert_called_once()

    def test_get_portfolio_breakdown(self, db, sample_account):
        """Test portfolio breakdown."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction.save(db)

        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=160.0)
        price.save(db)

        breakdown = get_portfolio_breakdown(
            sample_account.id, date(2024, 1, 1), db
        )

        assert "AAPL" in breakdown
        assert breakdown["AAPL"]["qty"] == 10.0
        assert breakdown["AAPL"]["cost_basis"] == pytest.approx(1500.0 + 5.0)
        assert breakdown["AAPL"]["current_value"] == pytest.approx(10.0 * 160.0)
        assert breakdown["AAPL"]["unrealized_gain"] == pytest.approx(
            (10.0 * 160.0) - (1500.0 + 5.0)
        )


class TestCashFlows:
    """Test cash flow tracking functions."""

    def test_get_cash_flows_deposit(self, db, sample_account):
        """Test getting DEPOSIT cash flows."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="DEPOSIT",
            qty=1000.0,
        )
        transaction.save(db)

        cash_flows = get_cash_flows(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 1), db
        )

        assert len(cash_flows) == 1
        assert cash_flows[0]["type"] == "DEPOSIT"
        assert cash_flows[0]["amount"] == 1000.0

    def test_get_cash_flows_withdraw(self, db, sample_account):
        """Test getting WITHDRAW cash flows."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="WITHDRAW",
            qty=500.0,
        )
        transaction.save(db)

        cash_flows = get_cash_flows(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 1), db
        )

        assert len(cash_flows) == 1
        assert cash_flows[0]["type"] == "WITHDRAW"
        assert cash_flows[0]["amount"] == -500.0

    def test_get_cash_flows_dividend(self, db, sample_account):
        """Test getting DIVIDEND cash flows."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="DIVIDEND",
            symbol="AAPL",
            qty=10.0,
            price=2.5,  # $2.50 per share dividend
        )
        transaction.save(db)

        cash_flows = get_cash_flows(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 1), db
        )

        assert len(cash_flows) == 1
        assert cash_flows[0]["type"] == "DIVIDEND"
        assert cash_flows[0]["amount"] == pytest.approx(10.0 * 2.5)
        assert cash_flows[0]["symbol"] == "AAPL"

    def test_calculate_net_cash_flow(self, db, sample_account):
        """Test calculating net cash flow."""
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="DEPOSIT",
            qty=1000.0,
        )
        transaction1.save(db)

        transaction2 = Transaction(
            date=date(2024, 1, 2),
            account_id=sample_account.id,
            transaction_type="WITHDRAW",
            qty=300.0,
        )
        transaction2.save(db)

        net = calculate_net_cash_flow(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 2), db
        )
        assert net == pytest.approx(1000.0 - 300.0)

    def test_get_cash_balance(self, db, sample_account):
        """Test getting cash balance."""
        # Deposit
        transaction1 = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="DEPOSIT",
            qty=1000.0,
        )
        transaction1.save(db)

        # Buy stock (cash outflow)
        transaction2 = Transaction(
            date=date(2024, 1, 2),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=5.0,
            price=150.0,
            fee=5.0,
        )
        transaction2.save(db)

        # Sell stock (cash inflow)
        transaction3 = Transaction(
            date=date(2024, 1, 3),
            account_id=sample_account.id,
            transaction_type="SELL",
            symbol="AAPL",
            qty=2.0,
            price=160.0,
            fee=3.0,
        )
        transaction3.save(db)

        balance = get_cash_balance(sample_account.id, date(2024, 1, 3), db)
        # 1000 (deposit) - 755 (buy: 5*150+5) + 317 (sell: 2*160-3)
        expected = 1000.0 - (5.0 * 150.0 + 5.0) + (2.0 * 160.0 - 3.0)
        assert balance == pytest.approx(expected)


class TestPortfolioEngine:
    """Test PortfolioEngine class."""

    def test_engine_initialization(self, db):
        """Test PortfolioEngine initialization."""
        engine = PortfolioEngine(db=db)
        assert engine.db is not None
        assert engine.price_downloader is not None

    def test_engine_clear_cache(self, db):
        """Test clearing engine cache."""
        engine = PortfolioEngine(db=db)
        engine._cache["test"] = "value"
        engine.clear_cache()
        assert len(engine._cache) == 0

    def test_engine_get_positions(self, db, sample_account):
        """Test engine get_positions method."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        transaction.save(db)

        engine = PortfolioEngine(db=db)
        positions = engine.get_positions(sample_account.id, date(2024, 1, 1))
        assert "AAPL" in positions

    def test_engine_calculate_pru(self, db, sample_account):
        """Test engine calculate_pru method."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
            fee=5.0,
        )
        transaction.save(db)

        engine = PortfolioEngine(db=db)
        pru = engine.calculate_pru("AAPL", sample_account.id, date(2024, 1, 1))
        assert pru > 0

    def test_engine_calculate_portfolio_value(self, db, sample_account):
        """Test engine calculate_portfolio_value method."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10.0,
            price=150.0,
        )
        transaction.save(db)

        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=160.0)
        price.save(db)

        engine = PortfolioEngine(db=db)
        value = engine.calculate_portfolio_value(sample_account.id, date(2024, 1, 1))
        assert value == pytest.approx(10.0 * 160.0)

    def test_engine_get_cash_flows(self, db, sample_account):
        """Test engine get_cash_flows method."""
        transaction = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="DEPOSIT",
            qty=1000.0,
        )
        transaction.save(db)

        engine = PortfolioEngine(db=db)
        cash_flows = engine.get_cash_flows(
            sample_account.id, date(2024, 1, 1), date(2024, 1, 1)
        )
        assert len(cash_flows) == 1


"""Tests for models module."""

import pytest
import sqlite3
import tempfile
import os
from datetime import date, timedelta
from finarius_app.core.database import init_db, Database
from finarius_app.core.models import (
    Account,
    Transaction,
    Price,
    get_account_by_id,
    get_account_by_name,
    get_all_accounts,
    get_transaction_by_id,
    get_transactions_by_account,
    get_transactions_by_symbol,
    get_price,
    get_prices,
    get_latest_price,
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


class TestAccount:
    """Test Account model."""

    def test_account_creation(self, db):
        """Test creating an account."""
        account = Account(name="My Account", currency="EUR")
        assert account.name == "My Account"
        assert account.currency == "EUR"
        assert account.id is None

    def test_account_save_new(self, db):
        """Test saving a new account."""
        account = Account(name="New Account", currency="USD")
        account.save(db)
        assert account.id is not None
        assert account.created_at is not None
        assert account.updated_at is not None

    def test_account_save_existing(self, db, sample_account):
        """Test updating an existing account."""
        original_name = sample_account.name
        sample_account.name = "Updated Account"
        sample_account.save(db)
        assert sample_account.name == "Updated Account"
        assert sample_account.id is not None

        # Verify in database
        result = db.fetchone("SELECT name FROM accounts WHERE id = ?", (sample_account.id,))
        assert result["name"] == "Updated Account"

    def test_account_delete(self, db, sample_account):
        """Test deleting an account."""
        account_id = sample_account.id
        sample_account.delete(db)
        assert sample_account.id is None

        # Verify deleted
        result = db.fetchone("SELECT * FROM accounts WHERE id = ?", (account_id,))
        assert result is None

    def test_account_delete_without_id(self, db):
        """Test deleting account without ID raises error."""
        account = Account(name="Test", currency="USD")
        with pytest.raises(ValueError, match="Cannot delete account without ID"):
            account.delete(db)

    def test_account_update(self, db, sample_account):
        """Test updating account fields."""
        sample_account.update(name="Updated", currency="EUR")
        assert sample_account.name == "Updated"
        assert sample_account.currency == "EUR"

    def test_account_to_dict(self, sample_account):
        """Test converting account to dictionary."""
        data = sample_account.to_dict()
        assert data["id"] == sample_account.id
        assert data["name"] == sample_account.name
        assert data["currency"] == sample_account.currency
        assert "created_at" in data

    def test_account_from_dict(self):
        """Test creating account from dictionary."""
        data = {
            "id": 1,
            "name": "Test Account",
            "currency": "USD",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
        }
        account = Account.from_dict(data)
        assert account.id == 1
        assert account.name == "Test Account"
        assert account.currency == "USD"

    def test_account_validation_empty_name(self):
        """Test account validation with empty name."""
        account = Account(name="", currency="USD")
        with pytest.raises(ValueError, match="Account name cannot be empty"):
            account.validate()

    def test_account_validation_invalid_currency(self):
        """Test account validation with invalid currency."""
        account = Account(name="Test", currency="US")
        with pytest.raises(ValueError, match="Currency must be a 3-letter code"):
            account.validate()

    def test_account_unique_constraint(self, db):
        """Test account unique name constraint."""
        account1 = Account(name="Unique Account", currency="USD")
        account1.save(db)

        account2 = Account(name="Unique Account", currency="EUR")
        with pytest.raises(sqlite3.IntegrityError):
            account2.save(db)


class TestTransaction:
    """Test Transaction model."""

    def test_transaction_creation(self, sample_account):
        """Test creating a transaction."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        assert txn.date == date(2024, 1, 1)
        assert txn.account_id == sample_account.id
        assert txn.type == "BUY"
        assert txn.symbol == "AAPL"
        assert txn.qty == 10
        assert txn.price == 150.0

    def test_transaction_save_new(self, db, sample_account):
        """Test saving a new transaction."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        txn.save(db)
        assert txn.id is not None
        assert txn.created_at is not None

    def test_transaction_save_existing(self, db, sample_account):
        """Test updating an existing transaction."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        txn.save(db)
        original_id = txn.id

        txn.qty = 20
        txn.save(db)
        assert txn.id == original_id

        # Verify update
        result = db.fetchone("SELECT qty FROM transactions WHERE id = ?", (txn.id,))
        assert result["qty"] == 20

    def test_transaction_delete(self, db, sample_account):
        """Test deleting a transaction."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        txn.save(db)
        txn_id = txn.id
        txn.delete(db)
        assert txn.id is None

        # Verify deleted
        result = db.fetchone("SELECT * FROM transactions WHERE id = ?", (txn_id,))
        assert result is None

    def test_transaction_delete_without_id(self, db, sample_account):
        """Test deleting transaction without ID raises error."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        with pytest.raises(ValueError, match="Cannot delete transaction without ID"):
            txn.delete(db)

    def test_transaction_update(self, sample_account):
        """Test updating transaction fields."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        txn.update(qty=20, price=160.0)
        assert txn.qty == 20
        assert txn.price == 160.0

    def test_transaction_to_dict(self, sample_account):
        """Test converting transaction to dictionary."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        data = txn.to_dict()
        assert data["date"] == "2024-01-01"
        assert data["account_id"] == sample_account.id
        assert data["type"] == "BUY"
        assert data["symbol"] == "AAPL"

    def test_transaction_from_dict(self, sample_account):
        """Test creating transaction from dictionary."""
        data = {
            "id": 1,
            "date": "2024-01-01",
            "account_id": sample_account.id,
            "type": "BUY",
            "symbol": "AAPL",
            "qty": 10,
            "price": 150.0,
            "fee": 1.0,
            "notes": "Test",
        }
        txn = Transaction.from_dict(data)
        assert txn.id == 1
        assert txn.date == date(2024, 1, 1)
        assert txn.type == "BUY"

    def test_transaction_validation_invalid_type(self, sample_account):
        """Test transaction validation with invalid type."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="INVALID",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        with pytest.raises(ValueError, match="Invalid transaction type"):
            txn.validate()

    def test_transaction_validation_missing_symbol_buy(self, sample_account):
        """Test transaction validation for BUY without symbol."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            qty=10,
            price=150.0,
        )
        with pytest.raises(ValueError, match="Symbol is required"):
            txn.validate()

    def test_transaction_validation_negative_qty(self, sample_account):
        """Test transaction validation with negative quantity."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=-10,
            price=150.0,
        )
        with pytest.raises(ValueError, match="Quantity must be positive"):
            txn.validate()

    def test_transaction_validation_negative_price(self, sample_account):
        """Test transaction validation with negative price."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=-150.0,
        )
        with pytest.raises(ValueError, match="Price must be non-negative"):
            txn.validate()

    def test_transaction_foreign_key_constraint(self, db):
        """Test transaction foreign key constraint."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=999,  # Non-existent account
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        with pytest.raises(sqlite3.IntegrityError):
            txn.save(db)

    def test_transaction_get_account(self, db, sample_account):
        """Test getting associated account."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        txn.save(db)
        account = txn.get_account(db)
        assert account is not None
        assert account.id == sample_account.id
        assert account.name == sample_account.name

    def test_transaction_types(self, db, sample_account):
        """Test all transaction types."""
        types = ["BUY", "SELL", "DIVIDEND", "DEPOSIT", "WITHDRAW"]
        for txn_type in types:
            if txn_type in ["DEPOSIT", "WITHDRAW"]:
                txn = Transaction(
                    date=date(2024, 1, 1),
                    account_id=sample_account.id,
                    transaction_type=txn_type,
                )
            elif txn_type == "DIVIDEND":
                txn = Transaction(
                    date=date(2024, 1, 1),
                    account_id=sample_account.id,
                    transaction_type=txn_type,
                    symbol="AAPL",
                    qty=10,
                )
            else:
                txn = Transaction(
                    date=date(2024, 1, 1),
                    account_id=sample_account.id,
                    transaction_type=txn_type,
                    symbol="AAPL",
                    qty=10,
                    price=150.0,
                )
            txn.save(db)
            assert txn.id is not None


class TestPrice:
    """Test Price model."""

    def test_price_creation(self):
        """Test creating a price."""
        price = Price(
            symbol="AAPL",
            date=date(2024, 1, 1),
            close=150.0,
            open_price=149.0,
            high=151.0,
            low=148.0,
            volume=1000000,
        )
        assert price.symbol == "AAPL"
        assert price.date == date(2024, 1, 1)
        assert price.close == 150.0
        assert price.open == 149.0

    def test_price_save(self, db):
        """Test saving a price."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.save(db)
        assert price.created_at is not None

        # Verify saved
        result = db.fetchone(
            "SELECT * FROM prices WHERE symbol = ? AND date = ?",
            ("AAPL", "2024-01-01"),
        )
        assert result is not None
        assert result["close"] == 150.0

    def test_price_save_update(self, db):
        """Test updating an existing price."""
        price1 = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price1.save(db)

        price2 = Price(symbol="AAPL", date=date(2024, 1, 1), close=155.0)
        price2.save(db)

        # Should update, not create duplicate
        result = db.fetchall(
            "SELECT * FROM prices WHERE symbol = ? AND date = ?",
            ("AAPL", "2024-01-01"),
        )
        assert len(result) == 1
        assert result[0]["close"] == 155.0

    def test_price_delete(self, db):
        """Test deleting a price."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.save(db)
        price.delete(db)

        # Verify deleted
        result = db.fetchone(
            "SELECT * FROM prices WHERE symbol = ? AND date = ?",
            ("AAPL", "2024-01-01"),
        )
        assert result is None

    def test_price_update(self):
        """Test updating price fields."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.update(close=155.0, high=156.0)
        assert price.close == 155.0
        assert price.high == 156.0

    def test_price_to_dict(self):
        """Test converting price to dictionary."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        data = price.to_dict()
        assert data["symbol"] == "AAPL"
        assert data["date"] == "2024-01-01"
        assert data["close"] == 150.0

    def test_price_from_dict(self):
        """Test creating price from dictionary."""
        data = {
            "symbol": "AAPL",
            "date": "2024-01-01",
            "close": 150.0,
            "open": 149.0,
            "high": 151.0,
            "low": 148.0,
            "volume": 1000000,
        }
        price = Price.from_dict(data)
        assert price.symbol == "AAPL"
        assert price.date == date(2024, 1, 1)
        assert price.close == 150.0

    def test_price_validation_empty_symbol(self):
        """Test price validation with empty symbol."""
        price = Price(symbol="", date=date(2024, 1, 1), close=150.0)
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            price.validate()

    def test_price_validation_negative_close(self):
        """Test price validation with negative close price."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=-150.0)
        with pytest.raises(ValueError, match="Close price must be positive"):
            price.validate()

    def test_price_validation_high_less_than_low(self):
        """Test price validation with high < low."""
        price = Price(
            symbol="AAPL",
            date=date(2024, 1, 1),
            close=150.0,
            high=148.0,
            low=149.0,
        )
        with pytest.raises(ValueError, match="High price cannot be less than low price"):
            price.validate()


class TestQueryHelpers:
    """Test query helper functions."""

    def test_get_account_by_id(self, db, sample_account):
        """Test getting account by ID."""
        account = get_account_by_id(sample_account.id, db)
        assert account is not None
        assert account.id == sample_account.id
        assert account.name == sample_account.name

    def test_get_account_by_id_not_found(self, db):
        """Test getting non-existent account by ID."""
        account = get_account_by_id(999, db)
        assert account is None

    def test_get_account_by_name(self, db, sample_account):
        """Test getting account by name."""
        account = get_account_by_name(sample_account.name, db)
        assert account is not None
        assert account.name == sample_account.name

    def test_get_account_by_name_not_found(self, db):
        """Test getting non-existent account by name."""
        account = get_account_by_name("Non-existent", db)
        assert account is None

    def test_get_all_accounts(self, db):
        """Test getting all accounts."""
        # Create multiple accounts
        for i in range(3):
            account = Account(name=f"Account {i}", currency="USD")
            account.save(db)

        accounts = get_all_accounts(db)
        assert len(accounts) >= 3
        # Should be ordered by name
        names = [acc.name for acc in accounts]
        assert names == sorted(names)

    def test_get_transaction_by_id(self, db, sample_account):
        """Test getting transaction by ID."""
        txn = Transaction(
            date=date(2024, 1, 1),
            account_id=sample_account.id,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0,
        )
        txn.save(db)

        retrieved = get_transaction_by_id(txn.id, db)
        assert retrieved is not None
        assert retrieved.id == txn.id
        assert retrieved.symbol == "AAPL"

    def test_get_transactions_by_account(self, db, sample_account):
        """Test getting transactions by account."""
        # Create multiple transactions
        for i in range(3):
            txn = Transaction(
                date=date(2024, 1, i + 1),
                account_id=sample_account.id,
                transaction_type="BUY",
                symbol="AAPL",
                qty=10,
                price=150.0,
            )
            txn.save(db)

        transactions = get_transactions_by_account(sample_account.id, db=db)
        assert len(transactions) >= 3

    def test_get_transactions_by_account_date_range(self, db, sample_account):
        """Test getting transactions by account with date range."""
        # Create transactions on different dates
        dates = [date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 1)]
        for d in dates:
            txn = Transaction(
                date=d,
                account_id=sample_account.id,
                transaction_type="BUY",
                symbol="AAPL",
                qty=10,
                price=150.0,
            )
            txn.save(db)

        # Get transactions in January
        transactions = get_transactions_by_account(
            sample_account.id,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            db=db,
        )
        assert len(transactions) == 2

    def test_get_transactions_by_symbol(self, db, sample_account):
        """Test getting transactions by symbol."""
        # Create transactions for different symbols
        symbols = ["AAPL", "GOOGL", "AAPL"]
        for symbol in symbols:
            txn = Transaction(
                date=date(2024, 1, 1),
                account_id=sample_account.id,
                transaction_type="BUY",
                symbol=symbol,
                qty=10,
                price=150.0,
            )
            txn.save(db)

        transactions = get_transactions_by_symbol("AAPL", db=db)
        assert len(transactions) >= 2

    def test_get_price(self, db):
        """Test getting price by symbol and date."""
        price = Price(symbol="AAPL", date=date(2024, 1, 1), close=150.0)
        price.save(db)

        retrieved = get_price("AAPL", date(2024, 1, 1), db)
        assert retrieved is not None
        assert retrieved.close == 150.0

    def test_get_price_not_found(self, db):
        """Test getting non-existent price."""
        price = get_price("AAPL", date(2024, 1, 1), db)
        assert price is None

    def test_get_prices(self, db):
        """Test getting price range."""
        # Create prices for multiple dates
        for i in range(5):
            price = Price(
                symbol="AAPL",
                date=date(2024, 1, i + 1),
                close=150.0 + i,
            )
            price.save(db)

        prices = get_prices("AAPL", db=db)
        assert len(prices) == 5
        # Should be ordered by date ascending
        assert prices[0].date < prices[-1].date

    def test_get_prices_date_range(self, db):
        """Test getting prices with date range."""
        # Create prices for different dates
        dates = [date(2024, 1, 1), date(2024, 1, 15), date(2024, 2, 1)]
        for d in dates:
            price = Price(symbol="AAPL", date=d, close=150.0)
            price.save(db)

        # Get prices in January
        prices = get_prices(
            "AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            db=db,
        )
        assert len(prices) == 2

    def test_get_latest_price(self, db):
        """Test getting latest price."""
        # Create prices for different dates
        dates = [
            date(2024, 1, 1),
            date(2024, 1, 15),
            date(2024, 2, 1),
        ]
        for d in dates:
            price = Price(symbol="AAPL", date=d, close=150.0)
            price.save(db)

        latest = get_latest_price("AAPL", db)
        assert latest is not None
        assert latest.date == date(2024, 2, 1)

    def test_get_latest_price_not_found(self, db):
        """Test getting latest price when none exists."""
        latest = get_latest_price("NONEXISTENT", db)
        assert latest is None


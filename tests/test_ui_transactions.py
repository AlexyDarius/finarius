"""Tests for UI transactions module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from finarius_app.core.models import Transaction, Account
from finarius_app.ui.transactions import (
    render_transactions_page,
    TRANSACTION_TYPES,
)
from finarius_app.ui.transactions.filters import get_filtered_transactions
from finarius_app.ui.transactions.csv import generate_csv


class TestTransactionsUI:
    """Test transactions UI module."""

    def test_transaction_types_constant(self):
        """Test that TRANSACTION_TYPES constant is defined."""
        assert isinstance(TRANSACTION_TYPES, list)
        assert len(TRANSACTION_TYPES) == 5
        assert "BUY" in TRANSACTION_TYPES
        assert "SELL" in TRANSACTION_TYPES
        assert "DIVIDEND" in TRANSACTION_TYPES
        assert "DEPOSIT" in TRANSACTION_TYPES
        assert "WITHDRAW" in TRANSACTION_TYPES

    @patch("finarius_app.ui.transactions.page.get_db")
    @patch("finarius_app.ui.transactions.page.st")
    def test_render_transactions_page_no_db(self, mock_st, mock_get_db):
        """Test rendering transactions page when database is not initialized."""
        mock_get_db.return_value = None
        mock_st.error = MagicMock()
        mock_st.title = MagicMock()

        render_transactions_page()

        mock_st.error.assert_called_once_with("Database not initialized")
        mock_st.title.assert_called_once_with("💸 Transactions")

    @patch("finarius_app.ui.transactions.page.get_all_accounts")
    @patch("finarius_app.ui.transactions.page.get_db")
    @patch("finarius_app.ui.transactions.page.st")
    def test_render_transactions_page_no_accounts(self, mock_st, mock_get_db, mock_get_all_accounts):
        """Test rendering transactions page with no accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_all_accounts.return_value = []
        mock_st.title = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.info = MagicMock()

        render_transactions_page()

        mock_st.warning.assert_called_once()
        mock_get_all_accounts.assert_called_once_with(mock_db)

    @patch("finarius_app.ui.transactions.page.get_all_accounts")
    @patch("finarius_app.ui.transactions.filters.get_transactions_by_account")
    @patch("finarius_app.ui.transactions.page.get_db")
    @patch("finarius_app.ui.transactions.filters.st")
    @patch("finarius_app.ui.transactions.page.st")
    def test_render_transactions_page_with_accounts(
        self, mock_st_page, mock_st_filters, mock_get_db, mock_get_transactions, mock_get_all_accounts
    ):
        """Test rendering transactions page with accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        account = Account(name="Test Account", currency="USD", account_id=1)
        mock_get_all_accounts.return_value = [account]
        mock_get_transactions.return_value = []
        
        # Setup filters st mock
        mock_st_filters.subheader = MagicMock()
        mock_st_filters.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
        mock_st_filters.selectbox = MagicMock(return_value="All Accounts")
        mock_st_filters.date_input = MagicMock(return_value=(date.today() - timedelta(days=30), date.today()))
        mock_st_filters.text_input = MagicMock(return_value="")
        
        # Setup page st mock
        mock_st_page.title = MagicMock()
        mock_st_page.markdown = MagicMock()
        mock_st_page.subheader = MagicMock()
        mock_st_page.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
        mock_st_page.download_button = MagicMock()
        mock_st_page.info = MagicMock()
        mock_st_page.button = MagicMock(return_value=False)
        mock_st_page.session_state = {}
        mock_st_page.dataframe = MagicMock()

        render_transactions_page()

        mock_get_all_accounts.assert_called_once_with(mock_db)

    def test_get_filtered_transactions_by_account(self):
        """Test filtering transactions by account."""
        mock_db = MagicMock()
        
        account1 = Account(name="Account 1", currency="USD", account_id=1)
        account2 = Account(name="Account 2", currency="USD", account_id=2)
        
        transaction1 = Transaction(
            date=date.today(),
            account_id=1,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0
        )
        transaction2 = Transaction(
            date=date.today(),
            account_id=2,
            transaction_type="BUY",
            symbol="MSFT",
            qty=5,
            price=200.0
        )
        
        with patch("finarius_app.ui.transactions.filters.get_transactions_by_account") as mock_get:
            mock_get.return_value = [transaction1]
            
            filters = {
                "account_id": 1,
                "start_date": date.today() - timedelta(days=30),
                "end_date": date.today(),
                "symbol": None,
                "type": None,
            }
            
            result = get_filtered_transactions(filters, mock_db)
            
            assert len(result) == 1
            assert result[0].account_id == 1

    def test_get_filtered_transactions_by_symbol(self):
        """Test filtering transactions by symbol."""
        mock_db = MagicMock()
        
        transaction1 = Transaction(
            date=date.today(),
            account_id=1,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0
        )
        transaction2 = Transaction(
            date=date.today(),
            account_id=1,
            transaction_type="BUY",
            symbol="MSFT",
            qty=5,
            price=200.0
        )
        
        filters = {
            "account_id": 1,  # Use specific account to avoid date filtering issues
            "start_date": date.today() - timedelta(days=30),
            "end_date": date.today(),
            "symbol": "AAPL",
            "type": None,
        }
        
        with patch("finarius_app.ui.transactions.filters.get_transactions_by_account") as mock_get_txns:
            # Return both transactions when called for the account
            mock_get_txns.return_value = [transaction1, transaction2]
            
            result = get_filtered_transactions(filters, mock_db)
            
            # Filtering by symbol happens after getting all transactions
            # The filter checks: t.symbol and t.symbol.upper() == filters["symbol"]
            assert len(result) == 1
            assert result[0].symbol == "AAPL"

    def test_get_filtered_transactions_by_type(self):
        """Test filtering transactions by type."""
        mock_db = MagicMock()
        
        transaction1 = Transaction(
            date=date.today(),
            account_id=1,
            transaction_type="BUY",
            symbol="AAPL",
            qty=10,
            price=150.0
        )
        transaction2 = Transaction(
            date=date.today(),
            account_id=1,
            transaction_type="SELL",
            symbol="AAPL",
            qty=5,
            price=160.0
        )
        
        filters = {
            "account_id": 1,  # Use specific account to avoid date filtering issues
            "start_date": date.today() - timedelta(days=30),
            "end_date": date.today(),
            "symbol": None,
            "type": "BUY",
        }
        
        with patch("finarius_app.ui.transactions.filters.get_transactions_by_account") as mock_get_txns:
            # Return both transactions when called for the account
            mock_get_txns.return_value = [transaction1, transaction2]
            
            result = get_filtered_transactions(filters, mock_db)
            
            # Filtering by type happens after getting all transactions
            # The filter checks: t.type == filters["type"]
            assert len(result) == 1
            assert result[0].type == "BUY"

    def test_generate_csv(self):
        """Test CSV generation from transactions."""
        transactions = [
            Transaction(
                date=date(2024, 1, 1),
                account_id=1,
                transaction_type="BUY",
                symbol="AAPL",
                qty=10,
                price=150.0,
                fee=1.0,
                notes="Test transaction",
                transaction_id=1
            )
        ]
        
        csv_data = generate_csv(transactions)
        
        assert "ID" in csv_data
        assert "Date" in csv_data
        assert "Account ID" in csv_data
        assert "Type" in csv_data
        assert "Symbol" in csv_data
        assert "AAPL" in csv_data
        assert "BUY" in csv_data


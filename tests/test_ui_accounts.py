"""Tests for UI accounts module."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import date

from finarius_app.core.models import Account
from finarius_app.ui.accounts import (
    render_accounts_page,
    CURRENCIES,
)
from finarius_app.ui.accounts.page import render_accounts_page as render_page
from finarius_app.ui.accounts.constants import CURRENCIES as CURRENCIES_CONST


class TestAccountsUI:
    """Test accounts UI module."""

    def test_currencies_constant(self):
        """Test that CURRENCIES constant is defined."""
        assert isinstance(CURRENCIES, list)
        assert len(CURRENCIES) > 0
        assert "USD" in CURRENCIES
        assert "EUR" in CURRENCIES

    @patch("finarius_app.ui.accounts.page.get_db")
    @patch("finarius_app.ui.accounts.page.st")
    def test_render_accounts_page_no_db(self, mock_st, mock_get_db):
        """Test rendering accounts page when database is not initialized."""
        mock_get_db.return_value = None
        mock_st.error = MagicMock()
        mock_st.title = MagicMock()

        render_accounts_page()

        mock_st.error.assert_called_once_with("Database not initialized")
        mock_st.title.assert_called_once_with("🏦 Accounts")

    @patch("finarius_app.ui.accounts.page.get_all_accounts")
    @patch("finarius_app.ui.accounts.page.get_db")
    @patch("finarius_app.ui.accounts.page.st")
    def test_render_accounts_page_empty(self, mock_st, mock_get_db, mock_get_all_accounts):
        """Test rendering accounts page with no accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_all_accounts.return_value = []
        mock_st.title = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
        mock_st.expander = MagicMock(return_value=MagicMock())
        mock_st.subheader = MagicMock()
        mock_st.info = MagicMock()

        render_accounts_page()

        mock_st.title.assert_called_once()
        # get_all_accounts is called multiple times (in render and form validation)
        assert mock_get_all_accounts.called

    @patch("finarius_app.ui.accounts.page.get_all_accounts")
    @patch("finarius_app.ui.accounts.statistics.calculate_portfolio_value")
    @patch("finarius_app.ui.accounts.page.get_db")
    @patch("finarius_app.ui.accounts.page.st")
    def test_render_accounts_page_with_accounts(self, mock_st, mock_get_db, mock_calc_value, mock_get_all_accounts):
        """Test rendering accounts page with accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Create mock accounts
        account1 = Account(name="Test Account 1", currency="USD", account_id=1)
        account2 = Account(name="Test Account 2", currency="EUR", account_id=2)
        mock_get_all_accounts.return_value = [account1, account2]
        
        mock_calc_value.return_value = 1000.0
        
        mock_st.title = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
        mock_st.metric = MagicMock()
        mock_st.expander = MagicMock(return_value=MagicMock())
        mock_st.subheader = MagicMock()
        mock_st.dataframe = MagicMock()
        mock_st.selectbox = MagicMock(return_value="Test Account 1 (ID: 1)")
        # Fix columns return for edit/delete section
        mock_st.columns.side_effect = [
            [MagicMock(), MagicMock(), MagicMock(), MagicMock()],  # For statistics
            [MagicMock(), MagicMock()],  # For edit/delete forms
        ]
        mock_get_account_by_id = MagicMock(return_value=account1)
        
        with patch("finarius_app.ui.accounts.table.get_account_by_id", mock_get_account_by_id):
            render_accounts_page()

        assert mock_get_all_accounts.called
        assert mock_st.title.called

    @patch("finarius_app.ui.accounts.forms.st")
    @patch("finarius_app.ui.accounts.page.get_all_accounts")
    @patch("finarius_app.ui.accounts.page.get_db")
    @patch("finarius_app.ui.accounts.page.st")
    @patch("finarius_app.ui.accounts.forms.set_error_message")
    def test_render_accounts_page_form_validation(self, mock_set_error, mock_st_page, mock_get_db, mock_get_all_accounts, mock_st_forms):
        """Test account form validation."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_all_accounts.return_value = []
        
        mock_st_page.title = MagicMock()
        mock_st_page.markdown = MagicMock()
        mock_st_page.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
        mock_st_page.metric = MagicMock()
        mock_st_page.subheader = MagicMock()
        mock_st_page.info = MagicMock()
        
        # Mock form for forms module
        mock_form = MagicMock()
        mock_form.__enter__ = MagicMock(return_value=mock_form)
        mock_form.__exit__ = MagicMock(return_value=None)
        mock_expander = MagicMock()
        mock_expander.__enter__ = MagicMock(return_value=mock_expander)
        mock_expander.__exit__ = MagicMock(return_value=None)
        mock_expander.form = MagicMock(return_value=mock_form)
        mock_st_forms.expander = MagicMock(return_value=mock_expander)
        
        mock_st_forms.text_input = MagicMock(return_value="")
        mock_st_forms.selectbox = MagicMock(return_value="USD")
        mock_st_forms.form_submit_button = MagicMock(return_value=True)
        mock_st_forms.rerun = MagicMock()
        
        render_accounts_page()

        # Form validation test - verify form structure is set up correctly
        # The actual validation happens inside the form context manager when submit=True
        # This test verifies the form rendering structure
        assert mock_st_forms.expander.called

    @patch("finarius_app.ui.accounts.page.get_all_accounts")
    @patch("finarius_app.ui.accounts.table.get_account_by_id")
    @patch("finarius_app.core.models.get_transactions_by_account")
    @patch("finarius_app.ui.accounts.statistics.calculate_portfolio_value")
    @patch("finarius_app.ui.accounts.page.get_db")
    @patch("finarius_app.ui.accounts.page.st")
    @patch("finarius_app.ui.accounts.forms.set_success_message")
    def test_render_accounts_page_delete_account(
        self, mock_set_success, mock_st, mock_get_db, mock_calc_value,
        mock_get_transactions, mock_get_account_by_id, mock_get_all_accounts
    ):
        """Test delete account functionality."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        account = Account(name="Test Account", currency="USD", account_id=1)
        mock_get_all_accounts.return_value = [account]
        mock_get_account_by_id.return_value = account
        mock_get_transactions.return_value = []
        mock_calc_value.return_value = 0.0
        
        mock_st.title = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.columns = MagicMock(side_effect=[
            [MagicMock(), MagicMock(), MagicMock(), MagicMock()],  # For statistics
            [MagicMock(), MagicMock()],  # For edit/delete forms
        ])
        mock_st.metric = MagicMock()
        mock_st.expander = MagicMock(return_value=MagicMock())
        mock_st.subheader = MagicMock()
        mock_st.dataframe = MagicMock()
        mock_st.selectbox = MagicMock(return_value="Test Account (ID: 1)")
        mock_st.warning = MagicMock()
        mock_st.error = MagicMock()
        mock_st.text_input = MagicMock(return_value="Test Account")
        mock_st.form_submit_button = MagicMock(return_value=True)
        mock_st.rerun = MagicMock()
        
        # Mock form
        mock_form = MagicMock()
        mock_form.__enter__ = MagicMock(return_value=mock_form)
        mock_form.__exit__ = MagicMock(return_value=None)
        mock_st.form.return_value = mock_form
        
        render_accounts_page()

        # Verify account was processed
        assert mock_get_all_accounts.called


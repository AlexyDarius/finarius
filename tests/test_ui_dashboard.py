"""Tests for UI dashboard module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from finarius_app.core.models import Account
from finarius_app.ui.dashboard import render_dashboard_page


class TestDashboardUI:
    """Test dashboard UI module."""

    @patch("finarius_app.ui.dashboard.page.get_db")
    @patch("finarius_app.ui.dashboard.page.st")
    def test_render_dashboard_page_no_db(self, mock_st, mock_get_db):
        """Test rendering dashboard page when database is not initialized."""
        mock_get_db.return_value = None
        mock_st.error = MagicMock()
        mock_st.title = MagicMock()

        render_dashboard_page()

        mock_st.error.assert_called_once_with("Database not initialized")
        mock_st.title.assert_called_once_with("📊 Dashboard")

    @patch("finarius_app.ui.dashboard.page.get_all_accounts")
    @patch("finarius_app.ui.dashboard.page.get_db")
    @patch("finarius_app.ui.dashboard.page.st")
    def test_render_dashboard_page_no_accounts(self, mock_st, mock_get_db, mock_get_all_accounts):
        """Test rendering dashboard page with no accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_all_accounts.return_value = []
        mock_st.title = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.info = MagicMock()

        render_dashboard_page()

        mock_st.warning.assert_called_once()
        mock_get_all_accounts.assert_called_once_with(mock_db)

    @patch("finarius_app.ui.dashboard.page.render_dividend_summary")
    @patch("finarius_app.ui.dashboard.page.render_recent_transactions")
    @patch("finarius_app.ui.dashboard.page.render_top_positions")
    @patch("finarius_app.ui.dashboard.page.render_charts")
    @patch("finarius_app.ui.dashboard.page.render_performance_metrics")
    @patch("finarius_app.ui.dashboard.page.render_portfolio_overview")
    @patch("finarius_app.ui.dashboard.page.render_filters")
    @patch("finarius_app.ui.dashboard.page.get_all_accounts")
    @patch("finarius_app.ui.dashboard.page.get_db")
    @patch("finarius_app.ui.dashboard.page.st")
    def test_render_dashboard_page_with_accounts(
        self,
        mock_st,
        mock_get_db,
        mock_get_all_accounts,
        mock_render_filters,
        mock_render_overview,
        mock_render_metrics,
        mock_render_charts,
        mock_render_positions,
        mock_render_transactions,
        mock_render_dividends,
    ):
        """Test rendering dashboard page with accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        account = Account(name="Test Account", currency="USD", account_id=1)
        mock_get_all_accounts.return_value = [account]
        
        mock_render_filters.return_value = (1, date.today() - timedelta(days=30), date.today())
        
        mock_st.title = MagicMock()
        mock_st.markdown = MagicMock()
        mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])

        render_dashboard_page()

        mock_st.title.assert_called_once_with("📊 Dashboard")
        mock_get_all_accounts.assert_called_once_with(mock_db)
        mock_render_filters.assert_called_once_with(mock_db)
        mock_render_overview.assert_called_once()
        mock_render_metrics.assert_called_once()
        mock_render_charts.assert_called_once()
        mock_render_positions.assert_called_once()
        mock_render_transactions.assert_called_once()
        mock_render_dividends.assert_called_once()


"""Tests for UI analytics module."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

from finarius_app.core.models import Account
from finarius_app.ui.analytics import render_analytics_page


class TestAnalyticsUI:
    """Test analytics UI module."""

    @patch("finarius_app.ui.analytics.page.get_db")
    @patch("finarius_app.ui.analytics.page.st")
    def test_render_analytics_page_no_db(self, mock_st, mock_get_db):
        """Test rendering analytics page when database is not initialized."""
        mock_get_db.return_value = None
        mock_st.error = MagicMock()
        mock_st.title = MagicMock()

        render_analytics_page()

        mock_st.error.assert_called_once_with("Database not initialized")
        mock_st.title.assert_called_once_with("📈 Analytics")

    @patch("finarius_app.ui.analytics.page.get_all_accounts")
    @patch("finarius_app.ui.analytics.page.get_db")
    @patch("finarius_app.ui.analytics.page.st")
    def test_render_analytics_page_no_accounts(self, mock_st, mock_get_db, mock_get_all_accounts):
        """Test rendering analytics page with no accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_get_all_accounts.return_value = []
        mock_st.title = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.info = MagicMock()

        render_analytics_page()

        mock_st.warning.assert_called_once()
        mock_get_all_accounts.assert_called_once_with(mock_db)

    @patch("finarius_app.ui.analytics.page.render_position_analytics")
    @patch("finarius_app.ui.analytics.page.render_dividend_analytics")
    @patch("finarius_app.ui.analytics.page.render_risk_metrics")
    @patch("finarius_app.ui.analytics.page.render_returns_analysis")
    @patch("finarius_app.ui.analytics.page.render_gains_analysis")
    @patch("finarius_app.ui.analytics.page.render_performance_analytics")
    @patch("finarius_app.ui.analytics.page.render_filters")
    @patch("finarius_app.ui.analytics.page.get_all_accounts")
    @patch("finarius_app.ui.analytics.page.get_db")
    @patch("finarius_app.ui.analytics.page.st")
    def test_render_analytics_page_with_accounts(
        self,
        mock_st,
        mock_get_db,
        mock_get_all_accounts,
        mock_render_filters,
        mock_render_performance,
        mock_render_gains,
        mock_render_returns,
        mock_render_risk,
        mock_render_dividends,
        mock_render_positions,
    ):
        """Test rendering analytics page with accounts."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        account = Account(name="Test Account", currency="USD", account_id=1)
        mock_get_all_accounts.return_value = [account]
        
        mock_render_filters.return_value = (1, date.today() - timedelta(days=365), date.today())
        
        mock_st.title = MagicMock()
        mock_st.markdown = MagicMock()

        render_analytics_page()

        mock_st.title.assert_called_once_with("📈 Analytics")
        mock_get_all_accounts.assert_called_once_with(mock_db)
        mock_render_filters.assert_called_once_with(mock_db)
        mock_render_performance.assert_called_once()
        mock_render_gains.assert_called_once()
        mock_render_returns.assert_called_once()
        mock_render_risk.assert_called_once()
        mock_render_dividends.assert_called_once()
        mock_render_positions.assert_called_once()


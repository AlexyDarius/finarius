"""Tests for UI navigation module."""

import pytest
from unittest.mock import MagicMock, patch

from finarius_app.ui.navigation import (
    render_sidebar,
    get_page_title,
    get_page_icon,
    PAGE_DASHBOARD,
    PAGE_ACCOUNTS,
    PAGE_TRANSACTIONS,
    PAGE_PORTFOLIO,
    PAGE_ANALYTICS,
    PAGE_SETTINGS,
)


class TestNavigation:
    """Test navigation module."""

    def test_page_constants(self):
        """Test that page constants are defined."""
        assert PAGE_DASHBOARD == "dashboard"
        assert PAGE_ACCOUNTS == "accounts"
        assert PAGE_TRANSACTIONS == "transactions"
        assert PAGE_PORTFOLIO == "portfolio"
        assert PAGE_ANALYTICS == "analytics"
        assert PAGE_SETTINGS == "settings"

    def test_get_page_title(self):
        """Test getting page title."""
        assert get_page_title(PAGE_DASHBOARD) == "Dashboard"
        assert get_page_title(PAGE_ACCOUNTS) == "Accounts"
        assert get_page_title(PAGE_TRANSACTIONS) == "Transactions"
        assert get_page_title(PAGE_PORTFOLIO) == "Portfolio"
        assert get_page_title(PAGE_ANALYTICS) == "Analytics"
        assert get_page_title(PAGE_SETTINGS) == "Settings"
        assert get_page_title("unknown") == "Finarius"

    def test_get_page_icon(self):
        """Test getting page icon."""
        assert get_page_icon(PAGE_DASHBOARD) == "📊"
        assert get_page_icon(PAGE_ACCOUNTS) == "🏦"
        assert get_page_icon(PAGE_TRANSACTIONS) == "💸"
        assert get_page_icon(PAGE_PORTFOLIO) == "💼"
        assert get_page_icon(PAGE_ANALYTICS) == "📈"
        assert get_page_icon(PAGE_SETTINGS) == "⚙️"
        assert get_page_icon("unknown") == "📊"

    @patch("finarius_app.ui.navigation.st")
    def test_render_sidebar(self, mock_st):
        """Test rendering sidebar navigation."""
        # Mock session state as MagicMock to support attribute access
        mock_session_state = MagicMock()
        mock_session_state.__contains__ = lambda self, key: key not in ["selected_page"]
        mock_session_state.get = lambda key, default=None: default
        mock_st.session_state = mock_session_state
        mock_st.sidebar = MagicMock()
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.radio = MagicMock(return_value=PAGE_DASHBOARD)

        # Call function
        result = render_sidebar()

        # Verify calls
        assert result == PAGE_DASHBOARD
        mock_st.sidebar.title.assert_called_once()
        mock_st.sidebar.radio.assert_called_once()
        assert mock_st.session_state.selected_page == PAGE_DASHBOARD

    @patch("finarius_app.ui.navigation.st")
    def test_render_sidebar_with_existing_state(self, mock_st):
        """Test rendering sidebar with existing session state."""
        # Mock session state with existing page
        mock_session_state = MagicMock()
        mock_session_state.__contains__ = lambda self, key: key == "selected_page"
        mock_session_state.selected_page = PAGE_ACCOUNTS
        mock_st.session_state = mock_session_state
        mock_st.sidebar = MagicMock()
        mock_st.sidebar.title = MagicMock()
        mock_st.sidebar.markdown = MagicMock()
        mock_st.sidebar.radio = MagicMock(return_value=PAGE_ACCOUNTS)

        # Call function
        result = render_sidebar()

        # Verify calls
        assert result == PAGE_ACCOUNTS
        assert mock_st.session_state.selected_page == PAGE_ACCOUNTS


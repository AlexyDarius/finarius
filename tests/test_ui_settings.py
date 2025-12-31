"""Tests for UI settings module."""

import pytest
from unittest.mock import MagicMock, patch

from finarius_app.ui.settings import render_settings_page


class TestSettingsUI:
    """Test settings UI module."""

    @patch("finarius_app.ui.settings.page.get_db")
    @patch("finarius_app.ui.settings.page.st")
    def test_render_settings_page_no_db(self, mock_st, mock_get_db):
        """Test rendering settings page when database is not initialized."""
        mock_get_db.return_value = None
        mock_st.error = MagicMock()
        mock_st.title = MagicMock()

        render_settings_page()

        mock_st.error.assert_called_once_with("Database not initialized")
        mock_st.title.assert_called_once_with("⚙️ Settings")

    @patch("finarius_app.ui.settings.page.render_export_import_settings")
    @patch("finarius_app.ui.settings.page.render_display_settings")
    @patch("finarius_app.ui.settings.page.render_price_settings")
    @patch("finarius_app.ui.settings.page.render_database_settings")
    @patch("finarius_app.ui.settings.page.get_db")
    @patch("finarius_app.ui.settings.page.st")
    def test_render_settings_page_with_db(
        self,
        mock_st,
        mock_get_db,
        mock_render_database,
        mock_render_prices,
        mock_render_display,
        mock_render_export_import,
    ):
        """Test rendering settings page with database."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_st.title = MagicMock()
        mock_st.markdown = MagicMock()

        render_settings_page()

        mock_st.title.assert_called_once_with("⚙️ Settings")
        mock_get_db.assert_called_once()
        mock_render_database.assert_called_once_with(mock_db)
        mock_render_prices.assert_called_once_with(mock_db)
        mock_render_display.assert_called_once()
        mock_render_export_import.assert_called_once_with(mock_db)


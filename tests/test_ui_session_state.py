"""Tests for UI session state module."""

import pytest
from unittest.mock import MagicMock, patch

from finarius_app.core.database import Database
from finarius_app.ui.session_state import (
    initialize_session_state,
    get_db,
    set_db,
    clear_messages,
    set_error_message,
    set_success_message,
    display_messages,
    get_session_value,
    set_session_value,
)


class TestSessionState:
    """Test session state module."""

    @patch("finarius_app.ui.session_state.st")
    def test_initialize_session_state(self, mock_st):
        """Test initializing session state."""
        # Create MagicMock that supports both dict and attribute access
        mock_session_state = MagicMock()
        mock_session_state.__contains__ = lambda self, key: False
        mock_st.session_state = mock_session_state

        initialize_session_state()

        # Verify attributes were set
        assert hasattr(mock_st.session_state, "db")
        assert mock_st.session_state.db is None
        assert hasattr(mock_st.session_state, "selected_account_id")
        assert mock_st.session_state.selected_account_id is None
        assert hasattr(mock_st.session_state, "date_range")
        assert hasattr(mock_st.session_state, "show_transaction_form")
        assert hasattr(mock_st.session_state, "editing_transaction_id")
        assert hasattr(mock_st.session_state, "show_account_form")
        assert hasattr(mock_st.session_state, "editing_account_id")
        assert hasattr(mock_st.session_state, "error_message")
        assert hasattr(mock_st.session_state, "success_message")

    @patch("finarius_app.ui.session_state.st")
    def test_initialize_session_state_idempotent(self, mock_st):
        """Test that initializing session state is idempotent."""
        # Create MagicMock with existing key
        mock_session_state = MagicMock()
        mock_session_state.__contains__ = lambda self, key: key == "existing_key"
        mock_session_state.existing_key = "existing_value"
        mock_st.session_state = mock_session_state

        initialize_session_state()

        # Verify existing key is preserved
        assert hasattr(mock_st.session_state, "existing_key")
        assert mock_st.session_state.existing_key == "existing_value"
        assert hasattr(mock_st.session_state, "db")

    @patch("finarius_app.ui.session_state.st")
    def test_get_db_none(self, mock_st):
        """Test getting database when not set."""
        mock_session_state = MagicMock()
        mock_session_state.get = lambda key, default=None: None
        mock_st.session_state = mock_session_state

        result = get_db()

        assert result is None

    @patch("finarius_app.ui.session_state.st")
    def test_get_db_set(self, mock_st):
        """Test getting database when set."""
        # Create a mock database object
        db = MagicMock(spec=Database)
        mock_st.session_state = {"db": db}

        result = get_db()

        assert result is db

    @patch("finarius_app.ui.session_state.st")
    def test_set_db(self, mock_st):
        """Test setting database."""
        # Create a mock database object
        db = MagicMock(spec=Database)
        mock_session_state = MagicMock()
        mock_st.session_state = mock_session_state

        set_db(db)

        assert mock_st.session_state.db is db

    @patch("finarius_app.ui.session_state.st")
    def test_clear_messages(self, mock_st):
        """Test clearing messages."""
        mock_session_state = MagicMock()
        mock_session_state.error_message = "Error"
        mock_session_state.success_message = "Success"
        mock_st.session_state = mock_session_state

        clear_messages()

        assert mock_st.session_state.error_message is None
        assert mock_st.session_state.success_message is None

    @patch("finarius_app.ui.session_state.st")
    def test_set_error_message(self, mock_st):
        """Test setting error message."""
        mock_session_state = MagicMock()
        mock_session_state.success_message = "Success"
        mock_st.session_state = mock_session_state

        set_error_message("Test error")

        assert mock_st.session_state.error_message == "Test error"
        assert mock_st.session_state.success_message is None

    @patch("finarius_app.ui.session_state.st")
    def test_set_success_message(self, mock_st):
        """Test setting success message."""
        mock_session_state = MagicMock()
        mock_session_state.error_message = "Error"
        mock_st.session_state = mock_session_state

        set_success_message("Test success")

        assert mock_st.session_state.success_message == "Test success"
        assert mock_st.session_state.error_message is None

    @patch("finarius_app.ui.session_state.st")
    def test_display_messages_error(self, mock_st):
        """Test displaying error message."""
        mock_session_state = MagicMock()
        mock_session_state.get = lambda key, default=None: "Test error" if key == "error_message" else None
        mock_session_state.error_message = "Test error"
        mock_st.session_state = mock_session_state
        mock_st.error = MagicMock()

        display_messages()

        mock_st.error.assert_called_once_with("Test error")
        assert mock_st.session_state.error_message is None

    @patch("finarius_app.ui.session_state.st")
    def test_display_messages_success(self, mock_st):
        """Test displaying success message."""
        mock_session_state = MagicMock()
        mock_session_state.get = lambda key, default=None: "Test success" if key == "success_message" else None
        mock_session_state.success_message = "Test success"
        mock_st.session_state = mock_session_state
        mock_st.success = MagicMock()

        display_messages()

        mock_st.success.assert_called_once_with("Test success")
        assert mock_st.session_state.success_message is None

    @patch("finarius_app.ui.session_state.st")
    def test_display_messages_both(self, mock_st):
        """Test displaying both messages."""
        mock_session_state = MagicMock()
        mock_session_state.get = lambda key, default=None: {
            "error_message": "Test error",
            "success_message": "Test success",
        }.get(key, None)
        mock_session_state.error_message = "Test error"
        mock_session_state.success_message = "Test success"
        mock_st.session_state = mock_session_state
        mock_st.error = MagicMock()
        mock_st.success = MagicMock()

        display_messages()

        mock_st.error.assert_called_once_with("Test error")
        mock_st.success.assert_called_once_with("Test success")

    @patch("finarius_app.ui.session_state.st")
    def test_get_session_value(self, mock_st):
        """Test getting session value."""
        mock_session_state = MagicMock()
        mock_session_state.get = lambda key, default=None: "test_value" if key == "test_key" else default
        mock_st.session_state = mock_session_state

        result = get_session_value("test_key")
        assert result == "test_value"

        result = get_session_value("missing_key", "default")
        assert result == "default"

    @patch("finarius_app.ui.session_state.st")
    def test_set_session_value(self, mock_st):
        """Test setting session value."""
        # Use a dict-like object that supports both dict and attribute access
        class MockSessionState(dict):
            def __getitem__(self, key):
                return dict.__getitem__(self, key)
            
            def __setitem__(self, key, value):
                dict.__setitem__(self, key, value)
        
        mock_session_state = MockSessionState()
        mock_st.session_state = mock_session_state

        set_session_value("test_key", "test_value")

        assert mock_st.session_state["test_key"] == "test_value"


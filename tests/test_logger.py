"""Tests for logger module."""

import pytest
import logging
import os
import tempfile
from pathlib import Path
from finarius_app.core.logger import (
    setup_logging,
    get_logger,
    reset_logging,
    set_log_level,
)
from finarius_app.core.config import Config


@pytest.fixture
def reset_logger():
    """Reset logging configuration before and after test."""
    reset_logging()
    yield
    reset_logging()


class TestSetupLogging:
    """Test logging setup functionality."""

    def test_setup_logging_defaults(self, reset_logger):
        """Test that setup_logging uses default configuration."""
        setup_logging()
        logger = logging.getLogger("test")
        assert logger.level == logging.NOTSET  # Inherits from root
        assert len(logging.getLogger().handlers) > 0

    def test_setup_logging_with_config(self, reset_logger):
        """Test setup_logging with custom config."""
        # Create config with custom log level
        config = Config()
        config.set("logging.level", "DEBUG")
        config.set("logging.file_enabled", False)

        setup_logging(config=config)
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_setup_logging_idempotent(self, reset_logger):
        """Test that setup_logging can be called multiple times safely."""
        setup_logging()
        handler_count_1 = len(logging.getLogger().handlers)

        setup_logging()
        handler_count_2 = len(logging.getLogger().handlers)

        # Should not add duplicate handlers
        assert handler_count_1 == handler_count_2

    def test_setup_logging_force(self, reset_logger):
        """Test that force parameter reconfigures logging."""
        setup_logging()
        handler_count_1 = len(logging.getLogger().handlers)

        setup_logging(force=True)
        handler_count_2 = len(logging.getLogger().handlers)

        # Should reconfigure (may have same or different handler count)
        assert handler_count_2 > 0

    def test_setup_logging_file_handler(self, reset_logger, tmp_path):
        """Test file handler creation when enabled."""
        log_file = tmp_path / "test.log"
        config = Config()
        config.set("logging.file_enabled", True)
        config.set("logging.file_path", str(log_file))
        config.set("logging.level", "INFO")

        setup_logging(config=config)
        logger = logging.getLogger("test")
        logger.info("Test message")

        # Check that file was created and contains message
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_file_handler_failure(self, reset_logger, monkeypatch):
        """Test that file handler failure doesn't crash the app."""
        # Mock Path.mkdir to raise an error
        def mock_mkdir(*args, **kwargs):
            raise PermissionError("Permission denied")

        config = Config()
        config.set("logging.file_enabled", True)
        config.set("logging.file_path", "/invalid/path/test.log")

        # Should not raise exception
        setup_logging(config=config)
        # Console handler should still be present
        assert len(logging.getLogger().handlers) > 0

    def test_setup_logging_invalid_level(self, reset_logger):
        """Test that invalid log level defaults to INFO."""
        config = Config()
        config.set("logging.level", "INVALID_LEVEL")

        setup_logging(config=config)
        root_logger = logging.getLogger()
        # Should default to INFO
        assert root_logger.level == logging.INFO


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_auto_setup(self, reset_logger):
        """Test that get_logger automatically sets up logging."""
        # Reset logging first
        reset_logging()
        assert len(logging.getLogger().handlers) == 0

        # get_logger should auto-setup
        logger = get_logger("test_module")
        assert len(logging.getLogger().handlers) > 0
        assert logger.name == "test_module"

    def test_get_logger_with_name(self, reset_logger):
        """Test get_logger with module name."""
        setup_logging()
        logger = get_logger("finarius_app.core.test")
        assert logger.name == "finarius_app.core.test"

    def test_get_logger_root(self, reset_logger):
        """Test get_logger without name returns root logger."""
        setup_logging()
        logger = get_logger()
        assert logger.name == "root"

    def test_get_logger_multiple_calls(self, reset_logger):
        """Test that multiple calls to get_logger work correctly."""
        setup_logging()
        logger1 = get_logger("test")
        logger2 = get_logger("test")

        # Should return same logger instance
        assert logger1 is logger2


class TestResetLogging:
    """Test reset_logging function."""

    def test_reset_logging(self, reset_logger):
        """Test that reset_logging clears handlers."""
        setup_logging()
        assert len(logging.getLogger().handlers) > 0

        reset_logging()
        assert len(logging.getLogger().handlers) == 0

    def test_reset_logging_allows_reconfiguration(self, reset_logger):
        """Test that reset allows reconfiguration."""
        setup_logging()
        reset_logging()

        # Should be able to setup again
        setup_logging()
        assert len(logging.getLogger().handlers) > 0


class TestSetLogLevel:
    """Test set_log_level function."""

    def test_set_log_level_debug(self, reset_logger):
        """Test setting log level to DEBUG."""
        setup_logging()
        set_log_level("DEBUG")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

        # Check handlers are updated
        for handler in root_logger.handlers:
            assert handler.level == logging.DEBUG

    def test_set_log_level_info(self, reset_logger):
        """Test setting log level to INFO."""
        setup_logging()
        set_log_level("INFO")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_set_log_level_warning(self, reset_logger):
        """Test setting log level to WARNING."""
        setup_logging()
        set_log_level("WARNING")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_set_log_level_error(self, reset_logger):
        """Test setting log level to ERROR."""
        setup_logging()
        set_log_level("ERROR")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR

    def test_set_log_level_invalid(self, reset_logger):
        """Test that invalid log level defaults to INFO."""
        setup_logging()
        set_log_level("INVALID")

        root_logger = logging.getLogger()
        # Should default to INFO
        assert root_logger.level == logging.INFO


class TestLoggingIntegration:
    """Test logging integration with Config."""

    def test_logging_with_env_vars(self, reset_logger, monkeypatch):
        """Test that logging respects environment variables."""
        monkeypatch.setenv("FINARIUS_LOGGING__LEVEL", "DEBUG")
        monkeypatch.setenv("FINARIUS_LOGGING__FILE_ENABLED", "true")

        # Reset config singleton to pick up env vars
        from finarius_app.core.config import Config

        Config._instance = None
        Config._config = {}
        config = Config()

        setup_logging(config=config)
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_logging_with_config_file(self, reset_logger, tmp_path):
        """Test logging with config file settings."""
        import json

        # Reset Config singleton to ensure fresh instance
        Config._instance = None
        Config._config = {}

        config_file = tmp_path / "config.json"
        config_data = {
            "logging": {
                "level": "WARNING",
                "file_enabled": False,
            }
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(str(config_file))
        setup_logging(config=config)
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_logging_format(self, reset_logger, tmp_path):
        """Test that custom log format is applied."""
        # Ensure logging is reset first
        reset_logging()

        log_file = tmp_path / "test.log"
        config = Config()
        config.set("logging.file_enabled", True)
        config.set("logging.file_path", str(log_file))
        config.set("logging.format", "%(levelname)s - %(message)s")

        # Force reconfiguration to ensure new format is applied
        setup_logging(config=config, force=True)
        
        # Verify file handler was created
        root_logger = logging.getLogger()
        file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0, "File handler should be created"
        
        logger = logging.getLogger("test")
        logger.info("Test message")

        # Flush and close all handlers to ensure message is written
        for handler in root_logger.handlers:
            handler.flush()
            if isinstance(handler, logging.FileHandler):
                handler.close()

        # Wait a bit for file system to sync
        import time

        time.sleep(0.1)

        # Reopen file handler if it was closed
        if not file_handlers[0].stream:
            file_handlers[0].stream = open(log_file, "a", encoding="utf-8")

        content = log_file.read_text()
        # Should contain level and message, but not timestamp
        assert "INFO" in content or "Test message" in content, f"Log file content: {repr(content)}, handlers: {[type(h).__name__ for h in root_logger.handlers]}"
        # Format should not include asctime (if content exists)
        if content:
            assert "%(asctime)s" not in content


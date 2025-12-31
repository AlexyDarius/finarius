"""Logging configuration module for Finarius.

This module provides centralized logging configuration that integrates
with the Config system. It supports:
- Configurable log levels from config file or environment
- Console and file output handlers
- Structured logging format
- Easy logger instance creation for modules
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import Config


# Global flag to track if logging has been configured
_logging_configured = False


def setup_logging(config: Optional[Config] = None, force: bool = False) -> None:
    """Configure logging system based on configuration.

    This function should be called once at application startup. It reads
    logging configuration from the Config system and sets up handlers
    for console and optionally file output.

    Args:
        config: Config instance. If None, creates a new instance.
        force: If True, reconfigure logging even if already configured.

    Example:
        >>> from finarius_app.core.logger import setup_logging
        >>> setup_logging()
    """
    global _logging_configured

    if _logging_configured and not force:
        return

    if config is None:
        config = Config()

    # Get logging configuration
    log_level = config.get("logging.level", "INFO")
    log_format = config.get(
        "logging.format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    file_enabled = config.get("logging.file_enabled", False)
    file_path = config.get("logging.file_path", "finarius.log")

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if file_enabled:
        try:
            # Ensure log directory exists
            log_file_path = Path(file_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file handler
            file_handler = logging.FileHandler(file_path, encoding="utf-8")
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # If file logging fails, log to console and continue
            root_logger.warning(f"Failed to set up file logging: {e}")

    _logging_configured = True
    root_logger.info(f"Logging configured: level={log_level}, file_enabled={file_enabled}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for a module.

    This function ensures logging is configured before returning a logger.
    It's safe to call this function multiple times - logging will only be
    configured once.

    Args:
        name: Logger name, typically __name__ of the calling module.
              If None, returns the root logger.

    Returns:
        Logger instance configured according to application settings.

    Example:
        >>> from finarius_app.core.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    # Ensure logging is configured
    if not _logging_configured:
        setup_logging()

    return logging.getLogger(name)


def reset_logging() -> None:
    """Reset logging configuration (useful for testing).

    This function clears the logging configuration state, allowing
    logging to be reconfigured. Mainly used in tests.
    """
    global _logging_configured
    _logging_configured = False
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.WARNING)


def set_log_level(level: str) -> None:
    """Set log level for all handlers.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Update all handlers
    for handler in root_logger.handlers:
        handler.setLevel(numeric_level)


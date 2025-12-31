"""Configuration management module for Finarius.

This module provides a centralized configuration system that supports:
- Loading from config files (JSON/YAML/TOML)
- Environment variable overrides
- Sensible default values
- Type validation
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager with file and environment variable support.

    Configuration is loaded in the following order (highest priority first):
    1. Environment variables
    2. Config file
    3. Default values

    Example:
        >>> config = Config()
        >>> db_path = config.get("database.path")
        >>> currency = config.get("display.default_currency", "USD")
    """

    _instance: Optional["Config"] = None
    _config: Dict[str, Any] = {}

    def __new__(cls, config_path: Optional[str] = None) -> "Config":
        """Create or return existing Config instance (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize Config instance.

        Args:
            config_path: Path to configuration file. If None, searches for
                config.json, config.yaml, or config.toml in current directory.
        """
        if not self._config:
            self._load_config(config_path)

    def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file and environment variables.

        Args:
            config_path: Path to configuration file. If None, searches for
                config files in current directory.
        """
        # Start with defaults
        self._config = self._get_defaults()

        # Load from config file
        file_config = self._load_from_file(config_path)
        if file_config:
            self._merge_config(self._config, file_config)

        # Override with environment variables
        env_config = self._load_from_env()
        if env_config:
            self._merge_config(self._config, env_config)

        logger.info("Configuration loaded successfully")

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values.

        Returns:
            Dictionary with default configuration values.
        """
        return {
            "database": {
                "path": "db.sqlite",
            },
            "display": {
                "default_currency": "USD",
                "date_format": "%Y-%m-%d",
                "number_format": "{:,.2f}",
            },
            "prices": {
                "update_frequency": "daily",  # daily, weekly, manual
                "cache_enabled": True,
                "cache_expiry_days": 1,
            },
            "logging": {
                "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_enabled": False,
                "file_path": "finarius.log",
            },
        }

    def _load_from_file(self, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load configuration from file.

        Supports JSON, YAML, and TOML formats. Searches for config files
        in the following order if config_path is not provided:
        1. config.json
        2. config.yaml
        3. config.toml

        Args:
            config_path: Path to configuration file.

        Returns:
            Dictionary with configuration values, or None if no file found.
        """
        if config_path:
            paths = [Path(config_path)]
        else:
            # Search for config files in current directory
            current_dir = Path.cwd()
            paths = [
                current_dir / "config.json",
                current_dir / "config.yaml",
                current_dir / "config.toml",
            ]

        for path in paths:
            if path.exists() and path.is_file():
                try:
                    if path.suffix == ".json":
                        return self._load_json(path)
                    elif path.suffix == ".yaml" or path.suffix == ".yml":
                        return self._load_yaml(path)
                    elif path.suffix == ".toml":
                        return self._load_toml(path)
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")

        return None

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load configuration from JSON file.

        Args:
            path: Path to JSON file.

        Returns:
            Dictionary with configuration values.

        Raises:
            json.JSONDecodeError: If JSON is invalid.
            IOError: If file cannot be read.
        """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            path: Path to YAML file.

        Returns:
            Dictionary with configuration values.

        Raises:
            ImportError: If PyYAML is not installed.
            yaml.YAMLError: If YAML is invalid.
            IOError: If file cannot be read.
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML config files. "
                "Install it with: pip install pyyaml"
            )

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _load_toml(self, path: Path) -> Dict[str, Any]:
        """Load configuration from TOML file.

        Args:
            path: Path to TOML file.

        Returns:
            Dictionary with configuration values.

        Raises:
            ImportError: If tomli/tomllib is not installed.
            tomli.TOMLDecodeError: If TOML is invalid.
            IOError: If file cannot be read.
        """
        # Try built-in tomllib (Python 3.11+)
        try:
            import tomllib

            with open(path, "rb") as f:
                return tomllib.load(f)
        except ImportError:
            # Fall back to tomli for Python < 3.11
            try:
                import tomli

                with open(path, "rb") as f:
                    return tomli.load(f)
            except ImportError:
                raise ImportError(
                    "tomli is required for TOML config files (Python < 3.11). "
                    "Install it with: pip install tomli"
                )

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Environment variables should be prefixed with FINARIUS_ and use
        double underscores (__) to represent nested keys.

        Examples:
            FINARIUS_DATABASE__PATH -> database.path
            FINARIUS_DISPLAY__DEFAULT_CURRENCY -> display.default_currency

        Returns:
            Dictionary with configuration values from environment.
        """
        env_config: Dict[str, Any] = {}
        prefix = "FINARIUS_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to nested dict structure
                config_key = key[len(prefix) :].lower()
                keys = config_key.split("__")
                self._set_nested(env_config, keys, value)

        return env_config

    def _set_nested(self, d: Dict[str, Any], keys: list, value: Any) -> None:
        """Set a nested dictionary value.

        Args:
            d: Dictionary to modify.
            keys: List of keys representing the path.
            value: Value to set.
        """
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        # Convert string values to appropriate types
        d[keys[-1]] = self._convert_value(value)

    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type.

        Args:
            value: String value to convert.

        Returns:
            Converted value (bool, int, float, or str).
        """
        # Boolean values
        if value.lower() in ("true", "1", "yes", "on"):
            return True
        if value.lower() in ("false", "0", "no", "off"):
            return False

        # Numeric values
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # String value
        return value

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Merge override configuration into base configuration.

        Args:
            base: Base configuration dictionary (modified in place).
            override: Override configuration dictionary.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Supports dot notation for nested keys (e.g., "database.path").

        Args:
            key: Configuration key, supports dot notation for nested keys.
            default: Default value if key is not found.

        Returns:
            Configuration value or default.

        Example:
            >>> config.get("database.path")
            'db.sqlite'
            >>> config.get("display.default_currency", "EUR")
            'USD'
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key.

        Supports dot notation for nested keys (e.g., "database.path").

        Args:
            key: Configuration key, supports dot notation for nested keys.
            value: Value to set.

        Example:
            >>> config.set("database.path", "custom.db")
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary.

        Returns:
            Complete configuration dictionary.
        """
        return self._config.copy()

    def reload(self, config_path: Optional[str] = None) -> None:
        """Reload configuration from file and environment.

        Args:
            config_path: Path to configuration file. If None, searches for
                config files in current directory.
        """
        self._config = {}
        self._load_config(config_path)
        logger.info("Configuration reloaded")


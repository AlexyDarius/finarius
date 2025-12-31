"""Tests for configuration module."""

import pytest
import json
import os
import tempfile
from pathlib import Path
from finarius_app.core.config import Config


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def reset_config():
    """Reset Config singleton before and after test."""
    Config._instance = None
    Config._config = {}
    yield
    Config._instance = None
    Config._config = {}


class TestConfigDefaults:
    """Test default configuration values."""

    def test_default_values(self, reset_config):
        """Test that default values are loaded when no config file exists."""
        config = Config()
        assert config.get("database.path") == "db.sqlite"
        assert config.get("display.default_currency") == "USD"
        assert config.get("display.date_format") == "%Y-%m-%d"
        assert config.get("display.number_format") == "{:,.2f}"
        assert config.get("prices.update_frequency") == "daily"
        assert config.get("prices.cache_enabled") is True
        assert config.get("prices.cache_expiry_days") == 1
        assert config.get("logging.level") == "INFO"

    def test_get_with_default(self, reset_config):
        """Test get() method with default value."""
        config = Config()
        assert config.get("nonexistent.key", "default") == "default"
        assert config.get("database.path", "custom.db") == "db.sqlite"

    def test_get_nonexistent_key(self, reset_config):
        """Test get() method with nonexistent key."""
        config = Config()
        assert config.get("nonexistent.key") is None
        assert config.get("database.nonexistent") is None


class TestConfigFileLoading:
    """Test configuration loading from files."""

    def test_load_json_config(self, temp_config_dir, reset_config):
        """Test loading configuration from JSON file."""
        config_file = temp_config_dir / "config.json"
        config_data = {
            "database": {"path": "test.db"},
            "display": {"default_currency": "EUR"},
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_config_dir)
            config = Config()
            assert config.get("database.path") == "test.db"
            assert config.get("display.default_currency") == "EUR"
            # Other defaults should still be present
            assert config.get("prices.update_frequency") == "daily"
        finally:
            os.chdir(original_cwd)

    def test_load_json_with_path(self, temp_config_dir, reset_config):
        """Test loading JSON config with explicit path."""
        config_file = temp_config_dir / "custom.json"
        config_data = {"database": {"path": "custom.db"}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(str(config_file))
        assert config.get("database.path") == "custom.db"

    def test_load_yaml_config(self, temp_config_dir, reset_config):
        """Test loading configuration from YAML file."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        config_file = temp_config_dir / "config.yaml"
        config_data = {
            "database": {"path": "yaml.db"},
            "display": {"default_currency": "GBP"},
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_config_dir)
            config = Config()
            assert config.get("database.path") == "yaml.db"
            assert config.get("display.default_currency") == "GBP"
        finally:
            os.chdir(original_cwd)

    def test_load_toml_config(self, temp_config_dir, reset_config):
        """Test loading configuration from TOML file."""
        try:
            # Try tomllib (Python 3.11+)
            import tomllib
            toml_module = "tomllib"
        except ImportError:
            try:
                import tomli
                toml_module = "tomli"
            except ImportError:
                pytest.skip("tomli/tomllib not installed")

        config_file = temp_config_dir / "config.toml"
        config_data = """[database]
path = "toml.db"

[display]
default_currency = "JPY"
"""
        with open(config_file, "w") as f:
            f.write(config_data)

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_config_dir)
            config = Config()
            assert config.get("database.path") == "toml.db"
            assert config.get("display.default_currency") == "JPY"
        finally:
            os.chdir(original_cwd)

    def test_config_file_priority(self, temp_config_dir, reset_config):
        """Test that config files are searched in correct order."""
        # Create all three config files
        json_file = temp_config_dir / "config.json"
        yaml_file = temp_config_dir / "config.yaml"
        toml_file = temp_config_dir / "config.toml"

        with open(json_file, "w") as f:
            json.dump({"database": {"path": "json.db"}}, f)

        try:
            import yaml

            with open(yaml_file, "w") as f:
                yaml.dump({"database": {"path": "yaml.db"}}, f)
        except ImportError:
            pass

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_config_dir)
            config = Config()
            # JSON should be loaded first (highest priority in search)
            assert config.get("database.path") == "json.db"
        finally:
            os.chdir(original_cwd)

    def test_invalid_config_file(self, temp_config_dir, reset_config):
        """Test handling of invalid config file."""
        config_file = temp_config_dir / "config.json"
        with open(config_file, "w") as f:
            f.write("invalid json content {")

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_config_dir)
            # Should fall back to defaults without crashing
            config = Config()
            assert config.get("database.path") == "db.sqlite"
        finally:
            os.chdir(original_cwd)

    def test_nonexistent_config_file(self, reset_config):
        """Test that defaults are used when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config = Config()
                assert config.get("database.path") == "db.sqlite"
            finally:
                os.chdir(original_cwd)


class TestEnvironmentVariables:
    """Test environment variable overrides."""

    def test_env_var_override(self, reset_config):
        """Test that environment variables override config file values."""
        os.environ["FINARIUS_DATABASE__PATH"] = "env.db"
        os.environ["FINARIUS_DISPLAY__DEFAULT_CURRENCY"] = "CAD"

        try:
            config = Config()
            assert config.get("database.path") == "env.db"
            assert config.get("display.default_currency") == "CAD"
        finally:
            # Cleanup
            os.environ.pop("FINARIUS_DATABASE__PATH", None)
            os.environ.pop("FINARIUS_DISPLAY__DEFAULT_CURRENCY", None)

    def test_env_var_type_conversion(self, reset_config):
        """Test that environment variables are converted to appropriate types."""
        os.environ["FINARIUS_PRICES__CACHE_ENABLED"] = "false"
        os.environ["FINARIUS_PRICES__CACHE_EXPIRY_DAYS"] = "7"
        os.environ["FINARIUS_LOGGING__LEVEL"] = "DEBUG"

        try:
            config = Config()
            assert config.get("prices.cache_enabled") is False
            assert config.get("prices.cache_expiry_days") == 7
            assert config.get("logging.level") == "DEBUG"
        finally:
            os.environ.pop("FINARIUS_PRICES__CACHE_ENABLED", None)
            os.environ.pop("FINARIUS_PRICES__CACHE_EXPIRY_DAYS", None)
            os.environ.pop("FINARIUS_LOGGING__LEVEL", None)

    def test_env_var_boolean_values(self, reset_config):
        """Test various boolean value formats in environment variables."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for value, expected in test_cases:
            os.environ["FINARIUS_PRICES__CACHE_ENABLED"] = value
            try:
                Config._instance = None
                Config._config = {}
                config = Config()
                assert config.get("prices.cache_enabled") is expected
            finally:
                os.environ.pop("FINARIUS_PRICES__CACHE_ENABLED", None)

    def test_env_var_numeric_values(self, reset_config):
        """Test numeric value conversion in environment variables."""
        os.environ["FINARIUS_PRICES__CACHE_EXPIRY_DAYS"] = "5"
        os.environ["FINARIUS_TEST__FLOAT"] = "3.14"

        try:
            config = Config()
            assert config.get("prices.cache_expiry_days") == 5
            assert config.get("test.float") == 3.14
        finally:
            os.environ.pop("FINARIUS_PRICES__CACHE_EXPIRY_DAYS", None)
            os.environ.pop("FINARIUS_TEST__FLOAT", None)


class TestConfigMethods:
    """Test Config class methods."""

    def test_set_method(self, reset_config):
        """Test set() method for updating configuration."""
        config = Config()
        config.set("database.path", "custom.db")
        assert config.get("database.path") == "custom.db"

        config.set("display.default_currency", "EUR")
        assert config.get("display.default_currency") == "EUR"

    def test_set_nested_key(self, reset_config):
        """Test set() method with nested keys."""
        config = Config()
        config.set("new.section.key", "value")
        assert config.get("new.section.key") == "value"

    def test_to_dict(self, reset_config):
        """Test to_dict() method."""
        config = Config()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "database" in config_dict
        assert "display" in config_dict
        assert "prices" in config_dict
        assert "logging" in config_dict
        assert config_dict["database"]["path"] == "db.sqlite"

    def test_reload(self, temp_config_dir, reset_config):
        """Test reload() method."""
        config_file = temp_config_dir / "config.json"
        config_data = {"database": {"path": "initial.db"}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(str(config_file))
        assert config.get("database.path") == "initial.db"

        # Update config file
        config_data["database"]["path"] = "updated.db"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Reload
        config.reload(str(config_file))
        assert config.get("database.path") == "updated.db"


class TestConfigSingleton:
    """Test Config singleton pattern."""

    def test_singleton_pattern(self, reset_config):
        """Test that Config uses singleton pattern."""
        config1 = Config()
        config2 = Config()

        assert config1 is config2
        assert Config._instance is config1

    def test_singleton_with_different_paths(self, reset_config):
        """Test that singleton ignores different paths after first creation."""
        config1 = Config("path1.json")
        config2 = Config("path2.json")

        assert config1 is config2


class TestConfigPriority:
    """Test configuration priority (env > file > defaults)."""

    def test_priority_order(self, temp_config_dir, reset_config):
        """Test that environment variables override file and defaults."""
        # Create config file
        config_file = temp_config_dir / "config.json"
        config_data = {"database": {"path": "file.db"}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Set environment variable
        os.environ["FINARIUS_DATABASE__PATH"] = "env.db"

        try:
            config = Config(str(config_file))
            # Environment variable should win
            assert config.get("database.path") == "env.db"
        finally:
            os.environ.pop("FINARIUS_DATABASE__PATH", None)

    def test_file_overrides_defaults(self, temp_config_dir, reset_config):
        """Test that config file overrides defaults."""
        config_file = temp_config_dir / "config.json"
        config_data = {"display": {"default_currency": "EUR"}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(str(config_file))
        # File should override default
        assert config.get("display.default_currency") == "EUR"
        # But other defaults should remain
        assert config.get("database.path") == "db.sqlite"


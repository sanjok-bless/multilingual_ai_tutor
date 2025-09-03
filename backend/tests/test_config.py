"""Tests for configuration management and environment settings."""

import os
import tempfile
from unittest.mock import patch

import pytest

from backend.config import AppConfig


class TestAppConfig:
    """Test main application configuration."""

    def test_app_config_requires_openai_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test app configuration requires OPENAI_API_KEY environment variable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clear all environment variables and change to empty temp directory
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)
            config_vars = [
                "ENVIRONMENT",
                "SUPPORTED_LANGUAGES",
                "CORS_ORIGINS",
            ]
            for key in list(os.environ.keys()):
                if key.startswith("OPENAI_") or key in config_vars:
                    monkeypatch.delenv(key, raising=False)
            monkeypatch.chdir(temp_dir)  # Change to temp directory with no .env files

            with pytest.raises(ValueError, match="Field required"):
                AppConfig(_env_file=None)

    def test_app_config_loads_from_environment_variables(self) -> None:
        """Test app configuration loads values from environment variables."""
        env_vars = {
            "ENVIRONMENT": "prod",
            "OPENAI_API_KEY": "sk-env-key-12345",
            "OPENAI_MODEL": "gpt-3.5-turbo",
            "OPENAI_MAX_TOKENS": "750",
            "OPENAI_TEMPERATURE": "0.5",
            "SUPPORTED_LANGUAGES": '["english","german","polish"]',
            "CORS_ORIGINS": '["http://localhost:3000"]',
        }

        with patch.dict(os.environ, env_vars):
            config = AppConfig()

            assert config.environment == "prod"
            assert config.openai_api_key == "sk-env-key-12345"
            assert config.openai_model == "gpt-3.5-turbo"
            assert config.supported_languages == ["english", "german", "polish"]
            assert config.cors_origins == ["http://localhost:3000"]

    @pytest.fixture
    def temp_env_file(self) -> str:
        """Create a temporary .env file for testing."""
        env_content = """OPENAI_API_KEY=sk-env-file-key
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=300
ENVIRONMENT=dev
SUPPORTED_LANGUAGES=["english","ukrainian"]
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            temp_file = f.name

        yield temp_file
        os.unlink(temp_file)

    def test_environment_variables_override_env_file(self, temp_env_file: str) -> None:
        """Test environment variables have higher priority than .env file values."""
        # Set environment variables that should override .env file
        override_env = {
            "OPENAI_API_KEY": "sk-override-from-env-var",  # Override .env value
            "OPENAI_TEMPERATURE": "0.8",  # Override .env value
            "OPENAI_MAX_TOKENS": "750",  # Override .env file value
        }

        with patch.dict(os.environ, override_env):
            config = AppConfig(_env_file=temp_env_file)

            # Values overridden by environment variables
            assert config.openai_api_key == "sk-override-from-env-var"
            assert config.openai_temperature == 0.8
            assert config.openai_max_tokens == 750
            assert config.environment == "dev"  # From .env file

    def test_app_config_supports_env_file_loading(self) -> None:
        """Test app configuration can load from .env file when no env vars set."""
        env_content = """OPENAI_API_KEY=sk-from-env-file
OPENAI_TEMPERATURE=0.4
ENVIRONMENT=ci
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write(env_content)
            temp_env_file = f.name

        try:
            # Clear environment variables
            with patch.dict(os.environ, {}, clear=True):
                config = AppConfig(_env_file=temp_env_file)

                # All values should come from .env file
                assert config.openai_api_key == "sk-from-env-file"
                assert config.openai_temperature == 0.4
                assert config.environment == "ci"

        finally:
            os.unlink(temp_env_file)

    def test_openai_config_validates_api_key_format(self) -> None:
        """Test app configuration validates API key format."""
        # Valid API key should work
        config = AppConfig(openai_api_key="sk-test-key-12345")
        assert config.openai_api_key == "sk-test-key-12345"

        # Invalid API key format should fail
        with pytest.raises(ValueError, match="OPENAI_API_KEY must start with 'sk-'"):
            AppConfig(openai_api_key="invalid-key")

    def test_openai_config_validates_temperature_range(self) -> None:
        """Test app configuration validates temperature is between 0 and 2."""
        # Valid temperature values
        config1 = AppConfig(openai_api_key="sk-test", openai_temperature=0.0)
        config2 = AppConfig(openai_api_key="sk-test", openai_temperature=1.5)
        config3 = AppConfig(openai_api_key="sk-test", openai_temperature=2.0)

        assert config1.openai_temperature == 0.0
        assert config2.openai_temperature == 1.5
        assert config3.openai_temperature == 2.0

        # Invalid temperature values
        with pytest.raises(ValueError):
            AppConfig(openai_api_key="sk-test", openai_temperature=-0.1)

        with pytest.raises(ValueError):
            AppConfig(openai_api_key="sk-test", openai_temperature=2.1)

    def test_max_tokens_validation(self) -> None:
        """Test max tokens must be positive."""
        config = AppConfig(openai_api_key="sk-test", openai_max_tokens=500)
        assert config.openai_max_tokens == 500

        with pytest.raises(ValueError, match="OPENAI_MAX_TOKENS must be positive"):
            AppConfig(openai_api_key="sk-test", openai_max_tokens=0)

        with pytest.raises(ValueError, match="OPENAI_MAX_TOKENS must be positive"):
            AppConfig(openai_api_key="sk-test", openai_max_tokens=-100)

    def test_supported_languages_defaults(self) -> None:
        """Test supported languages uses correct default values."""
        config = AppConfig(openai_api_key="sk-test")
        assert config.supported_languages == ["english", "ukrainian", "polish", "german"]

    def test_supported_languages_validates_subset_of_enum(self) -> None:
        """Test supported languages must be subset of Language enum."""
        # Valid subset
        config = AppConfig(openai_api_key="sk-test", supported_languages=["english", "german"])
        assert config.supported_languages == ["english", "german"]

        # Invalid language not in enum
        with pytest.raises(ValueError, match="SUPPORTED_LANGUAGES contains unsupported language.*not in Language enum"):
            AppConfig(openai_api_key="sk-test", supported_languages=["english", "FR"])

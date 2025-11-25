"""
Tests for utility modules.

TODO: Phase 2 - Implement comprehensive unit tests
"""

import pytest

from app.utils.exceptions import AgentCouncilException, ConfigurationException
from app.utils.formatting import format_json, format_duration
from app.utils.settings import get_settings


def test_settings_load():
    """Test settings loading."""
    settings = get_settings()
    assert settings is not None
    assert settings.env in ["development", "staging", "production"]


def test_custom_exceptions():
    """Test custom exception hierarchy."""
    exc = AgentCouncilException("Test error", details={"key": "value"})
    assert str(exc) == "Test error"
    assert exc.details == {"key": "value"}

    config_exc = ConfigurationException("Config error")
    assert isinstance(config_exc, AgentCouncilException)


def test_format_json():
    """Test JSON formatting."""
    data = {"key": "value", "number": 42}
    formatted = format_json(data)
    assert "key" in formatted
    assert "value" in formatted


def test_format_duration():
    """Test duration formatting."""
    assert format_duration(30) == "30.00s"
    assert format_duration(90) == "1m 30s"
    assert format_duration(3665) == "1h 1m"


# TODO: Phase 2 - Add more comprehensive tests for:
# - Logging with redaction
# - Caching
# - Config loader
# - All formatting functions


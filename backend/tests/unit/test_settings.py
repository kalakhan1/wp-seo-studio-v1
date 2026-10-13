"""Unit tests for app.config.settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.constants import AppEnv, AppMode, LogFormat
from app.config.settings import Settings


def _make(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "app_env": "development",
        "app_debug": True,
        "app_mode": "mock",
        "log_level": "info",
        "log_format": "human",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def test_defaults_are_development_and_mock() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.app_env == AppEnv.DEVELOPMENT
    assert settings.app_mode == AppMode.MOCK
    assert settings.log_format == LogFormat.HUMAN
    assert settings.log_level == "info"


def test_log_level_is_normalized() -> None:
    settings = _make(log_level="DEBUG")
    assert settings.log_level == "debug"


def test_invalid_log_level_raises() -> None:
    with pytest.raises(ValidationError):
        _make(log_level="verbose")


def test_effective_mode_is_mock_in_development() -> None:
    settings = _make(app_env="development", app_mode="mock")
    assert settings.effective_app_mode == AppMode.MOCK
    assert settings.is_mock_mode is True
    assert settings.is_production is False


def test_effective_mode_is_forced_real_in_production() -> None:
    settings = _make(app_env="production", app_mode="mock")
    assert settings.effective_app_mode == AppMode.REAL
    assert settings.is_production is True


def test_wp_base_url_trailing_slash_is_stripped() -> None:
    settings = _make(wp_base_url="https://example.test/")
    assert settings.wp_base_url == "https://example.test"


def test_cors_origins_parses_comma_string() -> None:
    settings = _make(cors_origins="http://a.test, http://b.test")
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_mask_dump_hides_wp_password() -> None:
    settings = _make(wp_app_password="supersecretvalue")
    dumped = settings.masked_dump()
    assert dumped["wp_app_password"] == "***MASKED***"
    # Non-secret fields remain unchanged
    assert dumped["app_env"] == "development"


def test_port_bounds() -> None:
    with pytest.raises(ValidationError):
        _make(app_port=0)
    with pytest.raises(ValidationError):
        _make(app_port=70000)
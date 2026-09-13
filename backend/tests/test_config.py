import pytest

from core.config import get_settings


def test_production_cors_rejects_wildcard_and_accepts_exact_origin(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///temporary-config-check.db")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("FRONTEND_ORIGINS", "*")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="wildcards"):
        get_settings()

    monkeypatch.setenv("FRONTEND_ORIGINS", "https://billing.example.com")
    get_settings.cache_clear()
    assert get_settings().frontend_origins == ("https://billing.example.com",)
    get_settings.cache_clear()

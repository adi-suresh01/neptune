import importlib
import os


def test_cors_origins_production_disables_allow_all(monkeypatch):
    monkeypatch.setenv("NEPTUNE_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ALL", "true")
    monkeypatch.setenv("CORS_ORIGINS", "")

    settings_module = importlib.reload(importlib.import_module("app.core.settings"))
    settings = settings_module.settings

    assert settings.resolved_cors_origins() == []


def test_cors_origins_production_uses_explicit_list(monkeypatch):
    monkeypatch.setenv("NEPTUNE_ENV", "production")
    monkeypatch.setenv("CORS_ALLOW_ALL", "true")
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com,https://app.example.com")

    settings_module = importlib.reload(importlib.import_module("app.core.settings"))
    settings = settings_module.settings

    assert settings.resolved_cors_origins() == [
        "https://example.com",
        "https://app.example.com",
    ]

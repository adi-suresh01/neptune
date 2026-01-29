import importlib
from types import SimpleNamespace


def test_llm_cooldown(monkeypatch):
    monkeypatch.setenv("OLLAMA_MAX_RETRIES", "0")
    monkeypatch.setenv("OLLAMA_FAILURE_THRESHOLD", "1")
    monkeypatch.setenv("OLLAMA_COOLDOWN_SECONDS", "60")

    settings_module = importlib.reload(importlib.import_module("app.core.settings"))
    llm_module = importlib.reload(importlib.import_module("app.services.llm_service"))

    service = llm_module.LLMService()

    calls = {"count": 0}

    def failing_post(*args, **kwargs):
        calls["count"] += 1
        raise llm_module.requests.exceptions.Timeout()

    service.session.post = failing_post

    result = service._call_ollama("test", max_tokens=1)
    assert result == "unclassified"
    assert calls["count"] == 1

    result_again = service._call_ollama("test", max_tokens=1)
    assert result_again == "unclassified"
    assert calls["count"] == 1

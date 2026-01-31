import importlib


def _reload_modules():
    settings_module = importlib.reload(importlib.import_module("app.core.settings"))
    note_content_module = importlib.reload(importlib.import_module("app.services.note_content"))
    return settings_module, note_content_module


def test_store_note_content_db_mode(monkeypatch):
    monkeypatch.setenv("STORAGE_MODE", "db")
    monkeypatch.setenv("MAX_NOTE_BYTES", "1048576")

    settings_module, note_content = _reload_modules()
    from app.db.models import FileSystem

    item = FileSystem(id=1, name="Test", type="file")
    result = note_content.store_note_content(item, "hello")

    assert result.storage_backend == "db"
    assert item.content == "hello"
    assert item.storage_size == len("hello".encode("utf-8"))


def test_store_note_content_enforces_limit(monkeypatch):
    monkeypatch.setenv("STORAGE_MODE", "db")
    monkeypatch.setenv("MAX_NOTE_BYTES", "4")

    _settings_module, note_content = _reload_modules()
    from app.db.models import FileSystem

    item = FileSystem(id=2, name="Test", type="file")
    try:
        note_content.store_note_content(item, "hello")
        assert False, "Expected ValueError"
    except ValueError:
        assert True

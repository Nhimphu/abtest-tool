from __future__ import annotations

import logging
from pathlib import Path
from abtest_tool import plugin_loader


def _write_plugin(path: Path, name: str, content: str) -> None:
    (path / f"{name}.py").write_text(content)


def test_good_bad_wrong_abi(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "__init__.py").write_text("")
    _write_plugin(
        plugin_dir,
        "good",
        """
ABI_VERSION = "1.0"
name = "good"
version = "0.1"
capabilities = {"x"}

def register(app):
    pass
""",
    )
    _write_plugin(plugin_dir, "bad", "raise RuntimeError('boom')\n")
    _write_plugin(
        plugin_dir,
        "old",
        """
ABI_VERSION = "0.9"
name = "old"
version = "0.1"
capabilities = set()

def register(app):
    pass
""",
    )

    monkeypatch.setattr(plugin_loader, "LOCAL_PLUGIN_DIR", plugin_dir)
    monkeypatch.syspath_prepend(tmp_path)
    plugin_loader._DISCOVERED.clear()
    plugin_loader._LOADED.clear()
    plugin_loader.load_plugins()

    assert plugin_loader.get_plugin("good") is not None
    assert plugin_loader.get_plugin("bad") is None
    assert plugin_loader.get_plugin("old") is None
    text = caplog.text
    assert "Failed to import plugin" in text
    assert "ABI mismatch" in text


def test_missing_directory(monkeypatch):
    missing = Path("/nonexistent/directory")
    monkeypatch.setattr(plugin_loader, "LOCAL_PLUGIN_DIR", missing)
    plugin_loader._DISCOVERED.clear()
    plugin_loader._LOADED.clear()
    plugin_loader.load_plugins()
    assert plugin_loader.get_plugin("anything") is None

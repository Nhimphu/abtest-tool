"""Minimal plugin loader for local or entry-point based plugins."""
from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType

log = logging.getLogger(__name__)

LOCAL_PLUGIN_DIR: Path = Path("plugins")
LOCAL_PLUGIN_PACKAGE = "plugins"

_DISCOVERED: dict[str, str] = {}
_LOADED: dict[str, ModuleType] = {}

ABI_VERSION = "1.0"


def load_plugins() -> None:
    """Discover and import all available plugins."""

    _DISCOVERED.clear()
    _LOADED.clear()
    if LOCAL_PLUGIN_DIR and LOCAL_PLUGIN_DIR.is_dir():
        parent = LOCAL_PLUGIN_DIR.resolve().parent
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        importlib.invalidate_caches()
        for p in LOCAL_PLUGIN_DIR.glob("*.py"):
            name = p.stem
            if name.startswith("_"):
                continue
            import_name = f"{LOCAL_PLUGIN_PACKAGE}.{name}"
            _DISCOVERED[name] = import_name
            try:
                mod = importlib.import_module(import_name)
            except Exception as e:  # pragma: no cover - plugin import may fail
                log.warning("Failed to import plugin %s: %s", import_name, e)
                continue
            plugin_abi = getattr(mod, "ABI_VERSION", None)
            if plugin_abi is not None and plugin_abi != ABI_VERSION:
                log.warning(
                    "Skip plugin %s due to ABI mismatch (%s != %s)",
                    import_name,
                    plugin_abi,
                    ABI_VERSION,
                )
                continue
            _LOADED[name] = mod


def get_plugin(name: str) -> ModuleType | None:
    """Return loaded plugin module by ``name``."""

    return _LOADED.get(name)


__all__ = [
    "load_plugins",
    "get_plugin",
    "LOCAL_PLUGIN_DIR",
    "_DISCOVERED",
    "_LOADED",
    "ABI_VERSION",
]


"""Discovery and loading of optional plugins."""
from __future__ import annotations

import importlib
import logging
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Dict, Iterator, Iterable

from .plugins import PluginBase

logger = logging.getLogger(__name__)

ENTRY_POINT = "abtest_tool.plugins"
LOCAL_PLUGIN_DIR = Path(__file__).resolve().parent.parent.parent / "plugins"

_DISCOVERED: Dict[str, str] = {}
_LOADED: Dict[str, ModuleType] = {}


def _discover() -> None:
    if _DISCOVERED:
        return
    # Local plugins directory
    if LOCAL_PLUGIN_DIR.is_dir():
        for path in LOCAL_PLUGIN_DIR.glob("*.py"):
            if path.name.startswith("_"):
                continue
            name = path.stem
            _DISCOVERED[name] = f"plugins.{name}"
    # Entry point plugins
    try:
        eps: Iterable[metadata.EntryPoint] = metadata.entry_points().select(group=ENTRY_POINT)
    except Exception:  # pragma: no cover - metadata failure
        eps = ()
    for ep in eps:
        _DISCOVERED[ep.name] = ep.value


def _import(name: str, module: str) -> ModuleType | None:
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - plugin import may fail
        logger.warning("Failed to import plugin %s: %s", module, exc)
        return None
    abi = getattr(mod, "ABI_VERSION", None)
    if abi != PluginBase.ABI_VERSION:
        logger.warning(
            "Skipping plugin %s due to ABI mismatch (%s != %s)",
            module,
            abi,
            PluginBase.ABI_VERSION,
        )
        return None
    return mod


def load_plugin(name: str) -> ModuleType | None:
    """Load plugin by ``name`` if available."""
    _discover()
    if name in _LOADED:
        return _LOADED[name]
    module = _DISCOVERED.get(name)
    if not module:
        return None
    mod = _import(name, module)
    if mod:
        _LOADED[name] = mod
    return mod


def iter_plugins() -> Iterator[ModuleType]:
    """Iterate over all available plugins, importing them lazily."""
    _discover()
    for name in list(_DISCOVERED):
        mod = load_plugin(name)
        if mod:
            yield mod


def load_plugins() -> None:
    """Import all available plugins."""
    for _ in iter_plugins():
        pass


def get_plugin(name: str) -> ModuleType | None:
    """Return loaded plugin module by ``name``."""
    return _LOADED.get(name)


__all__ = [
    "load_plugins",
    "iter_plugins",
    "get_plugin",
    "load_plugin",
    "LOCAL_PLUGIN_DIR",
]

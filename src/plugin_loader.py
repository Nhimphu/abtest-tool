"""Utility to automatically load optional plugins."""
import importlib
import os
import sys
from types import ModuleType
from typing import Dict

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PLUGIN_DIR = os.path.join(ROOT_DIR, 'plugins')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

_loaded: Dict[str, ModuleType] = {}


def load_plugins() -> None:
    """Import all plugin modules from :mod:`plugins` if available."""
    if not os.path.isdir(PLUGIN_DIR):
        return
    for fname in os.listdir(PLUGIN_DIR):
        if not fname.endswith('.py') or fname.startswith('_'):
            continue
        name = fname[:-3]
        mod_name = f'plugins.{name}'
        if name in _loaded:
            continue
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        _loaded[name] = mod


def get_plugin(name: str) -> ModuleType | None:
    """Return loaded plugin module by ``name``."""
    return _loaded.get(name)


load_plugins()

from __future__ import annotations

import importlib


def lazy_import(name: str):
    """Import a module only when needed."""
    return importlib.import_module(name)

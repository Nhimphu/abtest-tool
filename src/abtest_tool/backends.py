"""Lazy backend resolver for optional heavy dependencies."""
from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any


@lru_cache()
def get_backend(name: str) -> Any:
    """Return the imported module ``name`` lazily.

    Parameters
    ----------
    name:
        Dotted module path to import.

    Raises
    ------
    ImportError
        If the module cannot be imported.
    """
    try:
        return importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - optional dependency may be missing
        raise ImportError(f"Backend '{name}' is required but not installed") from exc


__all__ = ["get_backend"]

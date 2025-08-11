"""Lazy backend resolver for optional heavy dependencies."""
from __future__ import annotations

import importlib
import sys
from typing import Any

_BACKENDS: dict[str, Any] = {}


def get_backend(name: str) -> Any:
    """Import and cache the module identified by ``name``.

    Parameters
    ----------
    name:
        Full dotted module path to import, e.g. ``"plotly.graph_objects"``.
    """

    mod = _BACKENDS.get(name)
    if mod is not None:
        return mod
    mod = sys.modules.get(name)
    if mod is None:
        mod = importlib.import_module(name)
    _BACKENDS[name] = mod
    return mod


__all__ = ["get_backend"]


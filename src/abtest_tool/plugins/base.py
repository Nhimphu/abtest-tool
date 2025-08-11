"""Base protocol for abtest-tool plugins."""
from __future__ import annotations

from typing import Protocol, Set, Any


class PluginBase(Protocol):
    """Common interface for plugins."""

    name: str
    version: str
    capabilities: Set[str]
    ABI_VERSION: str = "1.0"

    def register(self, app: Any) -> None:
        """Register plugin in the given application context."""
        ...


__all__ = ["PluginBase"]

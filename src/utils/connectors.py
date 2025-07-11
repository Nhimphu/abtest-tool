"""Lightweight wrappers delegating to optional connector plugins."""

from typing import Any, Dict, List

import plugin_loader

_plug = plugin_loader.get_plugin("connectors")

if _plug and hasattr(_plug, "BigQueryConnector"):
    BigQueryConnector = _plug.BigQueryConnector  # type: ignore
else:

    class BigQueryConnector:
        """Fallback that signals missing plugin."""

        def __init__(self, *_: Any, **__: Any) -> None:
            raise ImportError("BigQueryConnector plugin not available")


if _plug and hasattr(_plug, "RedshiftConnector"):
    RedshiftConnector = _plug.RedshiftConnector  # type: ignore
else:

    class RedshiftConnector:
        """Fallback that signals missing plugin."""

        def __init__(self, *_: Any, **__: Any) -> None:
            raise ImportError("RedshiftConnector plugin not available")


__all__ = ["BigQueryConnector", "RedshiftConnector"]


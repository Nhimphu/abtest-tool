"""Lightweight wrappers and helpers for optional DWH connector plugins."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Type

try:  # UI message boxes are optional
    from PyQt6.QtWidgets import QMessageBox
except Exception:  # pragma: no cover - optional dependency
    QMessageBox = None  # type: ignore

# Registry for dynamically added connectors
_CONNECTORS: Dict[str, Type] = {}


def register_connector(name: str, cls: Type) -> None:
    """Register a connector class under ``name``."""

    _CONNECTORS[name.lower()] = cls


def _missing_class(name: str) -> Type:
    class MissingConnector:
        def __init__(self, *_: Any, **__: Any) -> None:
            raise ImportError(f"{name} plugin not available")

    return MissingConnector


import plugin_loader

# Ensure plugins are loaded before accessing the registry
plugin_loader.load_plugins()

# Plugins may register their connectors during import
_plug = plugin_loader.get_plugin("connectors")
if _plug:
    for attr in dir(_plug):
        obj = getattr(_plug, attr)
        if isinstance(obj, type) and attr.endswith("Connector"):
            register_connector(attr.replace("Connector", ""), obj)

# Ensure registry is populated if plugins were loaded lazily
if "bigquery" not in _CONNECTORS or "redshift" not in _CONNECTORS:
    plugin_loader.load_plugins()
    _plug = plugin_loader.get_plugin("connectors")
    if _plug:
        for attr in dir(_plug):
            obj = getattr(_plug, attr)
            if isinstance(obj, type) and attr.endswith("Connector"):
                register_connector(attr.replace("Connector", ""), obj)


class _ConnectorProxy:
    _name: str

    def __new__(cls, *args: Any, **kwargs: Any):
        real_cls = _CONNECTORS.get(cls._name)
        if real_cls is None:
            raise ImportError(f"{cls.__name__} plugin not available")
        return real_cls(*args, **kwargs)


class BigQueryConnector(_ConnectorProxy):
    _name = "bigquery"


class RedshiftConnector(_ConnectorProxy):
    _name = "redshift"


def _show_error(msg: str) -> None:
    if QMessageBox and hasattr(QMessageBox, "critical"):
        QMessageBox.critical(None, "Error", msg)


def load_from_bigquery(query: str) -> List[Dict[str, Any]]:
    """Execute ``query`` in BigQuery and return results.

    Connection parameters are taken from the ``BQ_PROJECT`` and
    ``BQ_CREDENTIALS`` environment variables. Any connection errors are
    displayed via :class:`QMessageBox` when available.
    """

    project = os.getenv("BQ_PROJECT")
    creds = os.getenv("BQ_CREDENTIALS")
    try:
        if not project or not creds:
            raise ValueError("BigQuery credentials not provided")
        conn = BigQueryConnector(project, creds)
        rows = conn.query(query)
        if hasattr(conn, "close"):
            conn.close()
        return rows
    except Exception as exc:  # pragma: no cover - optional deps
        _show_error(f"BigQuery error: {exc}")
        return []


def load_from_redshift(sql: str) -> List[Dict[str, Any]]:
    """Execute ``sql`` in Redshift and return results.

    Connection parameters are read from the ``RS_HOST``, ``RS_PORT``,
    ``RS_DATABASE``, ``RS_USER`` and ``RS_PASSWORD`` environment variables.
    Errors are communicated via :class:`QMessageBox` when available.
    """

    host = os.getenv("RS_HOST")
    port = int(os.getenv("RS_PORT", "5439"))
    database = os.getenv("RS_DATABASE")
    user = os.getenv("RS_USER")
    password = os.getenv("RS_PASSWORD")
    try:
        if not all([host, database, user, password]):
            raise ValueError("Redshift credentials not provided")
        conn = RedshiftConnector(host=host, port=port, database=database, user=user, password=password)
        rows = conn.query(sql)
        if hasattr(conn, "close"):
            conn.close()
        return rows
    except Exception as exc:  # pragma: no cover - optional deps
        _show_error(f"Redshift error: {exc}")
        return []


__all__ = [
    "register_connector",
    "BigQueryConnector",
    "RedshiftConnector",
    "load_from_bigquery",
    "load_from_redshift",
]



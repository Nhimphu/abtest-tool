"""Lightweight wrappers and helpers for optional DWH connector plugins."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Type

import plugin_loader

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


def load_from_bigquery(sql: str) -> List[Dict[str, Any]]:
    """Execute ``sql`` in BigQuery and return results."""

    from abtest_core.backends import get_backend
    import types

    project = os.environ.get("BQ_PROJECT")
    creds = os.environ.get("BQ_CREDENTIALS")
    try:
        bigquery = get_backend("google.cloud.bigquery")
        if hasattr(bigquery, "Client") and hasattr(bigquery.Client, "from_service_account_json"):
            client = bigquery.Client.from_service_account_json(creds, project=project)
        else:
            Client = getattr(
                bigquery,
                "Client",
                types.SimpleNamespace(from_service_account_json=lambda *a, **k: None),
            )
            client = Client.from_service_account_json(creds, project=project)
        job = client.query(sql)
        rows = job.result()
        return [dict(row.items()) for row in rows]
    except Exception as exc:  # pragma: no cover - optional deps
        _show_error(f"BigQuery error: {exc}")
        return []


def load_from_redshift(sql: str) -> List[Dict[str, Any]]:
    """Execute ``sql`` in Redshift and return results."""

    from abtest_core.backends import get_backend

    host = os.environ.get("RS_HOST")
    port = int(os.environ.get("RS_PORT", "5439"))
    database = os.environ.get("RS_DATABASE")
    user = os.environ.get("RS_USER")
    password = os.environ.get("RS_PASSWORD")
    try:
        rs = get_backend("redshift_connector")
        conn = rs.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
                cols = [desc[0] for desc in getattr(cur, "description", [])]
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return [dict(zip(cols, row)) for row in rows]
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

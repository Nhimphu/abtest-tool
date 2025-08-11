"""Data source connectors for BigQuery and Redshift.

Both connectors rely on the official client libraries. They are imported
on demand so that the optional dependencies are only required when a
particular connector is used.
"""

from typing import Any, Dict, List, Set

from abtest_core.backends import get_backend
from utils.connectors import register_connector

ABI_VERSION = "1.0"
name = "connectors"
version = "0.1"
capabilities: Set[str] = {"dwh"}


class BigQueryConnector:
    """Simple wrapper around the BigQuery client."""

    def __init__(self, project: str, credentials_path: str) -> None:
        bigquery = get_backend("google.cloud.bigquery")
        self._client = bigquery.Client.from_service_account_json(credentials_path, project=project)

    def query(self, sql: str) -> List[Dict[str, Any]]:
        result = self._client.query(sql).result()
        return [dict(row.items()) for row in result]

    def close(self) -> None:
        """BigQuery client does not require explicit close but provided for API consistency."""
        return None


class RedshiftConnector:
    """Redshift connector using the official ``redshift-connector`` package."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str) -> None:
        redshift_connector = get_backend("redshift_connector")
        self._conn = redshift_connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
        )

    def query(self, sql: str) -> List[Dict[str, Any]]:
        with self._conn.cursor() as cur:
            cur.execute(sql)
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]

    def close(self) -> None:
        self._conn.close()


def register(app: Any) -> None:  # noqa: D401 - simple delegation
    """Register connectors in the global registry."""
    register_connector("bigquery", BigQueryConnector)
    register_connector("redshift", RedshiftConnector)


# Automatically register when imported
register(None)

__all__ = ["BigQueryConnector", "RedshiftConnector", "register"]

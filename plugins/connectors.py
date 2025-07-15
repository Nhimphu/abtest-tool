"""Data source connectors for BigQuery and Redshift.

Both connectors rely on the official client libraries. They are imported
inside the initializer so that the optional dependencies are only required
when a particular connector is used.
"""

from typing import Any, Dict, List
from utils.connectors import register_connector


class BigQueryConnector:
    """Simple wrapper around the BigQuery client."""

    def __init__(self, project: str, credentials_path: str) -> None:
        try:
            from google.cloud import bigquery  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            raise ImportError("google-cloud-bigquery is required for BigQueryConnector")
        self._client = bigquery.Client.from_service_account_json(credentials_path, project=project)

    def query(self, sql: str) -> List[Dict[str, Any]]:
        result = self._client.query(sql).result()
        return [dict(row.items()) for row in result]

    def close(self) -> None:
        """BigQuery client does not require explicit close but provided for API consistency."""
        pass


class RedshiftConnector:
    """Redshift connector using the official ``redshift-connector`` package."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str) -> None:
        try:
            import redshift_connector  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            raise ImportError("redshift-connector is required for RedshiftConnector")
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


register_connector("bigquery", BigQueryConnector)
register_connector("redshift", RedshiftConnector)

__all__ = ["BigQueryConnector", "RedshiftConnector"]

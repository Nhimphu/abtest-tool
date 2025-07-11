"""Data source connectors for BigQuery and Redshift."""

from typing import Any, Dict, List


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


class RedshiftConnector:
    """Simple Redshift connector using psycopg2."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str) -> None:
        try:
            import psycopg2  # type: ignore
        except Exception:  # pragma: no cover - optional dependency
            raise ImportError("psycopg2 is required for RedshiftConnector")
        self._conn = psycopg2.connect(host=host, port=port, dbname=database, user=user, password=password)

    def query(self, sql: str) -> List[Dict[str, Any]]:
        with self._conn.cursor() as cur:
            cur.execute(sql)
            cols = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]


__all__ = ["BigQueryConnector", "RedshiftConnector"]


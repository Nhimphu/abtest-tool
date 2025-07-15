import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.connectors import (
    BigQueryConnector,
    RedshiftConnector,
    load_from_bigquery,
    load_from_redshift,
)


def test_bigquery_connector_queries(monkeypatch):
    called = {}
    class DummyResult:
        def result(self):
            return [types.SimpleNamespace(items=lambda: [('a', 1)])]
    class DummyClient:
        def query(self, sql):
            called['sql'] = sql
            return DummyResult()

    bigquery_mod = types.ModuleType('google.cloud.bigquery')
    bigquery_mod.Client = types.SimpleNamespace(from_service_account_json=lambda p, project=None: DummyClient())
    cloud_mod = types.ModuleType('google.cloud')
    cloud_mod.bigquery = bigquery_mod
    monkeypatch.setitem(sys.modules, 'google', types.ModuleType('google'))
    monkeypatch.setitem(sys.modules, 'google.cloud', cloud_mod)
    monkeypatch.setitem(sys.modules, 'google.cloud.bigquery', bigquery_mod)

    conn = BigQueryConnector('p', 'c.json')
    rows = conn.query('SELECT 1')
    assert called['sql'] == 'SELECT 1'
    assert rows == [{'a': 1}]


def test_redshift_connector_queries(monkeypatch):
    called = {}
    class DummyCursor:
        description = [('a',)]
        def execute(self, sql):
            called['sql'] = sql
        def fetchall(self):
            return [(2,)]
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
    class DummyConn:
        def cursor(self):
            return DummyCursor()
        def close(self):
            pass
    rs_mod = types.ModuleType('redshift_connector')
    rs_mod.connect = lambda **kw: DummyConn()
    monkeypatch.setitem(sys.modules, 'redshift_connector', rs_mod)

    conn = RedshiftConnector('h', 5439, 'db', 'u', 'p')
    rows = conn.query('SELECT 1')
    assert called['sql'] == 'SELECT 1'
    assert rows == [{'a': 2}]


def test_load_from_bigquery(monkeypatch):
    called = {}
    class DummyResult:
        def result(self):
            return [types.SimpleNamespace(items=lambda: [('a', 1)])]
    class DummyClient:
        def query(self, sql):
            called['sql'] = sql
            return DummyResult()

    bigquery_mod = types.ModuleType('google.cloud.bigquery')
    bigquery_mod.Client = types.SimpleNamespace(from_service_account_json=lambda p, project=None: DummyClient())
    cloud_mod = types.ModuleType('google.cloud')
    cloud_mod.bigquery = bigquery_mod
    monkeypatch.setitem(sys.modules, 'google', types.ModuleType('google'))
    monkeypatch.setitem(sys.modules, 'google.cloud', cloud_mod)
    monkeypatch.setitem(sys.modules, 'google.cloud.bigquery', bigquery_mod)

    monkeypatch.setenv('BQ_PROJECT', 'p')
    monkeypatch.setenv('BQ_CREDENTIALS', 'c.json')

    rows = load_from_bigquery('SELECT 1')
    assert called['sql'] == 'SELECT 1'
    assert rows == [{'a': 1}]


def test_load_from_redshift(monkeypatch):
    called = {}
    class DummyCursor:
        description = [('a',)]
        def execute(self, sql):
            called['sql'] = sql
        def fetchall(self):
            return [(2,)]
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
    class DummyConn:
        def cursor(self):
            return DummyCursor()
        def close(self):
            pass
    rs_mod = types.ModuleType('redshift_connector')
    rs_mod.connect = lambda **kw: DummyConn()
    monkeypatch.setitem(sys.modules, 'redshift_connector', rs_mod)

    monkeypatch.setenv('RS_HOST', 'h')
    monkeypatch.setenv('RS_PORT', '5439')
    monkeypatch.setenv('RS_DATABASE', 'db')
    monkeypatch.setenv('RS_USER', 'u')
    monkeypatch.setenv('RS_PASSWORD', 'p')

    rows = load_from_redshift('SELECT 1')
    assert called['sql'] == 'SELECT 1'
    assert rows == [{'a': 2}]

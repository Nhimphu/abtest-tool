import os
import sys
import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_jwt_extended")
pytest.importorskip("flask_swagger_ui")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.flags import create_app as create_flags_app
from api.analysis import create_app as create_analysis_app

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")


@pytest.fixture
def flags_client(tmp_path):
    os.environ['FLAGS_DB'] = str(tmp_path / 'flags.db')
    app = create_flags_app()
    return app.test_client()


@pytest.fixture
def analysis_client():
    app = create_analysis_app()
    return app.test_client()


def _login(client):
    resp = client.post('/login', json={'username': 'admin', 'password': 'admin'})
    assert resp.status_code == 200
    return resp.get_json()['access_token']


def test_docs_available(flags_client, analysis_client):
    assert flags_client.get('/docs/').status_code == 200
    assert analysis_client.get('/docs/').status_code == 200


def test_flags_crud(flags_client):
    token = _login(flags_client)
    headers = {'Authorization': f'Bearer {token}'}

    resp = flags_client.get('/flags', headers=headers)
    assert resp.status_code == 200
    assert resp.get_json() == []

    resp = flags_client.post(
        '/flags',
        json={'name': 'feat1', 'enabled': True, 'rollout': 60},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.get_json()['name'] == 'feat1'

    resp = flags_client.get('/flags', headers=headers)
    assert any(f['name'] == 'feat1' for f in resp.get_json())

    resp = flags_client.put(
        '/flags/feat1',
        json={'enabled': False, 'rollout': 20},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['enabled'] is False
    assert data['rollout'] == 20

    resp = flags_client.delete('/flags/feat1', headers=headers)
    assert resp.status_code == 204

    resp = flags_client.get('/flags', headers=headers)
    assert all(f['name'] != 'feat1' for f in resp.get_json())


def test_analyze_endpoint(analysis_client):
    token = _login(analysis_client)
    headers = {'Authorization': f'Bearer {token}'}

    payload = {'users_a': 10, 'conv_a': 1, 'users_b': 10, 'conv_b': 2}
    resp = analysis_client.post('/abtest', json=payload, headers=headers)
    assert resp.status_code == 200
    assert 'p_value_ab' in resp.get_json()


def test_metrics_endpoint(analysis_client):
    resp = analysis_client.get('/metrics')
    assert resp.status_code == 200


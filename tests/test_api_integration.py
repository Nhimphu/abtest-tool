import os
import sys
import importlib.util
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

if importlib.util.find_spec('flask') is None:
    pytest.skip('Flask not available', allow_module_level=True)

from analysis_api import create_app


def test_abtest_endpoint():
    app = create_app()
    client = app.test_client()
    resp = client.post('/abtest', json={
        'users_a': 100,
        'conv_a': 10,
        'users_b': 100,
        'conv_b': 20,
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'p_value_ab' in data

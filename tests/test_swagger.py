import os
import sys
import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_swagger_ui")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.analysis import create_app as create_analysis_app
from api.flags import create_app as create_flags_app


def test_analysis_docs_available():
    app = create_analysis_app()
    with app.test_client() as client:
        resp = client.get('/docs/')
        assert resp.status_code == 200


def test_flags_docs_available():
    app = create_flags_app()
    with app.test_client() as client:
        resp = client.get('/docs/')
        assert resp.status_code == 200

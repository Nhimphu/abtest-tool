import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

pytest = __import__("pytest")
pytest.importorskip("flask")
pytest.importorskip("flask_jwt_extended")

from api.flags import create_app as create_flags_app

os.environ.setdefault("JWT_SECRET_KEY", "test-secret")


def test_login_and_protected_endpoint():
    app = create_flags_app()
    with app.test_client() as client:
        resp = client.post("/login", json={"username": "admin", "password": "admin"})
        assert resp.status_code == 200
        data = resp.get_json()
        token = data["access_token"]
        refresh = data["refresh_token"]

        resp = client.post("/refresh", headers={"Authorization": f"Bearer {refresh}"})
        assert resp.status_code == 200
        new_token = resp.get_json()["access_token"]

        resp = client.get("/flags")
        assert resp.status_code == 401

        resp = client.get("/flags", headers={"Authorization": f"Bearer {new_token}"})
        assert resp.status_code == 200

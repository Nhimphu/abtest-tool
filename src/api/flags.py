import os
import time
from flask import Flask, jsonify, request, g
from flask_swagger_ui import get_swaggerui_blueprint
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flags import FeatureFlagStore
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    make_wsgi_app,
)
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from metrics import track_time


def create_app() -> Flask:
    app = Flask(__name__)
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is required")
    app.config["JWT_SECRET_KEY"] = jwt_secret
    JWTManager(app)
    registry = CollectorRegistry()

    swaggerui_blueprint = get_swaggerui_blueprint(
        "/docs",
        "/spec",
        config={
            "app_name": "Flags API",
            "supportedSubmitMethods": ["get", "post", "put", "delete"],
        },
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix="/docs")
    store = FeatureFlagStore()

    REQUEST_COUNTER = Counter(
        "flags_requests_total",
        "Total requests to flags API",
        ["endpoint", "method", "status"],
        registry=registry,
    )
    REQUEST_LATENCY = Histogram(
        "flags_request_seconds",
        "Request latency for flags API",
        ["endpoint"],
        registry=registry,
    )

    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app, {"/metrics": make_wsgi_app(registry)}
    )

    @app.before_request
    def start_timer():
        g._start_time = time.perf_counter()

    @app.after_request
    def record_metrics(response):
        REQUEST_COUNTER.labels(request.path, request.method, response.status_code).inc()
        if hasattr(g, "_start_time"):
            REQUEST_LATENCY.labels(request.path).observe(time.perf_counter() - g._start_time)
        return response


    @app.post("/login")
    @track_time
    def login():
        data = request.get_json(force=True)
        if data.get("username") == "admin" and data.get("password") == "admin":
            access = create_access_token(identity="admin")
            refresh = create_refresh_token(identity="admin")
            return jsonify(access_token=access, refresh_token=refresh)
        return (
            jsonify(
                {
                    "code": "auth_failed",
                    "title": "Bad credentials",
                    "details": "Invalid username or password",
                    "fix_hint": "Verify provided credentials",
                }
            ),
            401,
        )

    @app.post("/refresh")
    @jwt_required(refresh=True)
    @track_time
    def refresh():
        identity = get_jwt_identity()
        token = create_access_token(identity=identity)
        return jsonify(access_token=token)

    @app.route("/flags", methods=["GET"])
    @jwt_required()
    @track_time
    def list_flags():
        flags = store.list_flags()
        return jsonify([flag.__dict__ for flag in flags])

    @app.route("/spec", methods=["GET"])
    def spec():
        """Return minimal OpenAPI spec."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Flags API", "version": "1.0"},
            "servers": [{"url": "/"}],
            "paths": {
                "/login": {"post": {"responses": {"200": {"description": "Login"}}}},
                "/refresh": {
                    "post": {"responses": {"200": {"description": "Refresh"}}}
                },
                "/metrics": {"get": {"responses": {"200": {"description": "Metrics"}}}},
                "/flags": {
                    "get": {"responses": {"200": {"description": "List flags"}}},
                    "post": {"responses": {"201": {"description": "Created"}}},
                },
                "/flags/{name}": {
                    "put": {"responses": {"200": {"description": "Updated"}}},
                    "delete": {"responses": {"204": {"description": "Deleted"}}},
                },
            },
        }
        return jsonify(spec)

    @app.route("/flags", methods=["POST"])
    @jwt_required()
    @track_time
    def create_flag():
        data = request.get_json(force=True)
        flag = store.create_flag(
            data["name"],
            enabled=data.get("enabled", False),
            rollout=data.get("rollout", 100.0),
        )
        return jsonify(flag.__dict__), 201

    @app.route("/flags/<name>", methods=["PUT"])
    @jwt_required()
    @track_time
    def update_flag(name):
        data = request.get_json(force=True)
        flag = store.update_flag(
            name,
            enabled=data.get("enabled"),
            rollout=data.get("rollout"),
        )
        return jsonify(flag.__dict__)

    @app.route("/flags/<name>", methods=["DELETE"])
    @jwt_required()
    @track_time
    def delete_flag(name):
        store.delete_flag(name)
        return "", 204

    return app


def main():
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()

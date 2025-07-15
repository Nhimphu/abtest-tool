import os
from flask import Flask, jsonify, request, Response
from flask_swagger_ui import get_swaggerui_blueprint
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flags import FeatureFlagStore
from metrics import (
    REQUEST_COUNTER,
    generate_latest,
    CONTENT_TYPE_LATEST,
    track_time,
)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "secret")
    jwt = JWTManager(app)

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

    @app.after_request
    def record_metrics(response: Response) -> Response:
        REQUEST_COUNTER.labels(request.path, request.method, response.status_code).inc()
        return response

    @app.route("/metrics")
    def metrics() -> tuple[bytes, int, dict[str, str]]:
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    @app.post("/login")
    @track_time
    def login() -> Response:
        data = request.get_json(force=True)
        if data.get("username") == "admin" and data.get("password") == "admin":
            access = create_access_token(identity="admin")
            refresh = create_refresh_token(identity="admin")
            return jsonify(access_token=access, refresh_token=refresh)
        return jsonify({"msg": "Bad credentials"}), 401

    @app.post("/refresh")
    @jwt_required(refresh=True)
    @track_time
    def refresh() -> Response:
        identity = get_jwt_identity()
        token = create_access_token(identity=identity)
        return jsonify(access_token=token)

    @app.route("/flags", methods=["GET"])
    @jwt_required()
    @track_time
    def list_flags() -> Response:
        flags = store.list_flags()
        return jsonify([flag.__dict__ for flag in flags])

    @app.route("/spec", methods=["GET"])
    def spec() -> Response:
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
    def create_flag() -> tuple[Response, int]:
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
    def update_flag(name: str) -> Response:
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
    def delete_flag(name: str) -> tuple[str, int]:
        store.delete_flag(name)
        return "", 204

    return app


def main() -> None:
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()

"""Minimal Flask API exposing core analysis helpers."""

import os
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flask_swagger_ui import get_swaggerui_blueprint
from stats.ab_test import evaluate_abn_test
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
            "app_name": "Analysis API",
            "supportedSubmitMethods": ["get", "post", "put", "delete"],
        },
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix="/docs")

    @app.after_request
    def record_metrics(response):
        REQUEST_COUNTER.labels(request.path, request.method, response.status_code).inc()
        return response

    @app.route("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    @app.post("/login")
    @track_time
    def login():
        data = request.get_json(force=True)
        if data.get("username") == "admin" and data.get("password") == "admin":
            access = create_access_token(identity="admin")
            refresh = create_refresh_token(identity="admin")
            return jsonify(access_token=access, refresh_token=refresh)
        return jsonify({"msg": "Bad credentials"}), 401

    @app.post("/refresh")
    @jwt_required(refresh=True)
    @track_time
    def refresh():
        identity = get_jwt_identity()
        token = create_access_token(identity=identity)
        return jsonify(access_token=token)

    @app.route("/abtest", methods=["POST"])
    @jwt_required()
    @track_time
    def run_abtest():
        data = request.get_json(force=True)
        res = evaluate_abn_test(
            data["users_a"],
            data["conv_a"],
            data["users_b"],
            data["conv_b"],
            metrics=data.get("metrics", 1),
            alpha=data.get("alpha", 0.05),
        )
        return jsonify(res)

    @app.route("/spec", methods=["GET"])
    def spec():
        """Return minimal OpenAPI spec."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Analysis API", "version": "1.0"},
            "servers": [{"url": "/"}],
            "paths": {
                "/login": {"post": {"responses": {"200": {"description": "Login"}}}},
                "/refresh": {
                    "post": {"responses": {"200": {"description": "Refresh"}}}
                },
                "/abtest": {
                    "post": {"responses": {"200": {"description": "AB test result"}}}
                },
                "/metrics": {"get": {"responses": {"200": {"description": "Metrics"}}}},
            },
        }
        return jsonify(spec)

    return app


def main():
    app = create_app()
    port = int(os.environ.get("PORT", "5000"))
    app.run(port=port)


if __name__ == "__main__":
    main()

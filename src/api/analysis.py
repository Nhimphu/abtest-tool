"""Minimal Flask API exposing core analysis helpers."""

import os
import time
from flask import Flask, jsonify, request, g
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flask_swagger_ui import get_swaggerui_blueprint
from stats.ab_test import evaluate_abn_test
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from metrics import track_time


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

    REQUEST_COUNTER = Counter(
        "analysis_requests_total",
        "Total requests to analysis API",
        ["endpoint", "method", "status"],
    )
    REQUEST_LATENCY = Histogram(
        "analysis_request_seconds",
        "Request latency for analysis API",
        ["endpoint"],
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
            "components": {
                "schemas": {
                    "Login": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string"},
                            "password": {"type": "string"},
                        },
                        "required": ["username", "password"],
                    },
                    "Token": {
                        "type": "object",
                        "properties": {
                            "access_token": {"type": "string"},
                            "refresh_token": {"type": "string"},
                        },
                    },
                    "AbTestRequest": {
                        "type": "object",
                        "properties": {
                            "users_a": {"type": "integer"},
                            "conv_a": {"type": "integer"},
                            "users_b": {"type": "integer"},
                            "conv_b": {"type": "integer"},
                            "metrics": {"type": "integer"},
                            "alpha": {"type": "number"},
                        },
                        "required": ["users_a", "conv_a", "users_b", "conv_b"],
                    },
                }
            },
            "paths": {
                "/login": {
                    "post": {
                        "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Login"}}}},
                        "responses": {"200": {"description": "Login", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Token"}}}}},
                    }
                },
                "/refresh": {
                    "post": {
                        "responses": {"200": {"description": "Refresh", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Token"}}}}}
                    }
                },
                "/abtest": {
                    "post": {
                        "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/AbTestRequest"}}}},
                        "responses": {"200": {"description": "AB test result"}},
                    }
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

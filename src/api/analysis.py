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
import pandas as pd
from abtest_core.srm import SrmCheckFailed
from abtest_core import AnalysisConfig, analyze_groups
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from metrics import track_time
from abtest_core import DataSchema, validate_dataframe, ValidationError


def create_app() -> Flask:
    app = Flask(__name__)
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is required")
    app.config["JWT_SECRET_KEY"] = jwt_secret
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

    registry = CollectorRegistry()

    REQUEST_COUNTER = Counter(
        "analysis_requests_total",
        "Total requests to analysis API",
        ["endpoint", "method", "status"],
        registry=registry,
    )
    REQUEST_LATENCY = Histogram(
        "analysis_request_seconds",
        "Request latency for analysis API",
        ["endpoint"],
        registry=registry,
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
        return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}

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

    @app.route("/abtest", methods=["POST"])
    @jwt_required()
    @track_time
    def run_abtest():
        data = request.get_json(force=True)

        # Optional dataframe validation if raw rows are provided
        if "rows" in data and "schema" in data:
            df = pd.DataFrame(data["rows"])
            schema = DataSchema(**data["schema"])
            nan_policy = data.get("nan_policy", "drop")
            try:
                validate_dataframe(df, schema, nan_policy=nan_policy)
            except ValidationError as e:
                return jsonify(e.to_dict()), 400

        try:
            users_a, conv_a = data["users_a"], data["conv_a"]
            users_b, conv_b = data["users_b"], data["conv_b"]
            df = pd.DataFrame(
                {
                    "group": ["A"] * users_a + ["B"] * users_b,
                    "metric": [1] * conv_a + [0] * (users_a - conv_a) + [1] * conv_b + [0] * (users_b - conv_b),
                }
            )
            config = AnalysisConfig(alpha=data.get("alpha", 0.05), metric_type="binomial")
            res = analyze_groups(df, config)
        except SrmCheckFailed as e:
            return jsonify(e.to_dict()), 400
        return jsonify(
            {
                "cr_a": conv_a / users_a,
                "cr_b": conv_b / users_b,
                "p_value_ab": res.p_value,
                "effect": res.effect,
                "ci": res.ci,
                "method_notes": res.method_notes,
            }
        )

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
                            "force_run_when_srm_failed": {"type": "boolean"},
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

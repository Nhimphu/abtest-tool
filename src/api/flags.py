import os
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
)
from flags import FeatureFlagStore


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "secret")
    jwt = JWTManager(app)

    swaggerui_blueprint = get_swaggerui_blueprint(
        "/docs", "/spec", config={"app_name": "Flags API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix="/docs")
    store = FeatureFlagStore()

    @app.post("/login")
    def login():
        data = request.get_json(force=True)
        if data.get("username") == "admin" and data.get("password") == "admin":
            token = create_access_token(identity="admin")
            return jsonify(access_token=token)
        return jsonify({"msg": "Bad credentials"}), 401

    @app.route("/flags", methods=["GET"])
    @jwt_required()
    def list_flags():
        flags = store.list_flags()
        return jsonify([flag.__dict__ for flag in flags])

    @app.route("/spec", methods=["GET"])
    def spec():
        """Return minimal OpenAPI spec."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Flags API", "version": "1.0"},
            "paths": {
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
    def delete_flag(name):
        store.delete_flag(name)
        return "", 204

    return app


def main():
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()

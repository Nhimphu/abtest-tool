"""Minimal Flask API exposing core analysis helpers."""

import os
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
from stats.ab_test import evaluate_abn_test


def create_app() -> Flask:
    app = Flask(__name__)
    swaggerui_blueprint = get_swaggerui_blueprint("/docs", "/spec", config={"app_name": "Analysis API"})
    app.register_blueprint(swaggerui_blueprint, url_prefix="/docs")

    @app.route('/abtest', methods=['POST'])
    def run_abtest():
        data = request.get_json(force=True)
        res = evaluate_abn_test(
            data['users_a'], data['conv_a'],
            data['users_b'], data['conv_b'],
            metrics=data.get('metrics', 1),
            alpha=data.get('alpha', 0.05),
        )
        return jsonify(res)

    @app.route('/spec', methods=['GET'])
    def spec():
        """Return minimal OpenAPI spec."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Analysis API", "version": "1.0"},
            "paths": {
                "/abtest": {
                    "post": {
                        "responses": {"200": {"description": "AB test result"}}
                    }
                }
            },
        }
        return jsonify(spec)

    return app


def main():
    app = create_app()
    port = int(os.environ.get("PORT", "5000"))
    app.run(port=port)


if __name__ == '__main__':
    main()


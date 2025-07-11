"""Minimal Flask API exposing core analysis helpers."""

import os
from flask import Flask, jsonify, request
from logic import evaluate_abn_test


def create_app() -> Flask:
    app = Flask(__name__)

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

    return app


def main():
    app = create_app()
    port = int(os.environ.get("PORT", "5000"))
    app.run(port=port)


if __name__ == '__main__':
    main()


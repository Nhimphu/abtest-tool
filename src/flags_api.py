from flask import Flask, jsonify, request
from flags import FeatureFlagStore


def create_app() -> Flask:
    app = Flask(__name__)
    store = FeatureFlagStore()

    @app.route('/flags', methods=['GET'])
    def list_flags():
        flags = store.list_flags()
        return jsonify([flag.__dict__ for flag in flags])

    @app.route('/flags', methods=['POST'])
    def create_flag():
        data = request.get_json(force=True)
        flag = store.create_flag(
            data['name'],
            enabled=data.get('enabled', False),
            rollout=data.get('rollout', 100.0),
        )
        return jsonify(flag.__dict__), 201

    @app.route('/flags/<name>', methods=['PUT'])
    def update_flag(name):
        data = request.get_json(force=True)
        flag = store.update_flag(
            name,
            enabled=data.get('enabled'),
            rollout=data.get('rollout'),
        )
        return jsonify(flag.__dict__)

    @app.route('/flags/<name>', methods=['DELETE'])
    def delete_flag(name):
        store.delete_flag(name)
        return '', 204

    return app


def main():
    app = create_app()
    app.run()


if __name__ == '__main__':
    main()

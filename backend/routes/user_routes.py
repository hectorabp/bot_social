from flask import Blueprint, request, jsonify
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.user_controller import UserController

Userbp = Blueprint('users', __name__, url_prefix='/users')
controller = UserController()


@Userbp.route('', methods=['POST'])
def create_user():
    payload = request.get_json()
    result = controller.create(payload)
    status = 201 if result.get('success') else 400
    return jsonify(result), status


@Userbp.route('', methods=['GET'])
def list_users():
    try:
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)
        result = controller.list_users(limit=limit, offset=offset)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@Userbp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    result = controller.get_user(user_id)
    status = 200 if result.get('success') else 404
    return jsonify(result), status


@Userbp.route('/by-email', methods=['GET'])
def get_user_by_email():
    correo = request.args.get('correo')
    result = controller.get_user_by_email(correo)
    status = 200 if result.get('success') else 404
    return jsonify(result), status


@Userbp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    payload = request.get_json()
    result = controller.update_user(user_id, payload)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@Userbp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    result = controller.delete_user(user_id)
    status = 200 if result.get('success') else 400
    return jsonify(result), status

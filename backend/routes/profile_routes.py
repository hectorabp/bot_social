from flask import Blueprint, request, jsonify
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.profile_controller import ProfileController

Profilebp = Blueprint('profiles', __name__, url_prefix='/profiles')
controller = ProfileController()


@Profilebp.route('', methods=['POST'])
def create_profile():
    payload = request.get_json()
    result = controller.create(payload)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@Profilebp.route('/bulk', methods=['POST'])
def create_bulk():
    payloads = request.get_json()
    transactional = request.args.get('transactional', 'true').lower() == 'true'
    result = controller.create_bulk(payloads, transactional=transactional)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@Profilebp.route('/from-template', methods=['POST'])
def create_from_template():
    payloads = request.get_json()
    template = payloads.get("template") 
    payload = payloads.get("payloads", [])
    transactional = request.args.get('transactional', 'true').lower() == 'true'
    result = controller.create_from_template(template, payload, transactional=transactional)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@Profilebp.route('/<int:profile_id>', methods=['GET'])
def get_profile(profile_id):
    result = controller.get_profile_with_relations(profile_id)
    status = 200 if result.get('success') else 404
    return jsonify(result), status


@Profilebp.route('/by-template/<int:template_id>', methods=['GET'])
def get_profiles_by_template(template_id):
    page = request.args.get('page')
    per_page = request.args.get('per_page')
    result = controller.get_profiles_by_template(template_id, page=page, per_page=per_page)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@Profilebp.route('', methods=['GET'])
def list_profiles():
    filters = {}
    allowed = ('id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero', 'id_plantilla')
    for key in allowed:
        val = request.args.get(key)
        if val is not None:
            filters[key] = val

    page = request.args.get('page')
    per_page = request.args.get('per_page')
    order_by = request.args.get('order_by')
    try:
        result = controller.get_profiles(filters=filters if filters else None, page=page, per_page=per_page, order_by=order_by)
        status = 200 if result.get('success') else 400
        return jsonify(result), status
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@Profilebp.route('/<int:profile_id>', methods=['DELETE'])
def delete_profile(profile_id):
    result = controller.delete_profile(profile_id)
    status = 200 if result.get('success') else 400
    return jsonify(result), status


@Profilebp.route('/by-relation/<relation>/<int:relation_id>', methods=['DELETE'])
def delete_profiles_by_relation(relation, relation_id):
    result = controller.delete_profiles_by_relation(relation, relation_id)
    status = 200 if result.get('success') else 400
    return jsonify(result), status

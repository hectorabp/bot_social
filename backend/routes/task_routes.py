from flask import Blueprint, request, jsonify
from pathlib import Path
import sys
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))
from controller.task_controller import TaskController

Taskbp = Blueprint('tasks', __name__, url_prefix='/tasks')
controller = TaskController()


@Taskbp.route('', methods=['POST'])
def create_task():
    """Crea una tarea única o múltiples tareas programadas."""
    payload = request.get_json()
    if not payload:
        return jsonify({"success": False, "error": "Payload requerido"}), 400

    task_type = payload.get('type', 'single')  # 'single' o 'multiple'

    if task_type == 'single':
        # Tarea única
        task_payload = payload.get('payload')
        task_name = payload.get('task_name', 'create_email_account_task')
        eta_str = payload.get('eta')
        countdown = payload.get('countdown')

        eta = None
        if eta_str:
            try:
                eta = datetime.fromisoformat(eta_str)
            except ValueError:
                return jsonify({"success": False, "error": "Formato de eta inválido (use ISO format)"}), 400

        result = controller.create_task(task_payload, task_name=task_name, eta=eta, countdown=countdown)
        status = 200 if result.get('success') else 400
        return jsonify(result), status

    elif task_type == 'multiple':
        # Tareas múltiples
        payloads = payload.get('payloads')
        start_time_str = payload.get('start_time')
        intervals = payload.get('intervals')
        task_name = payload.get('task_name', 'create_email_account_task')

        if not payloads or not start_time_str:
            return jsonify({"success": False, "error": "payloads y start_time son requeridos para tareas múltiples"}), 400

        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            return jsonify({"success": False, "error": "Formato de start_time inválido (use ISO format)"}), 400

        result = controller.schedule_multiple_tasks(payloads, start_time, intervals=intervals, task_name=task_name)
        status = 200 if result.get('success') else 400
        return jsonify(result), status

    else:
        return jsonify({"success": False, "error": "Tipo de tarea inválido (use 'single' o 'multiple')"}), 400


@Taskbp.route('', methods=['GET'])
def read_all_tasks():
    """Lee todas las tareas programadas."""
    result = controller.read_all_tasks()
    return jsonify({"success": True, "data": result}), 200


@Taskbp.route('/<task_id>', methods=['GET'])
def read_task(task_id):
    """Lee la información de una tarea por su ID."""
    result = controller.read_task(task_id)
    if result:
        return jsonify({"success": True, "data": result}), 200
    else:
        return jsonify({"success": False, "error": "Tarea no encontrada"}), 404


@Taskbp.route('/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Actualiza una tarea programada."""
    payload = request.get_json()
    if not payload:
        return jsonify({"success": False, "error": "Payload requerido"}), 400

    status = payload.get('status')
    observation = payload.get('observation')
    task_payload = payload.get('payload')

    success = controller.update_task(task_id, status=status, observation=observation, payload=task_payload)
    if success:
        return jsonify({"success": True, "message": "Tarea actualizada"}), 200
    else:
        return jsonify({"success": False, "error": "Error al actualizar tarea"}), 400


@Taskbp.route('/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Elimina una tarea programada."""
    success = controller.delete_task(task_id)
    if success:
        return jsonify({"success": True, "message": "Tarea eliminada"}), 200
    else:
        return jsonify({"success": False, "error": "Error al eliminar tarea"}), 400
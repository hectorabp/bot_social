import os
from celery import Celery
from celery.signals import task_success, task_failure, task_revoked
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.scheduled_tasks import TareasProgramadasModule

# Configuración mínima de Celery usando variables de entorno
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', BROKER_URL)

celery_app = Celery('scheduled_service', broker=BROKER_URL, backend=RESULT_BACKEND)

# Puedes agregar aquí configuración extra de Celery si lo deseas
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Instancia del módulo DB para signals
db_module = TareasProgramadasModule()

@task_success.connect
def handle_task_success(sender=None, **kwargs):
    """Actualiza la DB cuando una tarea se completa exitosamente."""
    task_id = sender.request.id
    try:
        db_module.update(task_id, status='SUCCESS', completed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        print(f"Error updating DB for task success {task_id}: {e}")

@task_failure.connect
def handle_task_failure(sender=None, **kwargs):
    """Actualiza la DB cuando una tarea falla."""
    task_id = sender.request.id
    try:
        db_module.update(task_id, status='FAILURE', completed_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    except Exception as e:
        print(f"Error updating DB for task failure {task_id}: {e}")

@task_revoked.connect
def handle_task_revoked(sender=None, **kwargs):
    """Actualiza la DB cuando una tarea es revocada."""
    task_id = sender.request.id
    try:
        db_module.update(task_id, status='REVOKED')
    except Exception as e:
        print(f"Error updating DB for task revoked {task_id}: {e}")

__all__ = ['celery_app']

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from .celery_app import celery_app

@celery_app.task(bind=True)
def create_email_account_task(self, payload: dict, host: str = 'localhost', port: int = 3001):
    """Tarea Celery para crear una cuenta de email usando EmailGeneratorController."""
    from controller.email_generator_controller import EmailGeneratorController
    controller = EmailGeneratorController(host=host, port=port)
    return controller.create_account(payload)
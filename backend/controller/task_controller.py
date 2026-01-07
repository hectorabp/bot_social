import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).resolve().parent.parent))

from scheduled_service.celery_app import celery_app
from modules.scheduled_tasks import TareasProgramadasModule
from scheduled_service import tasks as tasks_module


class TaskController:
    """Controlador para operaciones CRUD de tareas programadas con Celery.

    Este controlador maneja la creación, lectura, actualización y eliminación de tareas
    programadas que ejecutan la creación de cuentas de email. Utiliza Celery para la
    programación asíncrona y registra cada operación en la base de datos.
    """

    def __init__(self, host: str = 'localhost', port: int = 3001, logger=None):
        self.host = host
        self.port = port
        self.logger = logger
        self.db_module = TareasProgramadasModule()

    def schedule_celery_task(self, task_name: str, args: list, task_id: str, eta: Optional[datetime] = None, countdown: Optional[int] = None) -> Any:
        """Programa una tarea en Celery de manera dinámica.

        Args:
            task_name: Nombre de la función de tarea en tasks_module (ej. 'create_email_account_task').
            args: Lista de argumentos para la tarea.
            task_id: ID único de la tarea.
            eta: Fecha y hora exacta.
            countdown: Segundos de espera.

        Returns:
            El resultado de apply_async.
        """
        try:
            task_func = getattr(tasks_module, task_name)
            return task_func.apply_async(
                args=args,
                task_id=task_id,
                eta=eta,
                countdown=countdown
            )
        except AttributeError:
            raise ValueError(f"Task '{task_name}' not found in tasks module")
        except Exception as e:
            raise e

    def create_task(self, payload: Dict[str, Any], task_name: str = 'create_email_account_task', eta: Optional[datetime] = None, countdown: Optional[int] = None) -> Dict[str, Any]:
        """Crea una nueva tarea programada para ejecutar una tarea específica.

        Inserta la tarea en la base de datos con estado PENDING y la programa en Celery.

        Args:
            payload: Diccionario con los datos para la tarea.
            task_name: Nombre de la función de tarea en tasks_module (default: 'create_email_account_task').
            eta: Fecha y hora exacta para ejecutar la tarea (datetime).
            countdown: Segundos para esperar antes de ejecutar (int).

        Returns:
            Dict con 'success', 'task_id', 'error'.
        """
        try:
            # Generar task_id único
            task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

            # Insertar en DB
            self.db_module.create(task_id=task_id, status='PENDING', payload=str(payload))

            # Programar en Celery
            task = self.schedule_celery_task(
                task_name,
                [payload, self.host, self.port],
                task_id,
                eta,
                countdown
            )

            return {"success": True, "task_id": task_id, "error": None}
        except Exception as e:
            if self.logger:
                self.logger.error("Error creating task", exc_info=e)
            return {"success": False, "task_id": None, "error": str(e)}

    def read_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Lee la información de una tarea programada desde la base de datos.

        Args:
            task_id: ID de la tarea.

        Returns:
            Dict con la información de la tarea o None si no existe.
        """
        try:
            task = self.db_module.read_by_task_id(task_id)
            if task:
                return {
                    "id": task["id"],
                    "task_id": task["task_id"],
                    "status": task["status"],
                    "created_at": task["created_at"],
                    "updated_at": task["updated_at"],
                    "completed_at": task["completed_at"],
                    "observation": task["observation"],
                    "payload": task["payload"]
                }
            return None
        except Exception as e:
            if self.logger:
                self.logger.error("Error reading task", exc_info=e)
            return None

    def read_all_tasks(self) -> List[Dict[str, Any]]:
        """Lee todas las tareas programadas desde la base de datos.

        Returns:
            Lista de diccionarios con la información de todas las tareas.
        """
        try:
            tasks = self.db_module.read_all()
            return [
                {
                    "id": task["id"],
                    "task_id": task["task_id"],
                    "status": task["status"],
                    "created_at": task["created_at"],
                    "updated_at": task["updated_at"],
                    "completed_at": task["completed_at"],
                    "observation": task["observation"],
                    "payload": task["payload"]
                }
                for task in tasks
            ]
        except Exception as e:
            if self.logger:
                self.logger.error("Error reading all tasks", exc_info=e)
            return []

    def update_task(self, task_id: str, status: Optional[str] = None, observation: Optional[str] = None, payload: Optional[str] = None) -> bool:
        """Actualiza una tarea programada en la base de datos.

        Si el status se cambia a REVOKED, revoca la tarea en Celery.

        Args:
            task_id: ID de la tarea.
            status: Nuevo estado (PENDING, SUCCESS, FAILURE, REVOKED).
            observation: Observación adicional.
            payload: Nuevo payload.

        Returns:
            True si se actualizó correctamente, False en caso contrario.
        """
        try:
            # Primero, obtener el id de la DB
            task = self.db_module.read_by_task_id(task_id)
            if not task:
                return False

            db_id = task["id"]

            # Actualizar DB
            success = self.db_module.update(db_id, status=status, observation=observation, payload=payload)

            # Si se revoca, revocar en Celery
            if status == 'REVOKED':
                celery_app.control.revoke(task_id, terminate=True)

            return success
        except Exception as e:
            if self.logger:
                self.logger.error("Error updating task", exc_info=e)
            return False

    def delete_task(self, task_id: str) -> bool:
        """Elimina una tarea programada de la base de datos y revoca en Celery.

        Args:
            task_id: ID de la tarea.

        Returns:
            True si se eliminó correctamente, False en caso contrario.
        """
        try:
            # Obtener id de DB
            task = self.db_module.read_by_task_id(task_id)
            if not task:
                return False

            db_id = task["id"]

            # Revocar en Celery
            celery_app.control.revoke(task_id, terminate=True)

            # Eliminar de DB
            return self.db_module.delete(db_id)
        except Exception as e:
            if self.logger:
                self.logger.error("Error deleting task", exc_info=e)
            return False

    def schedule_multiple_tasks(
        self,
        payloads: List[Dict[str, Any]],
        start_time: datetime,
        intervals: Optional[List[int]] = None,
        task_name: str = 'create_email_account_task'
    ) -> Dict[str, Any]:
        """Programa múltiples tareas con intervalos acumulativos.

        Si intervals es None, todas las tareas se ejecutan al instante de start_time.
        Si intervals está presente, debe tener len(payloads) - 1 elementos, y los intervalos
        son acumulativos (cada tarea se ejecuta X segundos después de la anterior).

        Args:
            payloads: Lista de payloads para cada tarea.
            start_time: Fecha y hora de inicio (datetime).
            intervals: Lista opcional de intervalos en segundos (acumulativos).
            task_name: Nombre de la función de tarea en tasks_module.

        Returns:
            Dict con 'success', 'task_ids', 'error'.
        """
        try:
            current_time = datetime.now()
            if start_time < current_time:
                return {"success": False, "task_ids": [], "error": "La fecha de inicio (start_time) no puede ser en el pasado."}

            if intervals is not None and len(intervals) != len(payloads) - 1:
                return {"success": False, "task_ids": [], "error": f"intervals debe tener {len(payloads) - 1} elementos, pero tiene {len(intervals)}."}

            task_ids = []
            accumulated_seconds = 0

            for i, payload in enumerate(payloads):
                if intervals is not None and i > 0:
                    accumulated_seconds += intervals[i - 1]

                eta = start_time + timedelta(seconds=accumulated_seconds)

                result = self.create_task(payload, task_name=task_name, eta=eta)
                if result["success"]:
                    task_ids.append(result["task_id"])
                else:
                    # Revocar tareas anteriores en caso de error
                    for tid in task_ids:
                        self.delete_task(tid)
                    return {"success": False, "task_ids": [], "error": f"Fallo al programar tarea {i}: {result['error']}"}

            return {"success": True, "task_ids": task_ids, "error": None}
        except Exception as e:
            if self.logger:
                self.logger.error("Error scheduling multiple tasks", exc_info=e)
            return {"success": False, "task_ids": [], "error": str(e)}

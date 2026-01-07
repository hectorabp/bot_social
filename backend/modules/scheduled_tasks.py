import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class TareasProgramadasModule:
    """Módulo para la tabla `tareas_programadas`."""

    def __init__(self):
        self.db = Database()
        self.table = 'tareas_programadas'

    def create(self, task_id: str, status: str = 'PENDING', observation: str = None, payload: str = None) -> int:
        if not task_id:
            raise ValueError("El campo 'task_id' es obligatorio")
        query = f"INSERT INTO {self.table} (task_id, status, observation, payload) VALUES (%s, %s, %s, %s)"
        return self.db.insert_query(query, (task_id, status, observation, payload))

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, task_id, status, created_at, updated_at, completed_at, observation, payload FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def read_by_task_id(self, task_id: str) -> dict | None:
        query = f"SELECT id, task_id, status, created_at, updated_at, completed_at, observation, payload FROM {self.table} WHERE task_id = %s"
        results = self.db.query(query, (task_id,))
        return results[0] if results else None

    def read_all(self) -> list:
        query = f"SELECT id, task_id, status, created_at, updated_at, completed_at, observation, payload FROM {self.table}"
        return self.db.query(query)

    def update(self, id: int, status: str = None, completed_at: str = None, observation: str = None, payload: str = None) -> bool:
        fields = []
        params = []
        if status is not None:
            fields.append('status = %s')
            params.append(status)
        if completed_at is not None:
            fields.append('completed_at = %s')
            params.append(completed_at)
        if observation is not None:
            fields.append('observation = %s')
            params.append(observation)
        if payload is not None:
            fields.append('payload = %s')
            params.append(payload)
        if not fields:
            return False
        params.append(id)
        set_clause = ', '.join(fields)
        query = f"UPDATE {self.table} SET {set_clause} WHERE id = %s"
        rowcount = self.db.query(query, tuple(params))
        return bool(rowcount)

    def delete(self, id: int) -> bool:
        query = f"DELETE FROM {self.table} WHERE id = %s"
        rowcount = self.db.query(query, (id,))
        return bool(rowcount)
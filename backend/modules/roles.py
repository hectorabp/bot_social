import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class RolesModule:
    """Módulo para la tabla `roles`.

    Todos los docstrings y comentarios están en español. Los métodos públicos
    siguen la convención: create, read, update, delete.
    """

    def __init__(self):
        self.db = Database()
        self.table = 'roles'

    def create(self, rol: str) -> int:
        if not rol:
            raise ValueError("El campo 'rol' es obligatorio")
        query = f"INSERT INTO {self.table} (rol) VALUES (%s)"
        return self.db.insert_query(query, (rol,))

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, rol FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def update(self, id: int, rol: str = None) -> bool:
        fields = []
        params = []
        if rol is not None:
            fields.append('rol = %s')
            params.append(rol)
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

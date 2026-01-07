import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class TemplateProfilesModule:
    """Módulo para la tabla `plantilla_perfiles`.

    Proporciona operaciones CRUD básicas: create, read, update, delete.
    """

    def __init__(self):
        self.db = Database()
        self.table = 'plantilla_perfiles'

    def create(self, nombre_plantilla: str) -> int:
        if not nombre_plantilla:
            raise ValueError("El campo 'nombre_plantilla' es obligatorio")
        query = f"INSERT INTO {self.table} (nombre_plantilla) VALUES (%s)"
        return self.db.insert_query(query, (nombre_plantilla,))

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, nombre_plantilla FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def update(self, id: int, nombre_plantilla: str = None) -> bool:
        fields = []
        params = []
        if nombre_plantilla is not None:
            fields.append('nombre_plantilla = %s')
            params.append(nombre_plantilla)
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

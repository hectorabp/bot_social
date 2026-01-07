import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class CitiesModule:
    """Módulo para la tabla `ciudades`."""

    def __init__(self):
        self.db = Database()
        self.table = 'ciudades'

    def create(self, ciudad: str, id_pais: int) -> int:
        if not ciudad:
            raise ValueError("El campo 'ciudad' es obligatorio")
        if id_pais is None:
            raise ValueError("El campo 'id_pais' es obligatorio")
        query = f"INSERT INTO {self.table} (ciudad, id_pais) VALUES (%s, %s)"
        return self.db.insert_query(query, (ciudad, id_pais))

    def list_all(self) -> list:
        query = f"SELECT id, ciudad, id_pais FROM {self.table} ORDER BY ciudad"
        return self.db.query(query) or []

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, ciudad, id_pais FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def update(self, id: int, ciudad: str = None, id_pais: int = None) -> bool:
        fields = []
        params = []
        if ciudad is not None:
            fields.append('ciudad = %s')
            params.append(ciudad)
        if id_pais is not None:
            fields.append('id_pais = %s')
            params.append(id_pais)
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

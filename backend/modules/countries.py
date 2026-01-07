import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class CountriesModule:
    """Módulo para la tabla `paises`."""

    def __init__(self):
        self.db = Database()
        self.table = 'paises'

    def create(self, pais: str) -> int:
        if not pais:
            raise ValueError("El campo 'pais' es obligatorio")
        query = f"INSERT INTO {self.table} (pais) VALUES (%s)"
        return self.db.insert_query(query, (pais,))

    def list_all(self) -> list:
        query = f"SELECT id, pais FROM {self.table} ORDER BY pais"
        return self.db.query(query) or []

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, pais FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def update(self, id: int, pais: str = None) -> bool:
        fields = []
        params = []
        if pais is not None:
            fields.append('pais = %s')
            params.append(pais)
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

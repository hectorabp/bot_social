import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class GendersModule:
    """Módulo para la tabla `generos`."""

    def __init__(self):
        self.db = Database()
        self.table = 'generos'

    def create(self, genero: str) -> int:
        if not genero:
            raise ValueError("El campo 'genero' es obligatorio")
        query = f"INSERT INTO {self.table} (genero) VALUES (%s)"
        return self.db.insert_query(query, (genero,))

    def list_all(self) -> list:
        query = f"SELECT id, genero FROM {self.table} ORDER BY genero"
        return self.db.query(query) or []

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, genero FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def update(self, id: int, genero: str = None) -> bool:
        fields = []
        params = []
        if genero is not None:
            fields.append('genero = %s')
            params.append(genero)
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

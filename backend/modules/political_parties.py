import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class PoliticalPartiesModule:
    """Módulo para la tabla `partidos_politicos`."""

    def __init__(self):
        self.db = Database()
        self.table = 'partidos_politicos'

    def create(self, partido_politico: str) -> int:
        if not partido_politico:
            raise ValueError("El campo 'partido_politico' es obligatorio")
        query = f"INSERT INTO {self.table} (partido_politico) VALUES (%s)"
        return self.db.insert_query(query, (partido_politico,))

    def list_all(self) -> list:
        query = f"SELECT id, partido_politico FROM {self.table} ORDER BY partido_politico"
        return self.db.query(query) or []

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, partido_politico FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def update(self, id: int, partido_politico: str = None) -> bool:
        fields = []
        params = []
        if partido_politico is not None:
            fields.append('partido_politico = %s')
            params.append(partido_politico)
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

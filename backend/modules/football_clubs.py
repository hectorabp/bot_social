import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class FootballClubsModule:
    """Módulo para la tabla `clubes_futbol`."""

    def __init__(self):
        self.db = Database()
        self.table = 'clubes_futbol'

    def create(self, club_futbol: str) -> int:
        if not club_futbol:
            raise ValueError("El campo 'club_futbol' es obligatorio")
        query = f"INSERT INTO {self.table} (club_futbol) VALUES (%s)"
        return self.db.insert_query(query, (club_futbol,))

    def list_all(self) -> list:
        query = f"SELECT id, club_futbol FROM {self.table} ORDER BY club_futbol"
        return self.db.query(query) or []

    def read(self, id: int) -> dict | None:
        query = f"SELECT id, club_futbol FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def update(self, id: int, club_futbol: str = None) -> bool:
        fields = []
        params = []
        if club_futbol is not None:
            fields.append('club_futbol = %s')
            params.append(club_futbol)
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

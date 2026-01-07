import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class TemplateProfileRecordsModule:
    """Módulo para la tabla `registro_plantilla_perfiles`.

    Permite asociar valores por defecto (FKs) a una plantilla de perfiles.
    """

    def __init__(self):
        self.db = Database()
        self.table = 'registro_plantilla_perfiles'

    def create(self, id_plantilla: int, id_pais: int | None = None, id_ciudad: int | None = None, id_barrio: int | None = None, id_partido_politico: int | None = None, id_club_futbol: int | None = None, id_ideologia: int | None = None, id_estilo_musica: int | None = None, id_genero: int | None = None) -> int:
        if id_plantilla is None:
            raise ValueError("El campo 'id_plantilla' es obligatorio")
        query = f"INSERT INTO {self.table} (id_plantilla, id_pais, id_ciudad, id_barrio, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (id_plantilla, id_pais, id_ciudad, id_barrio, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero)
        return self.db.insert_query(query, params)

    def read(self, id: int) -> dict | None:
        query = f"SELECT * FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def list_by_template(self, id_plantilla: int) -> list:
        query = f"SELECT * FROM {self.table} WHERE id_plantilla = %s"
        results = self.db.query(query, (id_plantilla,))
        return results or []

    def update(self, id: int, **kwargs) -> bool:
        allowed = ['id_plantilla', 'id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero']
        fields = []
        params = []
        for k, v in kwargs.items():
            if k in allowed:
                fields.append(f"{k} = %s")
                params.append(v)
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

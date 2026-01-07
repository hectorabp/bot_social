import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database


class ProfilesModule:
    """Módulo para la tabla `perfiles`.

    Debido a la gran cantidad de campos, el método create expone los campos
    más importantes y acepta otros como opcionales.
    """

    def __init__(self):
        self.db = Database()
        self.table = 'perfiles'

    def create(self, nombre: str, apellido: str, correo: str, fecha_nacimiento: str | None = None, telefono: str | None = None, id_pais: int | None = None, id_ciudad: int | None = None, id_barrio: int | None = None, id_partido_politico: int | None = None, id_club_futbol: int | None = None, id_ideologia: int | None = None, id_estilo_musica: int | None = None, id_genero: int | None = None, id_plantilla: int | None = None, cuenta_FB: str | None = None, cuenta_IG: str | None = None, cuenta_TW: str | None = None, cuenta_TK: str | None = None, password_FB: str | None = None, password_IG: str | None = None, password_TW: str | None = None, password_TK: str | None = None) -> int:
        if not all([nombre, apellido, correo]):
            raise ValueError("Los campos 'nombre', 'apellido' y 'correo' son obligatorios")
        
        query = f"""INSERT INTO {self.table} 
        (nombre, apellido, correo, fecha_nacimiento, telefono, id_pais, id_ciudad, id_barrio, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero, id_plantilla,
        cuenta_FB, cuenta_IG, cuenta_TW, cuenta_TK, password_FB, password_IG, password_TW, password_TK) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        params = (nombre, apellido, correo, fecha_nacimiento, telefono, id_pais, id_ciudad, id_barrio, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero, id_plantilla,
                  cuenta_FB, cuenta_IG, cuenta_TW, cuenta_TK, password_FB, password_IG, password_TW, password_TK)
        return self.db.insert_query(query, params)

    def bulk_insert(self, payloads: list, transactional: bool = True) -> dict:
        """Inserta múltiples perfiles de forma masiva.

        payloads: lista de diccionarios con los mismos campos aceptados por create().
        Si transactional=True intentará insertar en una única transacción.

        Retorna: {"success": bool, "inserted_ids": list, "errors": list}
        """
        if not isinstance(payloads, list):
            return {"success": False, "inserted_ids": [], "errors": ["payloads must be a list"]}

        inserted_ids = []
        errors = []

        if transactional:
            try:
                self.db.start_transaction()
                for idx, payload in enumerate(payloads):
                    try:
                        nombre = payload.get('nombre').strip()
                        apellido = payload.get('apellido').strip()
                        correo = payload.get('correo').strip().lower()
                        fecha_nacimiento = payload.get('fecha_nacimiento')
                        telefono = payload.get('telefono')
                        id_pais = payload.get('id_pais')
                        id_ciudad = payload.get('id_ciudad')
                        id_barrio = payload.get('id_barrio')
                        id_partido_politico = payload.get('id_partido_politico')
                        id_club_futbol = payload.get('id_club_futbol')
                        id_ideologia = payload.get('id_ideologia')
                        id_estilo_musica = payload.get('id_estilo_musica')
                        id_genero = payload.get('id_genero')
                        id_plantilla = payload.get('id_plantilla')
                        query = f"INSERT INTO {self.table} (nombre, apellido, correo, fecha_nacimiento, telefono, id_pais, id_ciudad, id_barrio, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero, id_plantilla) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                        params = (nombre, apellido, correo, fecha_nacimiento, telefono, id_pais, id_ciudad, id_barrio, id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero, id_plantilla)
                        self.db.cursor.execute(query, params)
                        inserted_ids.append(self.db.cursor.lastrowid)
                    except Exception as e:
                        errors.append({"index": idx, "error": str(e)})
                        raise
                self.db.commit()
                return {"success": True, "inserted_ids": inserted_ids, "errors": []}
            except Exception as e:
                try:
                    self.db.rollback()
                except Exception:
                    pass
                return {"success": False, "inserted_ids": inserted_ids, "errors": errors or [str(e)], "error": str(e)}
            finally:
                try:
                    self.db.close()
                except Exception:
                    pass
        else:
            for idx, payload in enumerate(payloads):
                try:
                    nombre = payload.get('nombre').strip()
                    apellido = payload.get('apellido').strip()
                    correo = payload.get('correo').strip().lower()
                    telefono = payload.get('telefono')
                    id_pais = payload.get('id_pais')
                    id_ciudad = payload.get('id_ciudad')
                    id_barrio = payload.get('id_barrio')
                    id_plantilla = payload.get('id_plantilla')
                    query = f"INSERT INTO {self.table} (nombre, apellido, correo, telefono, id_pais, id_ciudad, id_barrio, id_plantilla) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    params = (nombre, apellido, correo, telefono, id_pais, id_ciudad, id_barrio, id_plantilla)
                    new_id = self.db.insert_query(query, params)
                    inserted_ids.append(new_id)
                except Exception as e:
                    errors.append({"index": idx, "error": str(e)})
            return {"success": len(errors) == 0, "inserted_ids": inserted_ids, "errors": errors}

    def read(self, id: int) -> dict | None:
        query = f"SELECT * FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (id,))
        return results[0] if results else None

    def bulk_read_with_relations(self, ids: list, page: int | None = None, per_page: int | None = None) -> list[dict]:
        """Obtiene varios perfiles por sus ids y resuelve todas las relaciones

        - ids: lista de ids (enteros o strings convertibles a enteros)
        - Retorna: lista de diccionarios, cada uno con los campos de `perfiles`
          y campos adicionales provenientes de las tablas relacionadas
          (pais, ciudad, barrio, partido_politico, club_futbol, ideologia,
           estilo_musica, genero, nombre_plantilla).

        El método ejecuta una única consulta con LEFT JOIN para evitar
        múltiples roundtrips por cada perfil.
        """
        if not isinstance(ids, list):
            raise ValueError("ids must be a list of integers")

        # Convertir y filtrar ids válidos
        clean_ids = []
        for v in ids:
            try:
                clean_ids.append(int(v))
            except Exception:
                continue

        if not clean_ids:
            return []

        placeholders = ','.join(['%s'] * len(clean_ids))

        # Pagination handling
        limit_clause = ''
        extra_params = []
        if page is not None and per_page is not None:
            try:
                p = int(page)
                pp = int(per_page)
                if p < 1 or pp < 1:
                    raise ValueError()
            except Exception:
                raise ValueError('page and per_page must be positive integers')
            offset = (p - 1) * pp
            limit_clause = ' LIMIT %s OFFSET %s '
            extra_params = [pp, offset]

        query = (
            f"SELECT p.*, pa.pais AS pais, ci.ciudad AS ciudad, ba.barrio AS barrio,"
            f"               pp.partido_politico AS partido_politico, cf.club_futbol AS club_futbol,"
            f"               idd.ideologia AS ideologia, em.estilo_musica AS estilo_musica,"
            f"               ge.genero AS genero, tpl.nombre_plantilla AS nombre_plantilla"
            f" FROM {self.table} p"
            f" LEFT JOIN paises pa ON p.id_pais = pa.id"
            f" LEFT JOIN ciudades ci ON p.id_ciudad = ci.id"
            f" LEFT JOIN barrios ba ON p.id_barrio = ba.id"
            f" LEFT JOIN partidos_politicos pp ON p.id_partido_politico = pp.id"
            f" LEFT JOIN clubes_futbol cf ON p.id_club_futbol = cf.id"
            f" LEFT JOIN ideologia idd ON p.id_ideologia = idd.id"
            f" LEFT JOIN estilos_musicas em ON p.id_estilo_musica = em.id"
            f" LEFT JOIN generos ge ON p.id_genero = ge.id"
            f" LEFT JOIN plantilla_perfiles tpl ON p.id_plantilla = tpl.id"
            f" WHERE p.id IN ({placeholders})"
            f" ORDER BY p.id"
        )

        # Append limit/offset if requested
        if limit_clause:
            query = query + limit_clause

        params = tuple(clean_ids) + tuple(extra_params)
        results = self.db.query(query, params)
        return results

    def list_ids_by_template(self, template_id: int) -> list[int]:
        """Devuelve la lista de ids de perfiles asociados a una plantilla."""
        try:
            tid = int(template_id)
        except Exception:
            raise ValueError("template_id must be an integer")
        query = f"SELECT id FROM {self.table} WHERE id_plantilla = %s ORDER BY id"
        results = self.db.query(query, (tid,))
        return [r['id'] for r in results] if results else []

    def list_with_relations(self, filters: dict | None = None, page: int | None = None, per_page: int | None = None, order_by: str | None = None) -> dict:
        """Lista perfiles con todas las relaciones y soporte de filtros y paginación.

        - filters: dict con claves de FK posibles: id_pais, id_ciudad, id_barrio,
          id_partido_politico, id_club_futbol, id_ideologia, id_estilo_musica, id_genero, id_plantilla
          Los valores pueden ser int o lista de ints.
        - page, per_page: si se suministran ambos, se aplica LIMIT/OFFSET.
        - order_by: columna de orden (solo se permiten columnas seguras).

        Retorna: { success: bool, total: int, profiles: list[dict], page: int|None, per_page: int|None }
        """
        allowed_filters = {'id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero', 'id_plantilla'}
        social_filters = {'has_FB': 'cuenta_FB', 'has_IG': 'cuenta_IG', 'has_TW': 'cuenta_TW', 'has_TK': 'cuenta_TK'}
        where_clauses = []
        params = []

        if filters:
            if not isinstance(filters, dict):
                raise ValueError('filters must be a dict')
            for k, v in filters.items():
                if k in social_filters:
                    if v: # If true/truthy
                        col = social_filters[k]
                        where_clauses.append(f"(p.{col} IS NOT NULL AND p.{col} <> '')")
                    continue

                if k not in allowed_filters:
                    continue
                if v is None:
                    where_clauses.append(f"p.{k} IS NULL")
                    continue
                # allow list or single value
                if isinstance(v, (list, tuple)):
                    vals = []
                    for x in v:
                        try:
                            vals.append(int(x))
                        except Exception:
                            continue
                    if not vals:
                        continue
                    placeholders = ','.join(['%s'] * len(vals))
                    where_clauses.append(f"p.{k} IN ({placeholders})")
                    params.extend(vals)
                else:
                    try:
                        iv = int(v)
                    except Exception:
                        continue
                    where_clauses.append(f"p.{k} = %s")
                    params.append(iv)

        # Order by protection
        allowed_order = {'p.id', 'p.nombre', 'p.apellido', 'p.correo'}
        order_clause = 'p.id'
        if order_by:
            if order_by in allowed_order:
                order_clause = order_by
            else:
                raise ValueError('order_by not allowed')

        # Pagination validation
        limit_clause = ''
        extra_params = []
        if (page is None) ^ (per_page is None):
            raise ValueError('Both page and per_page must be provided together')
        if page is not None and per_page is not None:
            try:
                p = int(page)
                pp = int(per_page)
                if p < 1 or pp < 1:
                    raise ValueError()
            except Exception:
                raise ValueError('page and per_page must be positive integers')
            offset = (p - 1) * pp
            limit_clause = ' LIMIT %s OFFSET %s '
            extra_params = [pp, offset]

        where_sql = (' AND '.join(where_clauses)) if where_clauses else '1'

        # Use COUNT(*) OVER() to include total in the result (MySQL 8+)
        query = (
            f"SELECT p.*, pa.pais AS pais, ci.ciudad AS ciudad, ba.barrio AS barrio,"
            f" pp.partido_politico AS partido_politico, cf.club_futbol AS club_futbol,"
            f" idd.ideologia AS ideologia, em.estilo_musica AS estilo_musica,"
            f" ge.genero AS genero, tpl.nombre_plantilla AS nombre_plantilla,"
            f" COUNT(*) OVER() AS total_count"
            f" FROM {self.table} p"
            f" LEFT JOIN paises pa ON p.id_pais = pa.id"
            f" LEFT JOIN ciudades ci ON p.id_ciudad = ci.id"
            f" LEFT JOIN barrios ba ON p.id_barrio = ba.id"
            f" LEFT JOIN partidos_politicos pp ON p.id_partido_politico = pp.id"
            f" LEFT JOIN clubes_futbol cf ON p.id_club_futbol = cf.id"
            f" LEFT JOIN ideologia idd ON p.id_ideologia = idd.id"
            f" LEFT JOIN estilos_musicas em ON p.id_estilo_musica = em.id"
            f" LEFT JOIN generos ge ON p.id_genero = ge.id"
            f" LEFT JOIN plantilla_perfiles tpl ON p.id_plantilla = tpl.id"
            f" WHERE {where_sql}"
            f" ORDER BY {order_clause}"
        )

        if limit_clause:
            query = query + limit_clause

        final_params = tuple(params) + tuple(extra_params)
        results = self.db.query(query, final_params)

        total = 0
        if results:
            # total_count is returned per-row by COUNT(*) OVER()
            total = int(results[0].get('total_count', 0)) if results[0].get('total_count') is not None else 0

        return {"success": True, "total": total, "profiles": results, "page": page, "per_page": per_page}

    def update(self, id: int, **kwargs) -> bool:
        allowed = ['nombre', 'apellido', 'correo', 'telefono', 'cuenta_FB', 'cuenta_IG', 'cuenta_TW', 'cuenta_TK', 'password_FB', 'password_IG', 'password_TW', 'password_TK', 'id_pais', 'id_ciudad', 'id_barrio', 'calle', 'referencia_direccion', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero', 'id_plantilla']
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

    def delete_by_relation(self, field: str, relation_id: int) -> int:
        """Elimina perfiles donde `field` = relation_id.

        field debe ser una columna FK permitida para evitar inyección SQL.
        Retorna el número de filas eliminadas.
        """
        allowed = {'id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero', 'id_plantilla'}
        if field not in allowed:
            raise ValueError('field not allowed')
        try:
            rid = int(relation_id)
        except Exception:
            raise ValueError('relation_id must be an integer')

        query = f"DELETE FROM {self.table} WHERE {field} = %s"
        # Using db.query which returns affected rows for DELETE
        rowcount = self.db.query(query, (rid,))
        return int(rowcount) if rowcount is not None else 0

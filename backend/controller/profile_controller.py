import sys
from pathlib import Path
import re
import math
import random
import string

sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.profiles import ProfilesModule
from modules.template_profiles import TemplateProfilesModule
from modules.template_profile_records import TemplateProfileRecordsModule
from modules.countries import CountriesModule
from modules.cities import CitiesModule
from modules.neighborhoods import NeighborhoodsModule
from modules.political_parties import PoliticalPartiesModule
from modules.football_clubs import FootballClubsModule
from modules.ideologies import IdeologiesModule
from modules.music_styles import MusicStylesModule
from modules.genders import GendersModule


class ProfileController:
    """Controlador para operaciones sobre `perfiles`.

    Documentación en español. El controlador es independiente de frameworks
    web; devuelve diccionarios simples que el adaptador HTTP puede convertir
    en respuestas JSON.
    """

    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self):
        self.module = ProfilesModule()
        self.template_profile = TemplateProfilesModule()
        self.template_profile_records_module = TemplateProfileRecordsModule()
        # Modules to resolve foreign-key relations
        self.countries = CountriesModule()
        self.cities = CitiesModule()
        self.neighborhoods = NeighborhoodsModule()
        self.political_parties = PoliticalPartiesModule()
        self.football_clubs = FootballClubsModule()
        self.ideologies = IdeologiesModule()
        self.music_styles = MusicStylesModule()
        self.genders = GendersModule()

    def validate_payload(self, payload: dict) -> tuple[bool, list]:
        """Valida los campos esenciales del payload.

        Retorna (is_valid, errors_list).
        """
        errors = []
        if not isinstance(payload, dict):
            return False, ["Payload must be a dict"]

        nombre = payload.get('nombre')
        apellido = payload.get('apellido')
        correo = payload.get('correo')
        fecha_nacimiento = payload.get('fecha_nacimiento')

        if not nombre or not isinstance(nombre, str) or not nombre.strip():
            errors.append("'nombre' is required and must be a non-empty string")
        if not apellido or not isinstance(apellido, str) or not apellido.strip():
            errors.append("'apellido' is required and must be a non-empty string")
        if not correo or not isinstance(correo, str) or not correo.strip():
            errors.append("'correo' is required and must be a non-empty string")
        if not fecha_nacimiento or not isinstance(fecha_nacimiento, str) or not fecha_nacimiento.strip():
            errors.append("'fecha_nacimiento' is required and must be a non-empty string")
        else:
            correo_norm = correo.strip().lower()
            if not self.EMAIL_RE.match(correo_norm):
                errors.append("'correo' has invalid format")

        # Validate optional foreign keys if present
        for fk in ('id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero', 'id_plantilla'):
            if fk in payload and payload[fk] is not None:
                try:
                    int(payload[fk])
                except Exception:
                    errors.append(f"'{fk}' must be an integer if provided")

        return (len(errors) == 0), errors

    def create(self, payload: dict) -> dict:
        """Crea un perfil a partir del payload.

        Retorna dict con keys: success (bool), id (int|None), error (str|None), details (optional)
        """
        # Auto-generate email if missing
        if not payload.get('correo') or not str(payload.get('correo')).strip():
            nombre = payload.get('nombre', '')
            apellido = payload.get('apellido', '')
            if nombre and apellido:
                # Sanitize
                n = re.sub(r'[^a-zA-Z]', '', str(nombre)).lower()
                a = re.sub(r'[^a-zA-Z]', '', str(apellido)).lower()
                
                # 3 random letters
                letters = ''.join(random.choices(string.ascii_lowercase, k=3))
                # 2 random numbers
                numbers = ''.join(random.choices(string.digits, k=2))
                
                payload['correo'] = f"{n}{a}{letters}{numbers}@cabichui.com"

        is_valid, errors = self.validate_payload(payload)
        if not is_valid:
            return {"success": False, "id": None, "error": "Validation failed", "details": errors}

        # Prepare parameters expected by ProfilesModule.create
        nombre = payload.get('nombre').strip()
        apellido = payload.get('apellido').strip()
        correo = payload.get('correo').strip().lower()
        fecha_nacimiento = payload.get('fecha_nacimiento')
        telefono = payload.get('telefono')
        
        # Extract FKs
        id_pais = payload.get('id_pais')
        id_ciudad = payload.get('id_ciudad')
        id_barrio = payload.get('id_barrio')
        id_partido_politico = payload.get('id_partido_politico')
        id_club_futbol = payload.get('id_club_futbol')
        id_ideologia = payload.get('id_ideologia')
        id_estilo_musica = payload.get('id_estilo_musica')
        id_genero = payload.get('id_genero')
        id_plantilla = payload.get('id_plantilla')

        # Helper to ensure int or None
        def to_int_or_none(val):
            if val is None or val == '':
                return None
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return None

        id_pais = to_int_or_none(id_pais)
        id_ciudad = to_int_or_none(id_ciudad)
        id_barrio = to_int_or_none(id_barrio)
        id_partido_politico = to_int_or_none(id_partido_politico)
        id_club_futbol = to_int_or_none(id_club_futbol)
        id_ideologia = to_int_or_none(id_ideologia)
        id_estilo_musica = to_int_or_none(id_estilo_musica)
        id_genero = to_int_or_none(id_genero)
        id_plantilla = to_int_or_none(id_plantilla)

        # Campos de redes sociales (buscamos tanto la clave original como en minúsculas por si viene del CSV)
        cuenta_FB = payload.get('cuenta_FB') or payload.get('cuenta_fb')
        cuenta_IG = payload.get('cuenta_IG') or payload.get('cuenta_ig')
        cuenta_TW = payload.get('cuenta_TW') or payload.get('cuenta_tw')
        cuenta_TK = payload.get('cuenta_TK') or payload.get('cuenta_tk')
        password_FB = payload.get('password_FB') or payload.get('password_fb')
        password_IG = payload.get('password_IG') or payload.get('password_ig')
        password_TW = payload.get('password_TW') or payload.get('password_tw')
        password_TK = payload.get('password_TK') or payload.get('password_tk')

        try:
            new_id = self.module.create(
                nombre=nombre, 
                apellido=apellido, 
                correo=correo, 
                fecha_nacimiento=fecha_nacimiento, 
                telefono=telefono, 
                id_pais=id_pais, 
                id_ciudad=id_ciudad, 
                id_barrio=id_barrio, 
                id_partido_politico=id_partido_politico,
                id_club_futbol=id_club_futbol,
                id_ideologia=id_ideologia,
                id_estilo_musica=id_estilo_musica,
                id_genero=id_genero,
                id_plantilla=id_plantilla,
                cuenta_FB=cuenta_FB,
                cuenta_IG=cuenta_IG,
                cuenta_TW=cuenta_TW,
                cuenta_TK=cuenta_TK,
                password_FB=password_FB,
                password_IG=password_IG,
                password_TW=password_TW,
                password_TK=password_TK
            )
            return {"success": True, "id": new_id, "error": None}
        except Exception as e:
            return {"success": False, "id": None, "error": str(e)}

    def create_bulk(self, payloads: list, transactional: bool = True) -> dict:
        """Inserta múltiples perfiles.

        Si transactional=True intentará insertar en una única transacción.
        Devuelve un resumen con ids insertados y errores por índice.

        Formato de `payloads`:
        - Debe ser una lista de diccionarios.
        - Cada diccionario representa un perfil y debe contener al menos:
            - 'nombre' (str) obligatorio
            - 'apellido' (str) obligatorio
            - 'correo' (str) obligatorio, formato email
        - Campos opcionales admitidos:
            - 'telefono' (str)
            - 'id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero' (enteros o strings convertibles a enteros)
        - Ejemplo:
            [
                {'nombre': 'Ana', 'apellido': 'Perez', 'correo': 'ana@example.com', 'telefono': '123', 'id_pais': 1},
                {'nombre': 'Luis', 'apellido': 'Gomez', 'correo': 'luis@example.com'}
            ]
        """
        try:
            if not isinstance(payloads, list):
                return {"success": False, "error": "payloads must be a list"}

            inserted_ids = []
            errors = []

            if transactional:
                # Delegate bulk insertion to module to avoid SQL in controller
                # Module will manage transactions when transactional=True
                # Validate payloads first to provide early feedback
                for idx, payload in enumerate(payloads):
                    is_valid, val_errors = self.validate_payload(payload)
                    if not is_valid:
                        errors.append({"index": idx, "error": "validation", "details": val_errors})
                        # abort early
                        return {"success": False, "inserted_ids": [], "errors": errors}

                return self.module.bulk_insert(payloads, transactional=transactional)
            else:
                # Delegate non-transactional bulk insert to module as well
                # Validation is performed inside create() path, but we can pre-validate here
                for idx, payload in enumerate(payloads):
                    is_valid, val_errors = self.validate_payload(payload)
                    if not is_valid:
                        errors.append({"index": idx, "error": "validation", "details": val_errors})
                if errors:
                    return {"success": False, "inserted_ids": [], "errors": errors}
                return self.module.bulk_insert(payloads, transactional=False)
        except Exception as e:
            print(f"create_bulk error: {e}")
            return {"success": False, "inserted_ids": [], "error": str(e)}

    def create_from_template(self, template: list, payloads: list, transactional: bool = True) -> dict:
        """Crea perfiles a partir de una plantilla y una lista de payloads base.

        - Se obtienen los registros asociados a la plantilla (cada registro aporta
          valores por defecto para campos FK).
        - Se construye el producto cartesiano entre `payloads` y los registros de
          la plantilla: para cada payload y cada registro se genera un payload
          final que combina los valores (los campos del registro sobrescriben
          los campos FK del payload si existen).
        - Se reutiliza `create_bulk` para realizar la inserción masiva.

        Retorna el mismo esquema que `create_bulk`.

        Formato de `payloads` (payloads base):
        - Debe ser una lista de diccionarios.
        - Cada diccionario representa un perfil base y debe contener al menos:
            - 'nombre' (str) obligatorio
            - 'apellido' (str) obligatorio
            - 'correo' (str) obligatorio, formato email
        - Campos opcionales admitidos (además de los obligatorios):
            - 'telefono' (str)
            - 'id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero'
              (enteros o strings convertibles a enteros). Los valores de los registros de la plantilla
              sobrescribirán estos campos FK si están presentes en el registro de la plantilla.
        - Ejemplo de payloads base:
            [
                {'nombre': 'Ana', 'apellido': 'Perez', 'correo': 'ana@example.com'},
                {'nombre': 'Luis', 'apellido': 'Gomez', 'correo': 'luis@example.com', 'telefono': '123'}
            ]
        """
        try:
            if not isinstance(payloads, list):
                return {"success": False, "error": "payloads must be a list"}
            template_id = template.get("template_id")
            if self.template_profile.read(template_id) is None:
                template_id = self.template_profile.create(template.get("template_name", "Default Template"))
                self.template_profile_records_module.create(template_id, template.get("id_pais"), template.get("id_ciudad"), template.get("id_barrio"), template.get("id_partido_politico"), template.get("id_club_futbol"), template.get("id_ideologia"), template.get("id_estilo_musica"), template.get("id_genero"))

            records = self.template_profile_records_module.list_by_template(template_id)

            combined = []
            for idx_p, base in enumerate(payloads):
                if not isinstance(base, dict):
                    return {"success": False, "error": f"Each payload must be a dict, item {idx_p} invalid"}
                for rec in records:
                    # Start from base payload and apply record defaults for FK fields
                    item = dict(base)  # shallow copy
                    for fk in ('id_pais', 'id_ciudad', 'id_barrio', 'id_partido_politico', 'id_club_futbol', 'id_ideologia', 'id_estilo_musica', 'id_genero'):
                        val = rec.get(fk)
                        if val is not None:
                            item[fk] = val
                    # Associate created item with template
                    item['id_plantilla'] = template_id
                    combined.append(item)

            # Reuse create_bulk to insert all combined payloads
            return self.create_bulk(combined, transactional=transactional)
        except Exception as e:
            return {"success": False, "inserted_ids": [], "error": str(e)}

    def get_profile_with_relations(self, profile_id: int) -> dict:
        """Obtiene un perfil por id y resuelve las relaciones FK.

        Devuelve un diccionario con la estructura:
        {
            'profile': { ... perfil ... },
            'pais': {...} | None,
            'ciudad': {...} | None,
            'barrio': {...} | None,
            'partido_politico': {...} | None,
            'club_futbol': {...} | None,
            'ideologia': {...} | None,
            'estilo_musica': {...} | None,
            'genero': {...} | None
        }
        """
        profile = self.module.read(profile_id)
        if not profile:
            return {"success": False, "error": f"Profile id {profile_id} not found", "profile": None}

        result = {"success": True, "profile": profile}

        # Resolve FK relations if present
        id_pais = profile.get('id_pais')
        id_ciudad = profile.get('id_ciudad')
        id_barrio = profile.get('id_barrio')
        id_partido = profile.get('id_partido_politico')
        id_club = profile.get('id_club_futbol')
        id_ideologia = profile.get('id_ideologia')
        id_estilo = profile.get('id_estilo_musica')
        id_genero = profile.get('id_genero')

        result['pais'] = self.countries.read(id_pais) if id_pais else None
        result['ciudad'] = self.cities.read(id_ciudad) if id_ciudad else None
        result['barrio'] = self.neighborhoods.read(id_barrio) if id_barrio else None
        result['partido_politico'] = self.political_parties.read(id_partido) if id_partido else None
        result['club_futbol'] = self.football_clubs.read(id_club) if id_club else None
        result['ideologia'] = self.ideologies.read(id_ideologia) if id_ideologia else None
        result['estilo_musica'] = self.music_styles.read(id_estilo) if id_estilo else None
        result['genero'] = self.genders.read(id_genero) if id_genero else None

        return result

    def get_profiles_by_template(self, template_id: int, page: int | None = None, per_page: int | None = None) -> dict:
        """Obtiene todos los perfiles asociados a una plantilla con sus relaciones.

        Retorna: { success: bool, profiles: list[dict], error: str|None }
        """
        try:
            tid = int(template_id)
        except Exception:
            return {"success": False, "profiles": [], "error": "template_id must be an integer"}

        try:
            ids = self.module.list_ids_by_template(tid)
            if not ids:
                return {"success": True, "profiles": [], "pagination": None, "error": None}

            total = len(ids)

            # Validate pagination params
            if (page is None) ^ (per_page is None):
                return {"success": False, "profiles": [], "error": "Both page and per_page must be provided for pagination"}

            if page is not None and per_page is not None:
                try:
                    page = int(page)
                    per_page = int(per_page)
                    if page < 1 or per_page < 1:
                        raise ValueError()
                except Exception:
                    return {"success": False, "profiles": [], "error": "page and per_page must be positive integers"}

                total_pages = math.ceil(total / per_page) if per_page else 0
                # call module with pagination
                profiles = self.module.bulk_read_with_relations(ids, page=page, per_page=per_page)
                pagination = {"total": total, "page": page, "per_page": per_page, "total_pages": total_pages}
                return {"success": True, "profiles": profiles, "pagination": pagination, "error": None}

            # No pagination requested: return all
            profiles = self.module.bulk_read_with_relations(ids)
            return {"success": True, "profiles": profiles, "pagination": None, "error": None}
        except Exception as e:
            return {"success": False, "profiles": [], "error": str(e)}

    def get_profiles(self, filters: dict | None = None, page: int | None = None, per_page: int | None = None, order_by: str | None = None) -> dict:
        """Lista perfiles con filtros y paginación delegando a ProfilesModule.list_with_relations.

        filters: diccionario con claves permitidas (id_pais, id_ciudad, id_barrio, id_partido_politico,
                 id_club_futbol, id_ideologia, id_estilo_musica, id_genero, id_plantilla)
        page/per_page: paginación (deben proporcionarse juntos)
        order_by: columna segura para ordenar
        """
        try:
            result = self.module.list_with_relations(filters=filters, page=page, per_page=per_page, order_by=order_by)
            return result
        except Exception as e:
            return {"success": False, "total": 0, "profiles": [], "page": page, "per_page": per_page, "error": str(e)}

    def delete_profile(self, profile_id: int) -> dict:
        """Elimina un perfil por su id.

        Retorna { success: bool, deleted: int, error: str|None }
        """
        try:
            pid = int(profile_id)
        except Exception:
            return {"success": False, "deleted": 0, "error": "profile_id must be an integer"}

        try:
            deleted = self.module.delete(pid)
            # module.delete returns bool; convert to int count approximation
            return {"success": True, "deleted": 1 if deleted else 0, "error": None}
        except Exception as e:
            return {"success": False, "deleted": 0, "error": str(e)}

    def delete_profiles_by_relation(self, relation: str, relation_id: int) -> dict:
        """Elimina todos los perfiles asociados a una relación (ej. id_plantilla).

        relation: nombre de columna FK permitido.
        relation_id: id de la relación.
        Retorna { success: bool, deleted: int, error: str|None }
        """
        try:
            deleted = self.module.delete_by_relation(relation, relation_id)
            return {"success": True, "deleted": int(deleted), "error": None}
        except Exception as e:
            return {"success": False, "deleted": 0, "error": str(e)}

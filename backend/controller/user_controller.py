import sys
from pathlib import Path
import re

sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.user import UserModule


class UserController:
    """Controlador para operaciones sobre `usuarios`.

    Sigue el mismo formato que `ProfileController` pero adaptado a `UserModule`.
    Devuelve diccionarios simples que un adaptador HTTP puede convertir en JSON.
    """

    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self):
        self.module = UserModule()

    def validate_payload(self, payload: dict, require_password: bool = True) -> tuple[bool, list]:
        """Valida los campos esenciales para crear/actualizar un usuario.

        require_password: si True exige el campo `password` (crear), si False lo permite omitir (update).
        Retorna (is_valid, errors_list).
        """
        errors = []
        if not isinstance(payload, dict):
            return False, ["Payload must be a dict"]

        nombre = payload.get('nombre')
        apellido = payload.get('apellido')
        correo = payload.get('correo')
        password = payload.get('password')
        id_rol = payload.get('id_rol')

        if not nombre or not isinstance(nombre, str) or not nombre.strip():
            errors.append("'nombre' is required and must be a non-empty string")
        if not apellido or not isinstance(apellido, str) or not apellido.strip():
            errors.append("'apellido' is required and must be a non-empty string")
        if not correo or not isinstance(correo, str) or not correo.strip():
            errors.append("'correo' is required and must be a non-empty string")
        else:
            correo_norm = correo.strip().lower()
            if not self.EMAIL_RE.match(correo_norm):
                errors.append("'correo' has invalid format")

        if require_password:
            if not password or not isinstance(password, str) or password == '':
                errors.append("'password' is required and must be a non-empty string")

        # id_rol if present must be integer-convertible
        if id_rol is not None:
            try:
                int(id_rol)
            except Exception:
                errors.append("'id_rol' must be an integer if provided")

        return (len(errors) == 0), errors

    def create(self, payload: dict) -> dict:
        """Crea un usuario.

        Retorna { success: bool, id: int|None, error: str|None, details?: list }
        """
        is_valid, errors = self.validate_payload(payload, require_password=True)
        if not is_valid:
            return {"success": False, "id": None, "error": "Validation failed", "details": errors}

        nombre = payload.get('nombre').strip()
        apellido = payload.get('apellido').strip()
        correo = payload.get('correo').strip().lower()
        password = payload.get('password')
        id_rol = payload.get('id_rol')

        if id_rol is not None:
            try:
                id_rol = int(id_rol)
            except Exception:
                return {"success": False, "id": None, "error": "id_rol must be an integer"}

        try:
            new_id = self.module.create_user(nombre, apellido, correo, password, id_rol)
            return {"success": True, "id": new_id, "error": None}
        except Exception as e:
            return {"success": False, "id": None, "error": str(e)}

    def get_user(self, user_id: int) -> dict:
        """Obtiene un usuario por id (sin password)."""
        try:
            uid = int(user_id)
        except Exception:
            return {"success": False, "user": None, "error": "user_id must be an integer"}

        try:
            user = self.module.get_user_by_id(uid)
            if not user:
                return {"success": False, "user": None, "error": f"User id {uid} not found"}
            return {"success": True, "user": user, "error": None}
        except Exception as e:
            return {"success": False, "user": None, "error": str(e)}

    def get_user_by_email(self, correo: str) -> dict:
        """Obtiene usuario por correo."""
        if not correo or not isinstance(correo, str):
            return {"success": False, "user": None, "error": "correo must be a non-empty string"}
        try:
            user = self.module.get_user_by_email(correo.strip().lower())
            if not user:
                return {"success": False, "user": None, "error": "User not found"}
            return {"success": True, "user": user, "error": None}
        except Exception as e:
            return {"success": False, "user": None, "error": str(e)}

    def list_users(self, limit: int = 100, offset: int = 0) -> dict:
        """Lista usuarios con paginación simple."""
        try:
            limit_i = int(limit)
            offset_i = int(offset)
            users = self.module.list_users(limit=limit_i, offset=offset_i)
            return {"success": True, "users": users, "error": None, "limit": limit_i, "offset": offset_i}
        except Exception as e:
            return {"success": False, "users": [], "error": str(e)}

    def update_user(self, user_id: int, payload: dict) -> dict:
        """Actualiza campos de usuario. No requiere password por defecto."""
        try:
            uid = int(user_id)
        except Exception:
            return {"success": False, "updated": False, "error": "user_id must be an integer"}

        # Validate payload (password optional)
        is_valid, errors = self.validate_payload(payload, require_password=False)
        if not is_valid:
            return {"success": False, "updated": False, "error": "Validation failed", "details": errors}

        nombre = payload.get('nombre')
        apellido = payload.get('apellido')
        correo = payload.get('correo')
        password = payload.get('password')
        id_rol = payload.get('id_rol')

        if id_rol is not None:
            try:
                id_rol = int(id_rol)
            except Exception:
                return {"success": False, "updated": False, "error": "id_rol must be an integer"}

        try:
            updated = self.module.update_user(uid, nombre=nombre, apellido=apellido, correo=correo, password=password, id_rol=id_rol)
            return {"success": True, "updated": bool(updated), "error": None}
        except Exception as e:
            return {"success": False, "updated": False, "error": str(e)}

    def delete_user(self, user_id: int) -> dict:
        """Elimina un usuario por id."""
        try:
            uid = int(user_id)
        except Exception:
            return {"success": False, "deleted": 0, "error": "user_id must be an integer"}

        try:
            deleted = self.module.delete_user(uid)
            return {"success": True, "deleted": 1 if deleted else 0, "error": None}
        except Exception as e:
            return {"success": False, "deleted": 0, "error": str(e)}

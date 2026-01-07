import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from modules.config import Database
import os
import hashlib
import binascii
import hmac


class UserModule:
    def __init__(self):
        self.db = Database()
        # Nombre de la tabla según database/db_backend.sql
        self.table = 'usuarios'

    # --- Helper: hashing de contraseñas ---
    def _hash_password(self, password: str) -> str:
        """Genera un hash seguro de la contraseña usando PBKDF2-HMAC-SHA256.

        Retorna el valor formateado como: iterations$salt_hex$hash_hex
        """
        if not isinstance(password, str) or password == '':
            raise ValueError("Password debe ser una cadena no vacía")
        iterations = 100_000
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return f"{iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verifica una contraseña en claro contra el hash almacenado."""
        try:
            iterations_str, salt_hex, hash_hex = stored_hash.split('$')
            iterations = int(iterations_str)
            salt = binascii.unhexlify(salt_hex)
            expected = binascii.unhexlify(hash_hex)
            dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
            return hmac.compare_digest(dk, expected)
        except Exception:
            return False

    # --- CRUD ---
    def create_user(self, nombre: str, apellido: str, correo: str, password: str, id_rol: int) -> int:
        """Crea un nuevo usuario y devuelve su id."""
        if not all([nombre, apellido, correo, password]):
            raise ValueError("Todos los campos nombre, apellido, correo y password son obligatorios")
        pw_hash = self._hash_password(password)
        query = f"INSERT INTO {self.table} (nombre, apellido, correo, password, id_rol) VALUES (%s, %s, %s, %s, %s)"
        params = (nombre, apellido, correo, pw_hash, id_rol)
        return self.db.insert_query(query, params)

    def get_user_by_id(self, user_id: int) -> dict | None:
        query = f"SELECT id, nombre, apellido, correo, id_rol FROM {self.table} WHERE id = %s"
        results = self.db.query(query, (user_id,))
        return results[0] if results else None

    def get_user_by_email(self, correo: str) -> dict | None:
        query = f"SELECT * FROM {self.table} WHERE correo = %s"
        results = self.db.query(query, (correo,))
        return results[0] if results else None

    def list_users(self, limit: int = 100, offset: int = 0) -> list:
        query = f"SELECT id, nombre, apellido, correo, id_rol FROM {self.table} ORDER BY id LIMIT %s OFFSET %s"
        results = self.db.query(query, (limit, offset))
        return results or []

    def update_user(self, user_id: int, nombre: str = None, apellido: str = None, correo: str = None, password: str = None, id_rol: int = None) -> bool:
        """Actualiza campos del usuario. Devuelve True si se actualizó algún registro."""
        fields = []
        params = []
        if nombre is not None:
            fields.append('nombre = %s')
            params.append(nombre)
        if apellido is not None:
            fields.append('apellido = %s')
            params.append(apellido)
        if correo is not None:
            fields.append('correo = %s')
            params.append(correo)
        if password is not None:
            pw_hash = self._hash_password(password)
            fields.append('password = %s')
            params.append(pw_hash)
        if id_rol is not None:
            fields.append('id_rol = %s')
            params.append(id_rol)

        if not fields:
            return False

        params.append(user_id)
        set_clause = ', '.join(fields)
        query = f"UPDATE {self.table} SET {set_clause} WHERE id = %s"
        # Usamos query() que hace commit internally
        self.db.query(query, tuple(params))
        return True

    def delete_user(self, user_id: int) -> bool:
        query = f"DELETE FROM {self.table} WHERE id = %s"
        self.db.query(query, (user_id,))
        return True
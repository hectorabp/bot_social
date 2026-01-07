import json
import redis
import typing as t
import os

class RedisSessionManager:
    def __init__(self, host='localhost', port=6379, db=0, password=None, prefix="bot_social:"):
        # Permitir configuración vía variables de entorno si están disponibles
        self.host = os.getenv('REDIS_HOST', host)
        self.port = int(os.getenv('REDIS_PORT', port))
        
        # En caso de que se ejecute desde dentro de docker, el host podría ser 'redis_bot_social'
        # Pero si se ejecuta desde local (fuera del contenedor), usamos 'localhost'
        
        self.client = redis.Redis(
            host=self.host, 
            port=self.port, 
            db=db, 
            password=password, 
            decode_responses=True
        )
        self.prefix = prefix

    def _get_key(self, session_id: str, key_type: str) -> str:
        return f"{self.prefix}{session_id}:{key_type}"

    def save_profile(self, session_id: str, profile_data: dict, ttl: int = None):
        key = self._get_key(session_id, "profile")
        self.client.set(key, json.dumps(profile_data))
        if ttl:
            self.client.expire(key, ttl)

    def load_profile(self, session_id: str) -> t.Optional[dict]:
        key = self._get_key(session_id, "profile")
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def delete_profile(self, session_id: str):
        key = self._get_key(session_id, "profile")
        self.client.delete(key)

    def save_cookies(self, session_id: str, cookies_data: list, ttl: int = None):
        key = self._get_key(session_id, "cookies")
        self.client.set(key, json.dumps(cookies_data))
        if ttl:
            self.client.expire(key, ttl)

    def load_cookies(self, session_id: str) -> t.Optional[list]:
        key = self._get_key(session_id, "cookies")
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def delete_cookies(self, session_id: str):
        key = self._get_key(session_id, "cookies")
        self.client.delete(key)

    def clear_session(self, session_id: str):
        """Elimina tanto el perfil como las cookies de la sesión especificada."""
        self.delete_profile(session_id)
        self.delete_cookies(session_id)

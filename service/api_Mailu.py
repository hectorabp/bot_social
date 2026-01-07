import requests
import os
from typing import List, Optional, Dict, Any

class MailuClient:
    """
    Cliente para interactuar con la API de Mailu alojada en cabichui.com
    """
    
    def __init__(self, base_url: str = "https://cabichui.com", api_key: Optional[str] = None):
        """
        Inicializa el cliente de Mailu.
        
        Args:
            base_url: URL base de la API (por defecto: https://cabichui.com)
            api_key: Clave de API para autenticación. Si no se proporciona, 
                     intenta leerla de la variable de entorno APP_API_KEY.
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv('APP_API_KEY')
        self.headers = {
            'Content-Type': 'application/json'
        }
        if self.api_key:
            self.headers['X-API-Key'] = self.api_key

    def _get_url(self, endpoint: str) -> str:
        """Construye la URL completa para un endpoint."""
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        return f"{self.base_url}{endpoint}"

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Procesa la respuesta de la API."""
        try:
            return response.json()
        except ValueError:
            return {
                "success": False,
                "error": f"Error de decodificación JSON. Status: {response.status_code}, Content: {response.text}"
            }

    # ==================== USUARIOS ====================

    def create_user(self, email: str, password: str, display_name: str = "", 
                   quota_bytes: int = 1000000000, enable_imap: bool = True, 
                   enable_pop: bool = True) -> Dict[str, Any]:
        """
        Crea un nuevo usuario de correo.
        """
        url = self._get_url('/api/mailu/users')
        data = {
            "email": email,
            "password": password,
            "display_name": display_name,
            "quota_bytes": quota_bytes,
            "enable_imap": enable_imap,
            "enable_pop": enable_pop
        }
        response = requests.post(url, json=data, headers=self.headers)
        return self._handle_response(response)

    def delete_user(self, email: str) -> Dict[str, Any]:
        """
        Elimina un usuario de correo.
        """
        url = self._get_url(f'/api/mailu/users/{email}')
        response = requests.delete(url, headers=self.headers)
        return self._handle_response(response)

    def get_user(self, email: str) -> Dict[str, Any]:
        """
        Obtiene información de un usuario.
        """
        url = self._get_url(f'/api/mailu/users/{email}')
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)

    def list_users(self, domain: str = 'cabichui.com') -> Dict[str, Any]:
        """
        Lista todos los usuarios de un dominio.
        """
        url = self._get_url('/api/mailu/users')
        params = {'domain': domain}
        response = requests.get(url, params=params, headers=self.headers)
        return self._handle_response(response)

    def update_password(self, email: str, new_password: str) -> Dict[str, Any]:
        """
        Actualiza la contraseña de un usuario.
        """
        url = self._get_url(f'/api/mailu/users/{email}/password')
        data = {"new_password": new_password}
        response = requests.patch(url, json=data, headers=self.headers)
        return self._handle_response(response)

    # ==================== CORREOS ====================

    def read_emails(self, email: str, password: str, folder: str = 'INBOX', 
                   limit: int = 10, unread_only: bool = False) -> Dict[str, Any]:
        """
        Lee correos electrónicos de un usuario.
        """
        url = self._get_url('/api/mailu/emails/read')
        data = {
            "email": email,
            "password": password,
            "folder": folder,
            "limit": limit,
            "unread_only": unread_only
        }
        response = requests.post(url, json=data, headers=self.headers)
        return self._handle_response(response)

    def send_email(self, from_email: str, password: str, to_email: str, 
                  subject: str, body: str, is_html: bool = False, 
                  cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Envía un correo electrónico.
        """
        url = self._get_url('/api/mailu/emails/send')
        data = {
            "from_email": from_email,
            "password": password,
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "is_html": is_html,
            "cc": cc or [],
            "bcc": bcc or []
        }
        response = requests.post(url, json=data, headers=self.headers)
        return self._handle_response(response)

    # ==================== ALIAS ====================

    def create_alias(self, alias_email: str, destination_email: str) -> Dict[str, Any]:
        """
        Crea un alias de correo.
        """
        url = self._get_url('/api/mailu/aliases')
        data = {
            "alias_email": alias_email,
            "destination_email": destination_email
        }
        response = requests.post(url, json=data, headers=self.headers)
        return self._handle_response(response)

    def delete_alias(self, alias_email: str) -> Dict[str, Any]:
        """
        Elimina un alias de correo.
        """
        url = self._get_url(f'/api/mailu/aliases/{alias_email}')
        response = requests.delete(url, headers=self.headers)
        return self._handle_response(response)

    # ==================== HEALTH CHECK ====================

    def health_check(self) -> Dict[str, Any]:
        """
        Verifica que la API está funcionando.
        """
        url = self._get_url('/api/mailu/health')
        response = requests.get(url)
        return self._handle_response(response)

from typing import Any, Dict, Optional
from .send_data import SendData


class ApiEmailGenerator:
    """Cliente ligero para comunicarse con el microservicio email_generator.

    Usa la clase SendData existente para realizar las llamadas HTTP.
    """

    def __init__(self, host: str = "localhost", port: int = 3001):
        """Inicializa el cliente apuntando al host y puerto del servicio.

        Args:
            host: dirección del servicio (por defecto 'localhost')
            port: puerto del servicio (por defecto 3001, ver `email_generator/index.js`)
        """
        self._sender = SendData(host, port)

    def health(self) -> Optional[Dict[str, Any]]:
        """Consulta la ruta raíz (health) del servicio.

        Devuelve el JSON del servicio o None en caso de error.
        """
        return self._sender.send_data({}, endpoint="", method="GET")

    def create_account(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Lanza la creación de cuenta llamando al endpoint `/create-account`.

        Args:
            payload: diccionario con los parámetros que espera el servicio de generación
                     de cuentas (por ejemplo: firstName, lastName, day, month, year, gender, username)

        Returns:
            El JSON resultante del servicio o None si ocurre un error de comunicación.
        """
        # SendData espera el parámetro endpoint sin slash al inicio
        return self._sender.send_data(payload, endpoint="create-account", method="POST")

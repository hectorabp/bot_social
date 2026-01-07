"""
Cliente ligero y actualizado para OpenAI.

Usa el SDK moderno (>=1.0) de OpenAI, con importación perezosa y soporte para
definir la API key mediante variable de entorno OPENAI_API_KEY o con set_api_key().

Por defecto usa el modelo DEFAULT_MODEL = 'gpt-5-mini', pero puede sobrescribirse
en la instancia o al llamar a send_message().
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

DEFAULT_MODEL = "gpt-5-mini"


class OpenAIClient:
    """Cliente moderno y ligero para llamadas a OpenAI.

    Características:
    - Importación perezosa del paquete `openai`.
    - Permite definir API key por variable de entorno o método.
    - Maneja envíos de mensajes estilo Chat API.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """Inicializa el cliente.

        model: modelo por defecto; si None usa DEFAULT_MODEL.
        timeout: tiempo de espera en segundos para llamadas de red.
        """
        self._api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout
        self._client = None  # Cliente de OpenAI (importado perezosamente)

    def _ensure_client(self) -> None:
        """Importa perezosamente `openai` y crea el cliente."""
        if self._client is not None:
            return
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "El paquete 'openai' no está instalado. Instálalo con: pip install openai"
            ) from exc

        if not self._api_key:
            raise RuntimeError(
                "No se encontró API key. Usa set_api_key() o define OPENAI_API_KEY en el entorno."
            )

        self._client = OpenAI(api_key=self._api_key)

    def set_api_key(self, api_key: str) -> None:
        """Permite establecer o cambiar la API key en tiempo de ejecución."""
        self._api_key = api_key
        if self._client is not None:
            # Recrea el cliente si ya existía
            from openai import OpenAI
            self._client = OpenAI(api_key=self._api_key)

    def send_message(
        self,
        message: Union[str, List[Dict[str, str]]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """Envía un mensaje y devuelve la respuesta como texto.

        Parámetros:
        - message: puede ser un string (contenido para rol user) o una lista de mensajes [{'role':..., 'content':...}].
        - model: opcional, sobrescribe el modelo por defecto.
        - temperature: se intenta usar; si el modelo no lo soporta se reintenta sin él.
        - max_tokens: máximo de tokens de la completion (usa max_completion_tokens internamente).
        - system_prompt: si se provee y 'message' es un string, este se añade como primer mensaje con rol 'system' y el string pasa a rol 'user'.

        Comportamiento especial:
        - Si 'message' es lista y ya incluye un mensaje con rol 'system', system_prompt se ignora (no se duplicará).
        - Si 'message' es lista y NO incluye rol 'system' y se pasa system_prompt, se antepone.

        Ejemplos rápidos:
        1) client.send_message(html, system_prompt="Eres un extractor...")
           => Mensajes: [system:{Eres un extractor...}, user:{html}]
        2) client.send_message([
               {"role":"system","content":"Config base"},
               {"role":"user","content":"Hola"}
           ], system_prompt="IGNORADO")
           => system_prompt ignorado (ya existe uno).
        """
        self._ensure_client()
        model_to_use = model or self.model
        if isinstance(message, str):
            # Construimos lista con posible system
            messages: List[Dict[str, str]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
        elif isinstance(message, list):
            messages = list(message)  # copia superficial
            if system_prompt:
                has_system = any(m.get("role") == "system" for m in messages)
                if not has_system:
                    messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            raise TypeError("El parámetro 'message' debe ser str o lista de dicts {'role','content'}.")

        # Construcción inicial kwargs sin forzar temperature si el modelo no lo soporta
        kwargs = {
            "model": model_to_use,
            "messages": messages,
        }
        if max_tokens is not None:
            kwargs["max_completion_tokens"] = max_tokens

        # Intentar con temperature; si el modelo no lo soporta, remover y reintentar
        attempt_temperature = temperature
        for attempt in range(2):
            try:
                if attempt == 0:
                    # Primer intento: incluir temperature solo si es distinto de None
                    if attempt_temperature is not None:
                        kwargs["temperature"] = attempt_temperature
                else:
                    # Segundo intento: quitar temperature
                    if "temperature" in kwargs:
                        del kwargs["temperature"]
                resp = self._client.chat.completions.create(**kwargs)
                print(f"Respuesta IA (completions): {resp}")
                return resp.choices[0].message.content
            except Exception as exc:
                msg = str(exc)
                if attempt == 0 and ("Unsupported value: 'temperature'" in msg or "does not support" in msg):
                    # Reintentar sin temperature
                    continue
                if attempt == 0 and ("Unsupported parameter: 'max_tokens'" in msg or "Unsupported parameter" in msg):
                    # Ajustar clave de tokens si el modelo usa otro nombre (ya usamos max_completion_tokens)
                    if "max_tokens" in kwargs:
                        kwargs.pop("max_tokens", None)
                    continue
                raise RuntimeError(f"Error al comunicarse con OpenAI: {exc}") from exc

    def ping(self) -> bool:
        """Verifica disponibilidad mínima del servicio."""
        try:
            self._ensure_client()
            self._client.models.retrieve(self.model)
            return True
        except Exception:
            return False


__all__ = ["OpenAIClient", "DEFAULT_MODEL"]

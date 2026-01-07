import sys
from pathlib import Path
import re
from typing import List, Dict, Any, Optional, Iterable

sys.path.append(str(Path(__file__).resolve().parent.parent))
from service.api_email_generator import ApiEmailGenerator
from .task_controller import TaskController


class EmailGeneratorController:
    """Controlador para delegar en el microservicio `email_generator`.

    Recibe payloads que usan el campo `email` en lugar de `username`.
    Internamente mappea `email` -> `username` (usa la parte local antes del `@` si existe)
    para adaptarse a la API del generador de cuentas.
    """

    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, host: str = "localhost", port: int = 3001, logger=None):
        self.api = ApiEmailGenerator(host=host, port=port)
        self.logger = logger
        self.task_controller = TaskController(host=host, port=port, logger=logger)

    def _validate_payload(self, payload: dict) -> tuple[bool, list]:
        """Valida campos esperados para crear una cuenta.

        Campos requeridos esperados (entrada pública):
        - firstName (str)
        - lastName (str)
        - email (str)  <-- reemplaza a 'username' según preferencia del usuario
        - day (int), month (int), year (int)
        - gender (int|str)

        Retorna (is_valid, errors_list).
        """
        errors = []
        if not isinstance(payload, dict):
            return False, ["payload must be a dict"]

        # Required string fields
        for k in ("firstName", "lastName", "email"):
            v = payload.get(k)
            if not v or not isinstance(v, str) or not v.strip():
                errors.append(f"'{k}' is required and must be a non-empty string")

        # Validate email format
        email = payload.get("email")
        if isinstance(email, str) and email.strip():
            if not self.EMAIL_RE.match(email.strip()):
                errors.append("'email' has invalid format")

        # Validate dob
        try:
            day = int(payload.get("day"))
            month = int(payload.get("month"))
            year = int(payload.get("year"))
            if not (1 <= day <= 31):
                errors.append("'day' must be in 1..31")
            if not (1 <= month <= 12):
                errors.append("'month' must be in 1..12")
            if not (1900 <= year <= 2100):
                errors.append("'year' must be a reasonable integer (1900..2100)")
        except Exception:
            errors.append("'day', 'month' and 'year' are required and must be integers")

        # gender presence check (flexible)
        if "gender" not in payload:
            errors.append("'gender' is required")

        return (len(errors) == 0), errors

    def _email_to_username(self, email: str) -> str:
        """Convierte un email a un username usable por el servicio.

        Si el email contiene '@' usa la parte local (antes del @). Si no, devuelve
        la cadena tal cual. Esta función evita pasar un '@' en el campo `username`.
        """
        if not isinstance(email, str):
            return str(email)
        if "@" in email:
            return email.split("@", 1)[0]
        return email

    def health(self) -> dict:
        """Consulta el endpoint health del servicio email_generator.

        Retorna: { success: bool, status: dict|null, error: str|None }
        """
        try:
            res = self.api.health()
            if res is None:
                return {"success": False, "status": None, "error": "email_generator unreachable"}
            return {"success": True, "status": res, "error": None}
        except Exception as e:
            if self.logger:
                self.logger.error("health check error", exc_info=e)
            return {"success": False, "status": None, "error": str(e)}

    def create_account(self, payload: dict) -> dict:
        """Valida y crea una cuenta delegando a ApiEmailGenerator.

        Acepta `email` como campo en lugar de `username` y lo mapea antes
        de llamar al microservicio.
        """
        is_valid, errors = self._validate_payload(payload)
        if not is_valid:
            return {"success": False, "data": None, "error": "Validation failed", "details": errors}

        try:
            # Normalize and map
            firstName = payload.get("firstName").strip()
            lastName = payload.get("lastName").strip()
            email = payload.get("email").strip()
            day = int(payload.get("day"))
            month = int(payload.get("month"))
            year = int(payload.get("year"))
            gender = payload.get("gender")

            username = self._email_to_username(email)

            call_payload = {
                "firstName": firstName,
                "lastName": lastName,
                "day": day,
                "month": month,
                "year": year,
                "gender": gender,
                # El servicio espera 'username' — lo rellenamos a partir de 'email'.
                "username": username,
                # Conservamos el email original para trazabilidad si el servicio lo acepta
                "email": email,
            }

            res = self.api.create_account(call_payload)
            if res is None:
                return {"success": False, "data": None, "error": "email_generator unreachable"}

            # Si el microservicio devuelve un objeto con error interno, lo propagamos
            # devolviendo success False y detalles.
            if isinstance(res, dict) and res.get("success") is False:
                return {"success": False, "data": res, "error": "remote service reported failure", "details": res}

            return {"success": True, "data": res, "error": None}
        except Exception as e:
            if self.logger:
                self.logger.error("create_account error", exc_info=e)
            return {"success": False, "data": None, "error": str(e)}

    def schedule_accounts(
        self,
        payloads: Iterable[Dict[str, Any]],
        interval_seconds: int = 60,
        intervals: Optional[Iterable[int]] = None,
        start_delay: int = 0,
        use_countdown: bool = True,
        expires: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Programa la creación de múltiples cuentas con intervalos.

        Valida cada payload antes de programar. Si algún payload es inválido,
        no programa ninguna y retorna errores.

        Args:
            payloads: Lista de payloads para crear cuentas.
            interval_seconds, intervals, start_delay, use_countdown, expires: Parámetros de scheduling.

        Returns:
            Dict con 'success', 'task_ids', 'error', 'validation_errors'.
        """
        payloads_list = list(payloads)
        validation_errors = []
        for i, payload in enumerate(payloads_list):
            is_valid, errors = self._validate_payload(payload)
            if not is_valid:
                validation_errors.append({"index": i, "errors": errors})

        if validation_errors:
            return {
                "success": False,
                "task_ids": [],
                "error": "Validation failed for some payloads",
                "validation_errors": validation_errors,
            }

        try:
            result = self.task_controller.schedule_email_tasks(
                payloads=payloads_list,
                interval_seconds=interval_seconds,
                intervals=intervals,
                start_delay=start_delay,
                use_countdown=use_countdown,
                expires=expires,
                host=self.api.host,
                port=self.api.port,
            )
            return result
        except Exception as e:
            if self.logger:
                self.logger.error("schedule_accounts error", exc_info=e)
            return {"success": False, "task_ids": [], "error": str(e), "validation_errors": []}

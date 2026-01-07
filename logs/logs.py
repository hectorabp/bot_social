import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

class Logger:
    """
    Clase para manejar el registro de logs de acciones de cuentas.
    Permite registrar acciones agrupadas por email en archivos JSON diarios.
    """

    def __init__(self, platform: str = "general", base_log_directory: str = "logs"):
        """
        Inicializa el logger.
        
        :param platform: Nombre de la plataforma o subcarpeta (ej. 'x', 'facebook').
        :param base_log_directory: Ruta al directorio base de logs (por defecto 'logs').
        """
        self.platform = platform
        self.base_log_directory = base_log_directory
        # Construir la ruta completa: logs/platform
        self.log_directory = os.path.join(self.base_log_directory, self.platform)
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """Asegura que el directorio de logs exista."""
        if not os.path.exists(self.log_directory):
            try:
                os.makedirs(self.log_directory)
            except OSError as e:
                print(f"Error creando directorio de logs {self.log_directory}: {e}")

    def _get_log_file_path(self, date_obj: datetime = None) -> str:
        """Obtiene la ruta del archivo de log para una fecha dada (por defecto hoy)."""
        if date_obj is None:
            date_obj = datetime.now()
        
        date_str = date_obj.strftime("%Y-%m-%d")
        return os.path.join(self.log_directory, f"{date_str}_logs.json")

    def _read_logs(self, file_path: str) -> List[Dict[str, Any]]:
        """Lee los logs existentes de un archivo JSON de manera segura."""
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                    else:
                        print(f"Advertencia: El formato del archivo {file_path} no es una lista. Se reiniciará.")
                        return []
        except json.JSONDecodeError:
            print(f"Error: El archivo {file_path} contiene JSON inválido.")
            return []
        except Exception as e:
            print(f"Error leyendo logs existentes en {file_path}: {e}")
            return []

    def _write_logs(self, file_path: str, logs: List[Dict[str, Any]]):
        """Escribe la lista de logs en el archivo JSON."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error crítico al guardar log en {file_path}: {e}")

    def log_action(self, email: str, action: str, status: Union[List[Any], Dict[str, Any]] = [], observations: str = "", uso_ia: str = "NO"):
        """
        Registra una acción en el archivo de logs del día actual.
        
        :param email: El correo electrónico asociado a la acción.
        :param action: El nombre de la acción realizada (ej. "login", "create_account").
        :param status: Lista o diccionario con detalles del estado.
        :param observations: Texto libre con observaciones.
        :param uso_ia: Indicador de si se usó IA ("SI"/"NO").
        """
        try:
            log_file = self._get_log_file_path()
            logs = self._read_logs(log_file)

            new_log_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": action,
                "status": status,
                "observaciones": observations,
                "uso_ia": uso_ia
            }

            # Buscar si ya existe una entrada para este email
            email_found = False
            for entry in logs:
                if entry.get("email") == email:
                    if "logs" not in entry:
                        entry["logs"] = []
                    entry["logs"].append(new_log_entry)
                    email_found = True
                    break
            
            # Si no existe, crear nueva entrada
            if not email_found:
                new_entry = {
                    "email": email,
                    "logs": [new_log_entry]
                }
                logs.append(new_entry)
            
            self._write_logs(log_file, logs)
            
        except Exception as e:
            print(f"Error al registrar acción para {email}: {e}")

    def get_logs_by_email(self, email: str, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de logs de un email específico.
        
        :param email: El correo a buscar.
        :param date_str: Fecha en formato "YYYY-MM-DD". Si es None, usa la fecha actual.
        :return: Lista de entradas de log para ese email.
        """
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                file_path = self._get_log_file_path(date_obj)
            except ValueError:
                print(f"Formato de fecha inválido: {date_str}. Use YYYY-MM-DD.")
                return []
        else:
             file_path = self._get_log_file_path()
             
        logs = self._read_logs(file_path)
        for entry in logs:
            if entry.get("email") == email:
                return entry.get("logs", [])
        return []

    def get_all_logs_for_date(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """Devuelve todos los logs de una fecha específica."""
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                file_path = self._get_log_file_path(date_obj)
            except ValueError:
                print(f"Formato de fecha inválido: {date_str}. Use YYYY-MM-DD.")
                return []
        else:
             file_path = self._get_log_file_path()
        
        return self._read_logs(file_path)

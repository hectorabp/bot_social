
import requests

class SendData:
    def __init__(self, url, port):
        self.base_url = f"http://{url}:{port}"

    def send_data(self, data, endpoint="", method="POST"):
        """Envia solicitudes HTTP al backend"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data)
            elif method.upper() == "GET":
                response = requests.get(url, params=data)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=data)
            else:
                print(f"Error: Método HTTP '{method}' no soportado.")
                return None

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error al enviar datos a {url}: {e}")
            return None

import base64
import os
from google import genai
# Eliminamos la importación específica de 'types' que causaba el error
# from google.genai import types 

class ImageGenerationError(Exception):
    """Excepción personalizada para errores en la generación de imágenes."""
    pass

class ImageGenerator:
    """
    Módulo para generar imágenes usando Google GenAI (Nano Banana Pro / Imagen 3)
    """

    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de Google.
        Si no se pasa api_key, intenta leerla de GOOGLE_API_KEY.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("La API Key es obligatoria. Configura GOOGLE_API_KEY.")
        
        # Inicializamos el cliente de Google
        self.client = genai.Client(api_key=self.api_key)

    def generate(
        self,
        prompt: str,
        model: str = "imagen-4.0-generate-001", 
        aspect_ratio: str = "1:1",
        number_of_images: int = 1,
        return_base64: bool = True
    ) -> str:
        """
        Genera una imagen a partir de un prompt usando Imagen 3.
        """

        try:
            # --- CORRECCIÓN AQUÍ ---
            # En lugar de usar types.GenerateImageConfig(...), usamos un diccionario simple.
            # Esto evita el error "has no attribute 'GenerateImageConfig'"
            config_dict = {
                "number_of_images": number_of_images,
                "aspect_ratio": aspect_ratio,
                "safety_filter_level": "block_low_and_above",
                "person_generation": "allow_adult"
            }

            # Llamada a la API pasando el diccionario 'config'
            response = self.client.models.generate_images(
                model=model,
                prompt=prompt,
                config=config_dict
            )

            # Verificamos si hay imagen generada
            if not response.generated_images:
                raise ImageGenerationError("La API no devolvió ninguna imagen.")

            # Extraemos los bytes de la primera imagen
            image_bytes = response.generated_images[0].image.image_bytes

            if return_base64:
                return base64.b64encode(image_bytes).decode('utf-8')
            else:
                return base64.b64encode(image_bytes).decode('utf-8')

        except Exception as e:
            # Imprimimos el error completo para debug si vuelve a fallar
            print(f"DEBUG - Error detallado: {e}") 
            raise ImageGenerationError(f"Error generando imagen con Google: {str(e)}") from e

    def save_base64_image(self, b64_data: str, file_path: str) -> None:
        """
        Guarda una imagen base64 en disco.
        """
        try:
            image_bytes = base64.b64decode(b64_data)
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
             raise ImageGenerationError(f"Error guardando imagen en disco: {str(e)}") from e
import os
import sys

# Asegurar que el directorio raíz esté en el path para importar service
# Se asume que la clase ImageGenerator modificada para Google está en service/generator_image.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.generator_image import ImageGenerator

def main():
    # Prompt proporcionado (Sigue siendo excelente para Imagen 3 Pro debido a su realismo)
    prompt = (
        "Fotografía documental realista de alta resolución (estilo National Geographic). "
        "Plano medio de una mujer real de rasgos mestizos y piel trigueña clara con textura natural (poros visibles, sin filtros de belleza). "
        
        "RASGOS: Ojos almendrados oscuros con maquillaje dorado y negro, cejas tupidas marrón oscuro. "
        "Nariz recta, pómulos con rubor, labios carnosos rosa fucsia sonriendo levemente (dientes visibles). "
        "En la frente: un punto amarillo decorativo y un lunar pequeño debajo. "
        "Cabello largo negro y liso cayendo sobre los hombros. "
        
        "ENTORNO (FONDO VISIBLE): La mujer está parada en un mercado de artesanías tradicional al aire libre durante el día. "
        "Detrás de ella, se distinguen claramente estantes de madera rústica exhibiendo artesanías locales: "
        "se ven cántaros de cerámica (barro), termos forrados en cuero y textiles coloridos colgando. "
        "La luz es natural y difusa, filtrada por un techo alto o toldo de mercado. "
        
        "TÉCNICA: Profundidad de campo media (f/5.6) para que el fondo esté ligeramente desenfocado pero los objetos (artesanías) sean perfectamente identificables, integrando a la persona en el lugar."
    )

    try:
        # --- CAMBIO 1: Inicialización con la Google API Key ---
        # He puesto la clave que proporcionaste en el ejemplo.
        # Recordatorio de seguridad: Es mejor usar os.getenv("GOOGLE_API_KEY") en producción.
        generator = ImageGenerator(api_key="AIzaSyCO1Ft3EsyTGRZ6JSlJh7RhaEmaSYDl1I0")
        
        # --- CAMBIO 2: Actualización del mensaje ---
        print("Generando imagen con Google Imagen 3 (Nano Banana Pro)...")
        
        # --- CAMBIO 3: Adaptación de parámetros de 'generate' ---
        # DALL-E 3 usa 'size' y 'quality'. Google usa 'model' y 'aspect_ratio'.
        base64_result = generator.generate(
            prompt=prompt,
            model="imagen-4.0-generate-001", # El ID de Imagen 4
            aspect_ratio="1:1",              # Reemplaza a size="1024x1024"
            return_base64=True               # Google siempre devuelve Base64, mantenemos compatibilidad
            # 'quality' ya no es necesario, Imagen 3 Pro es alta calidad por defecto.
        )
        
        output_filename = "generated_profile.png"
        print(f"Guardando imagen en {output_filename}...")
        
        # Esta función sigue funcionando igual porque maneja datos Base64 estándar.
        generator.save_base64_image(base64_result, output_filename)
        
        print("¡Imagen generada exitosamente con la tecnología de Google!")

    except Exception as e:
        # Captura la excepción personalizada 'ImageGenerationError' definida en el otro módulo.
        print(f"Error al generar la imagen: {e}")

if __name__ == "__main__":
    main()
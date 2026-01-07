import asyncio
import json
import os
import random
from playwright.async_api import async_playwright
from search.search import Search
from create_account.create_account_x import XAccountCreator

# Configuración de selectores para X (Twitter)
# Estos selectores son ejemplos y podrían necesitar ajustes según la versión actual de X
HTML_SELECTORS = {
    # Selector para el botón de "Crear cuenta" en la home
    "create_account_button": "a[href='/i/flow/signup'], [data-testid='signupButton'], div[role='button']:has-text('Crear cuenta')",
    
    "perform_fill_form": {
        "name": "input[name='name']",
        "email": "input[name='email']",
        # Selectores para fecha de nacimiento (Revertido a IDs generados por X ya que data-testid estaba vacío)
        "month": "#SELECTOR_1", 
        "day": "#SELECTOR_2",
        "year": "#SELECTOR_3",
        # Botón siguiente
        "next_button_1": "[data-testid='ocfSignupNextLink'], div[role='button']:has-text('Siguiente')"
    }
}

def load_unique_users(file_path):
    """Carga usuarios desde JSON y elimina duplicados por email."""
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no existe.")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
            
        # Deduplicación por email
        unique_users = {}
        duplicates = 0
        for user in users:
            email = user.get('email')
            if email:
                if email not in unique_users:
                    unique_users[email] = user
                else:
                    duplicates += 1
        
        print(f"Usuarios cargados: {len(users)}")
        print(f"Duplicados eliminados: {duplicates}")
        print(f"Usuarios únicos a procesar: {len(unique_users)}")
        
        return list(unique_users.values())
    except Exception as e:
        print(f"Error leyendo el archivo JSON: {e}")
        return []

def save_generated_account(user_data, file_path="cuentas_generadas.json"):
    """Guarda la cuenta generada exitosamente en un archivo JSON."""
    try:
        accounts = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    content = f.read()
                    if content.strip():
                        accounts = json.loads(content)
                except json.JSONDecodeError:
                    pass
        
        # Verificar si ya existe para no duplicar
        if not any(acc.get('email') == user_data.get('email') for acc in accounts):
            accounts.append(user_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(accounts, f, indent=4, ensure_ascii=False)
            print(f"[INFO] Cuenta {user_data.get('email')} guardada en {file_path}")
        else:
            print(f"[INFO] La cuenta {user_data.get('email')} ya estaba en {file_path}")
            
    except Exception as e:
        print(f"[ERROR] No se pudo guardar la cuenta en {file_path}: {e}")

async def process_user(user_data):
    """Ejecuta el proceso de creación de cuenta para un solo usuario."""
    print(f"\n>>> Procesando usuario: {user_data.get('email')} <<<")
    
    #try:
        #cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")
        #if os.path.exists(cookies_path):
            #os.remove(cookies_path)
            #print("Archivo cookies.json eliminado correctamente.")
    #except Exception as e:
                #pass

    # 1. Configurar búsqueda (headless=False para ver lo que pasa)
    # check_ip=True verificará la IP antes de empezar
    search = Search(headless=False, check_ip=True) 
    
    async with async_playwright() as p:
        browser_manager = None
        browser = None
        context = None
        page = None
                    # Eliminar cookies.json si existe para limpiar sesión

        
        try:
            print("1. Abriendo navegador y buscando 'x.com'...")
            
            # 2. Buscar y navegar a X
            browser_manager, browser, context, page = await search.search_and_navigate(
                p, 
                search_term="x.com", 
                expected_domain="x.com"
            )
            
            print("2. Navegación a X completada.")
            print("3. Iniciando flujo de creación de cuenta...")
            
            # 3. Inicializar creador de cuentas con la página ya abierta
            creator = XAccountCreator(page=page)
            
            # 4. Ejecutar proceso de creación
            result = await creator.create_account(
                user_data=user_data,
                html_selectors=HTML_SELECTORS,
                wait_for_captcha=True
            )
            
            print(f"--- Resultado para {user_data.get('email')}: {result} ---")

            # Si la cuenta se creó exitosamente, borrar cookies.json
            if result.get("add_account") is True:
                save_generated_account(user_data)
                try:
                    cookies_path = "cookies.json"
                    if os.path.exists(cookies_path):
                        os.remove(cookies_path)
                        print(f"[INFO] Cuenta creada exitosamente. Archivo {cookies_path} eliminado para limpiar sesión.")
                except Exception as e:
                    print(f"[WARN] No se pudo eliminar {cookies_path}: {e}")
            
        except Exception as e:
            print(f"!!! Error durante la ejecución para {user_data.get('email')}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 5. Cerrar navegador limpiamente
            if browser_manager:
                print("Cerrando navegador...")
                await browser_manager.close_browser(browser, context)
        

async def main():
    json_file = "perfiles_generados.json"
    users = load_unique_users(json_file)
    
    if not users:
        print("No hay usuarios para procesar.")
        return

    for i, user in enumerate(users):
        await process_user(user)
        
        # Si no es el último usuario, esperar un intervalo aleatorio
        if i < len(users) - 1:
            wait_seconds = random.randint(5, 15)
            print(f"\n[ESPERA] Esperando {wait_seconds} segundos antes del siguiente usuario...")
            await asyncio.sleep(wait_seconds)

if __name__ == "__main__":
    asyncio.run(main())

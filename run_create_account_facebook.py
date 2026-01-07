import asyncio
import random
import json
import os
import re
from playwright.async_api import async_playwright
from search.search import Search
from search.redis_session_manager import RedisSessionManager
from service.api_Mailu import MailuClient
from logs.logs import Logger

PROFILES_FILE = 'perfiles_generados.json'
COOKIES_FILE = 'cookies.json'

# Instancia global del manager de Redis
redis_manager = RedisSessionManager()

def load_profiles():
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando perfiles: {e}")
        return []

def save_profiles(profiles):
    try:
        # Guardado atómico para evitar corrupción si se detiene el script
        temp_file = PROFILES_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=4, ensure_ascii=False)
        
        # Reemplazar archivo original solo si el volcado fue exitoso
        if os.path.exists(PROFILES_FILE):
            os.remove(PROFILES_FILE)
        os.rename(temp_file, PROFILES_FILE)
    except Exception as e:
        print(f"Error guardando perfiles: {e}")

def delete_session_data(email=None):
    # Limpieza de archivos legacy
    files_to_delete = [
        COOKIES_FILE, 
        'profile.json', 
        'session_data/cookies.json', 
        'session_data/profile.json'
    ]
    
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error eliminando {file_path}: {e}")

    # Limpieza de sesión en Redis
    if email:
        try:
            redis_manager.clear_session(email)
            print(f"Sesión Redis eliminada para {email}")
        except Exception as e:
            print(f"Error limpiando sesión Redis: {e}")

async def human_type(page, selector, text):
    """Escribe texto letra por letra con retardos variables para simular humano."""
    if not text:
        return
    try:
        # Asegurar foco
        await page.click(selector)
        for char in text:
            await page.keyboard.type(char)
            # Retardo aleatorio entre 50ms y 150ms
            await page.wait_for_timeout(random.uniform(50, 150))
        # Pequeña pausa al terminar un campo
        await page.wait_for_timeout(random.uniform(500, 1000))
    except Exception as e:
        print(f"Error escribiendo en {selector}: {e}")
        raise

async def check_for_registration_errors(page):
    print("Verificando posibles errores de registro...")
    for _ in range(20):
        if await page.is_visible("#reg_error"):
            error_text = await page.inner_text("#reg_error_inner")
            print(f"Error detectado: {error_text}")
            raise Exception(f"Fallo en registro: {error_text}")
        await page.wait_for_timeout(500)

async def fill_registration_form(page, profile):
    """Llena el formulario de registro con los datos del perfil."""
    print("Esperando formulario de registro...")
    await page.wait_for_selector("input[name='firstname']", timeout=10000)
    
    full_name = profile.get('name', '')
    parts = full_name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""
    
    print("Llenando formulario...")
    
    await human_type(page, "input[name='firstname']", first_name)
    await human_type(page, "input[name='lastname']", last_name)
    
    email = profile.get('email', '')
    await human_type(page, "input[name='reg_email__']", email)
    
    await page.wait_for_timeout(1000)
    if await page.is_visible("input[name='reg_email_confirmation__']"):
        print("Confirmando email...")
        await human_type(page, "input[name='reg_email_confirmation__']", email)
    
    password = profile.get('password', 'Pass12345!')
    await human_type(page, "input[name='reg_passwd__']", password)
    
    print("Seleccionando fecha de nacimiento...")
    day = str(int(profile.get('day', '1')))
    month = str(int(profile.get('month', '1')))
    year = str(profile.get('year', '2000'))
    
    await page.select_option("select[name='birthday_day']", day)
    await page.wait_for_timeout(random.uniform(300, 700))
    
    await page.select_option("select[name='birthday_month']", month)
    await page.wait_for_timeout(random.uniform(300, 700))
    
    await page.select_option("select[name='birthday_year']", year)
    await page.wait_for_timeout(random.uniform(300, 700))
    
    print("Seleccionando género...")
    gender_str = profile.get('gender', 'Hombre')
    gender_val = "2" if gender_str.lower() == "hombre" else "1"
    
    await page.click(f"input[name='sex'][value='{gender_val}']")
    
    print("Formulario completado.")

async def process_profile(profile, p, logger):
    print(f"--------------------------------------------------")
    print(f"Procesando perfil: {profile['name']} ({profile['email']})")
    
    # Usamos el email como session_id para Redis
    search = Search(headless=False, keep_open=False, session_id=profile['email'])
    browser_manager = None
    browser = None
    context = None
    page = None

    try:
        print("Iniciando búsqueda de facebook.com...")
        browser_manager, browser, context, page = await search.search_and_navigate(
            p, 
            search_term="facebook.com",
            expected_domain="facebook.com"
        )
        
        print("Click realizado en el primer resultado.")
        print("Esperando a que cargue la página de destino...")
        
        await page.wait_for_load_state("networkidle")
        
        wait_time = random.uniform(3, 5)
        print(f"Esperando {wait_time:.2f} segundos...")
        await page.wait_for_timeout(wait_time * 1000)

        # Manejo de Cookies (Importante para ver el botón e interactuar)
        cookie_selectors = [
            "button[data-testid='cookie-policy-manage-dialog-accept-button']",
            "text=Permitir todas las cookies",
            "text=Allow all cookies",
            "text=Aceptar todas",
            "button[title='Allow all cookies']",
            "[aria-label='Permitir todas las cookies']"
        ]
        for c_sel in cookie_selectors:
             try:
                 if await page.is_visible(c_sel):
                     print(f"Aceptando cookies ({c_sel})...")
                     await page.click(c_sel)
                     await page.wait_for_timeout(2000)
                     break
             except:
                 pass

        # Click en "Crear una cuenta"
        print("Haciendo click en 'Crear una cuenta'...")
        
        create_account_selectors = [
            "[data-testid='open-registration-form-button']",  # El estándar
            "a[role='button'][href*='/r.php']", # El que viene en el snippet del usuario
            "a[href*='/r.php']", # Genérico para link de registro
            "text=Crear cuenta nueva",
            "text=Create new account",
            "text=Registrarte",
            "div._6ltg a[role='button']" # Basado en la clase contenedora
        ]
        
        button_clicked = False
        for selector in create_account_selectors:
            try:
                if await page.is_visible(selector):
                    print(f"Botón encontrado ({selector}). Haciendo click...")
                    await page.click(selector)
                    button_clicked = True
                    break
            except Exception:
                continue

        if not button_clicked:
             # Maybe we are already on the form or different layout?
             print("Botón de registro no encontrado con selectores. Verificando si ya estamos en el formulario...")

        await fill_registration_form(page, profile)

        print("Haciendo click en 'Registrarte'...")
        await page.click("button[name='websubmit']")

        await check_for_registration_errors(page)

        print("Esperando correo de confirmación...")
        
        mailu = MailuClient("https://cabichui.com","40a18bd7a1a66d153bbb707ca2446625")
        max_retries = 30 
        email_found = False
        confirmation_code = None
        
        for i in range(max_retries):
            print(f"Verificando bandeja de entrada... (Intento {i+1}/{max_retries})")
            try:
                email = profile.get('email', '')
                password_email = profile.get('password', '')
                response = mailu.read_emails(email, password_email, limit=1)
                
                messages = []
                if isinstance(response, list):
                    messages = response
                elif isinstance(response, dict):
                    if 'emails' in response:
                        messages = response['emails']
                    elif 'messages' in response:
                        messages = response['messages']
                    elif 'data' in response:
                        messages = response['data']
                
                if messages:
                    latest_msg = messages[0]
                    body = latest_msg.get('body', 'Sin contenido')
                    
                    match = re.search(r'FB-(\d+)', body)
                    if match:
                        confirmation_code = match.group(1)
                        print(f"Código extraído: {confirmation_code}")
                        email_found = True
                        break
            except Exception as e:
                print(f"Excepción verificando correo: {e}")
            
            await asyncio.sleep(5)
        
        if email_found and confirmation_code:
            print("Ingresando código de confirmación...")
            await page.wait_for_selector("input[name='code']", state="visible", timeout=30000)
            await human_type(page, "input[name='code']", confirmation_code)
            print("Código ingresado correctamente.")

            print("Haciendo click en 'Continuar'...")
            await page.click("button[name='confirm']")

            # Manejo de botón "Continuar" adicional que a veces aparece
            try:
                print("Verificando si aparece segundo botón 'Continuar'...")
                await page.wait_for_timeout(3000)
                secondary_continue = "div[aria-label='Continuar'][role='button']"
                if await page.is_visible(secondary_continue):
                    print("Botón 'Continuar' secundario detectado. Haciendo click...")
                    await page.click(secondary_continue)
                    await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"No se detectó segundo botón Continuar: {e}")

            print("Esperando botón 'Aceptar'...")
            accept_selector = "a[role='button'].layerCancel.uiOverlayButton"
            try:
                await page.wait_for_selector(accept_selector, timeout=30000)
                await page.click(accept_selector)
                print("Click en 'Aceptar' realizado.")
            except:
                print("No se encontró botón Aceptar o ya se redirigió.")

            print("Cuenta creada exitosamente. Esperando 10 segundos antes de continuar...")
            await asyncio.sleep(35)

            # Success!
            return True

        elif not email_found:
            print("No se encontró el correo de confirmación.")
            raise Exception("Timeout esperando correo de confirmación")

    except Exception as e:
        print(f"Error procesando perfil {profile['email']}: {e}")
        raise e
    finally:
        if browser_manager and browser and context:
            await browser_manager.close_browser(browser, context)

async def main():
    profiles = load_profiles()
    if not profiles:
        print("No hay perfiles para procesar.")
        return

    logger = Logger(platform="facebook")

    processed_count = 0
    success_count = 0
    failure_count = 0

    async with async_playwright() as p:
        for i, profile in enumerate(profiles):
            # Check if already processed (Robust check)
            account_info = profile.get("account", {})
            fb_status = account_info.get("facebook")
            
            # Convierte a string y minúsculas para comparar (maneja 'True', 'true', True, etc.)
            if str(fb_status).lower() == "true":
                # print(f"Saltando perfil ya procesado: {profile.get('email')}")
                continue
            
            processed_count += 1
            print(f"\n>>> INICIO PROCESO #{processed_count} | Exitosos: {success_count} | Fallidos: {failure_count}")

            try:
                success = await process_profile(profile, p, logger)
                
                if success:
                    success_count += 1
                    # Update profile in memory
                    if "account" not in profile:
                        profile["account"] = {}
                    
                    profile["account"]["facebook"] = "True"
                    profile["account"]["twitter"] = "False"
                    
                    # Save all profiles to disk
                    save_profiles(profiles)
                    
                    logger.log_action(profile['email'], "create_account_facebook", "success")
                    print(f"Perfil {profile['email']} actualizado y guardado.")
                    print(f">>> ESTADO ACTUAL: Procesados: {processed_count} | Exitosos: {success_count} | Fallidos: {failure_count}")
                    delete_session_data(profile['email'])
                    
            except Exception as e:
                failure_count += 1
                logger.log_action(profile['email'], "create_account_facebook", "failed", str(e))
                delete_session_data(profile['email'])
                print(f">>> ESTADO ACTUAL: Procesados: {processed_count} | Exitosos: {success_count} | Fallidos: {failure_count}")
                print("Pasando al siguiente perfil...")
                continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCerrando...")

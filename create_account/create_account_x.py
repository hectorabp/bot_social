import asyncio
import time
import random
import re
from search.browser import BrowserManager
from playwright.async_api import async_playwright
from service.api_Mailu import MailuClient
from logs.logs import Logger


class XAccountCreator:
    """Manejador de creación de cuentas en X.

    Ahora permite inicializar sin una `page` y ofrece el método
    `open_browser_and_create` que abre Playwright/BrowserManager internamente,
    navega a la URL indicada y ejecuta el flujo de creación de cuenta sin
    depender de `search.py`.
    """
    def __init__(self, page=None):
        self.page = page
        self.mailu_client = MailuClient("https://cabichui.com","40a18bd7a1a66d153bbb707ca2446625")
        self.logger = Logger("x")



    async def smooth_move_to_element(self, locator):
        try:
            # Mover directamente al elemento
            await locator.hover()
            await self.page.wait_for_timeout(random.uniform(200, 500))
            return
        except Exception as e:
            print(f"Error en smooth_move_to_element: {e}")
            raise

    async def detect_bot_error(self, email, html_selectors_fill_form, check_verification_loop=False):
        print("[info] Ejecutando detección de errores de bot (30 intentos)...")
        for i in range(30):
            # 1. Popup Error
            try:
                human_error_popup = self.page.locator("[data-testid='confirmationSheetDialog']")
                if await human_error_popup.count() > 0 and await human_error_popup.is_visible():
                    popup_text = await human_error_popup.inner_text()
                    popup_text_lower = popup_text.lower()

                    if "unable to confirm you're human" in popup_text_lower:
                        print("[error] Se detectó el popup: 'We were unable to confirm you're human'.")
                        self.logger.log_action(email, "human_verification_failed", status=[{"add_account":False},{"bot_detected":True}], observations="Fallo confirmación humana (popup detectado).")
                        return {"status": True, "error": "HUMAN_VERIFICATION_FAILED_POPUP"}
                    
                    if "superaste el número de intentos permitidos" in popup_text_lower:
                        print("[error] Se detectó el popup: 'Superaste el número de intentos permitidos'.")
                        self.logger.log_action(email, "attempts_exceeded", status=[{"add_account":False},{"bot_detected":True}], observations="Superaste el número de intentos permitidos.")
                        return {"status": True, "error": "ATTEMPTS_EXCEEDED_POPUP"}

                    if "error" in popup_text_lower or "algo salió mal" in popup_text_lower:
                        print(f"[error] Se detectó un popup de error genérico: {popup_text}")
                        self.logger.log_action(email, "generic_error_popup", status=[{"add_account":False},{"bot_detected":True}], observations=f"Error genérico: {popup_text}")
                        return {"status": True, "error": "GENERIC_ERROR_POPUP"}
            except: pass

            # 2. Retorno a Formulario Registro
            try:
                name_input = self.page.locator(html_selectors_fill_form.get("name"))
                if await name_input.count() > 0 and await name_input.is_visible():
                    print("[error] Se detectó retorno al formulario de registro.")
                    self.logger.log_action(email, "returned_to_form", status=[{"add_account":False},{"bot_detected":True}], observations="Regresó al formulario inicial.")
                    return {"status": True, "error": "RETURNED_TO_REGISTRATION_FORM"}
            except: pass

            # 3. Loop en Verificación (Solo si se solicita chequear)
            if check_verification_loop:
                try:
                    verif_input = self.page.locator("input[name='verification_code'], input[name='verfication_code']")
                    if await verif_input.count() > 0 and await verif_input.is_visible():
                        # Si aparece, asumimos error/loop
                        print("[error] Se detectó bucle en código de verificación.")
                        self.logger.log_action(email, "verification_loop", status=[{"add_account":False},{"bot_detected":True}], observations="Bucle en código de verificación.")
                        return {"status": True, "error": "VERIFICATION_CODE_LOOP"}
                except: pass
            
            await asyncio.sleep(1)
        
        return {"status": False}

    async def perform_signup(self,create_account_button_select):
        try:
            # Esperar a que cargue la página de X y hacer clic en "Crear cuenta"
            await self.page.wait_for_timeout(random.uniform(3000, 5000))
            # Agregar scroll para simular navegación humana
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight / 4);")
            await self.page.wait_for_timeout(random.uniform(1000, 3000))
            await self.page.evaluate("window.scrollTo(0, 0);")
            await self.page.wait_for_timeout(random.uniform(1000, 3000))
            await self.page.wait_for_selector(create_account_button_select, timeout=20000)
            create_account_button = self.page.locator(create_account_button_select)
            # Hacer scroll al elemento
            await create_account_button.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(random.uniform(5000, 10000))
            # Usar click directo
            print("[info] Usando click directo en create_account_button")
            await create_account_button.click()
            print("[info] Se hizo clic en 'Crear cuenta'.")
        except Exception as e:
            print(f"Error en perform_signup: {e}")
            raise

    async def perform_fill_form(self, user_data, html_selectors, retry_count=0, wait_for_captcha=True):
        try:
            if user_data is None:
                return {"status": False, "message": "[USER_DATA_NOT_PROVIDED]"}
            
            email = user_data['email']
            password = user_data['password']
            
            self.logger.log_action(email, "add_account", observations="Iniciando llenado de formulario")
            
            # Primero: comprobar si hay un modal de error
            try:
                modal_span = self.page.locator("//div[contains(@class, 'css-175oi2r')]//span[contains(text(), 'Algo salió mal. Intenta recargar.')]")
                await modal_span.wait_for(timeout=3000)
                # Si llegamos aquí, el modal está presente
                print("[info] Pop-up de error detectado (comprobación inicial).")
                self.logger.log_action(email,"error_popup_detected", observations="Pop-up de error detectado al llenar formulario")


                # Intentar encontrar y clickear el botón "Intentar de nuevo"
                try:
                    retry_button = self.page.locator("//div[contains(@class, 'css-175oi2r')]//button[.//span[contains(text(), 'Intentar de nuevo')]]")
                    await retry_button.wait_for(timeout=10000)
                    print("[info] Botón 'Intentar de nuevo' encontrado. Haciendo click.")
                    self.logger.log_action(email, "boton_intentar_de_nuevo", observations="Botón 'Intentar de nuevo' encontrado.")

                    await retry_button.click()
                except Exception as e:
                    print(f"[error] Botón 'Intentar de nuevo' no encontrado o no clickeable: {e}")
                    print("[error] Fallo al encontrar o clickear 'Intentar de nuevo' — terminando ejecución.")
                    self.logger.log_action(email, "boton_intentar_de_nuevo", observations="Botón 'Intentar de nuevo' no encontrado o no clickeable")                    
                    return {"status": False, "add_account": False, "message": "[ERROR_POPUP_DETECTED_AND_RETRY_BUTTON_NOT_FOUND]"}

                # Esperar un poco
                await self.page.wait_for_timeout(random.uniform(3000, 5000))

                # Si aún no hemos reintentado, volver a intentar una vez
                if retry_count < 1:
                    print("[info] Reintentando el llenado del formulario (intentando una vez más)...")
                    self.logger.log_action(email, "completar_formulario", observations="Reintentando el llenado del formulario (intentando una vez más)")                                       
                    await self.perform_fill_form(user_data, retry_count + 1, wait_for_captcha)
                    return
                else:
                    print("[error] Pop-up de error detectado en el segundo intento. Terminando ejecución.")
                    self.logger.log_action(email, "error_popup_detected_twice", observations="Pop-up de error detectado dos veces al llenar formulario")
                    return {"status": False, "message": "[ERROR_POPUP_DETECTED_TWICE]"}
            except:
                # No había modal; continuar normalmente
                pass

            html_selectors_fill_form = html_selectors.get("perform_fill_form", {})
            # Esperar a que aparezca el formulario
            await self.page.wait_for_selector(html_selectors_fill_form.get("name"), timeout=10000)
            
            # Llenar formulario de login
            if not await self.complete_form_login(html_selectors_fill_form, user_data):
                return {"status": False, "message": "[ERROR_FILLING_FORM]"}
            self.logger.log_action(email, "completar_formulario", observations="Formulario completado")

            await self.page.wait_for_timeout(random.uniform(5000, 10000))  # Esperar a que se habilite el botón

            # Esperar a que el botón esté habilitado
            await self.page.wait_for_function("!document.querySelector('button[data-testid=\"ocfSignupNextLink\"]').disabled", timeout=30000)

            # Hacer clic en Siguiente
            next_button = self.page.locator(html_selectors_fill_form.get("next_button_1"))
            await self.smooth_move_to_element(next_button)
            await next_button.click()
            print("[info] Se hizo clic en 'Siguiente'.")
            self.logger.log_action(email, "boton_siguente", observations="Click en primer botón siguiente")
            bot_error = await self.detect_bot_error(email, html_selectors_fill_form, check_verification_loop=False)
            if bot_error["status"]:
                return {"status": False, "message": bot_error["error"]}
            
            # Esperar y verificar si aparece CAPTCHA
            await self.page.wait_for_timeout(random.uniform(5000, 10000))
            if await self.page.locator("#arkoseFrame").count() > 0:
                if wait_for_captcha:                
                    # Verificar si aparece el spinner de carga después del CAPTCHA
                    spinner_selector = "div[role='progressbar'][aria-valuemax='1'][aria-valuemin='0']"
                    start_time = time.time()
                    while time.time() - start_time < 10:
                        if await self.page.locator(spinner_selector).count() == 0:
                            break
                        await asyncio.sleep(1)
                    else:
                        self.logger.log_action(email, "spinner_timeout", observations="Spinner de carga detectado por más de 10 segundos.")
                        return {"status": False, "message": "Spinner de carga detectado por más de 10 segundos. Deteniendo ejecución."}

                    self.logger.log_action(email, "captcha_detectado", observations="Captcha detectado, esperando resolución manual")
                    print("[info] Esperando resolución de CAPTCHA (buscando campo de verificación)...")
                    
                    verification_input_selector = "input[name='verification_code'], input[name='verfication_code']"
                    captcha_solved = False
                    for _ in range(300):
                        if await self.page.locator(verification_input_selector).count() > 0:
                            if await self.page.locator(verification_input_selector).is_visible():
                                print("[info] Campo de verificación detectado. CAPTCHA resuelto.")
                                captcha_solved = True
                                break
                        await asyncio.sleep(2)
                    
                    if not captcha_solved:
                        self.logger.log_action(email, "captcha_timeout", observations="Tiempo de espera de CAPTCHA agotado.")
                        return {"status": False, "message": "Tiempo de espera de CAPTCHA agotado."}
                    
                    # --- Detección de errores post-CAPTCHA ---
                    # Aquí NO chequeamos loop de verificación porque esperamos que aparezca el input
                    bot_error = await self.detect_bot_error(email, html_selectors_fill_form, check_verification_loop=False)
                    if bot_error["status"]:
                        return {"status": False, "message": bot_error["error"]}

                else:
                    self.logger.log_action(email, "captcha_detectado", observations="Captcha detectado, deteniendo ejecución")
                    return {"status": False, "message": "CAPTCHA detectado. Deteniendo ejecución."}
            try:
                # X a veces tiene un typo en el nombre del campo: 'verfication_code' en lugar de 'verification_code'
                verification_input = self.page.locator("input[name='verification_code'], input[name='verfication_code']")
                await verification_input.wait_for(timeout=30000)
                
                verification_code = await self.find_verification_code(email, password)

                if not verification_code:
                    self.logger.log_action(email, "verificacion_codigo", observations="No se encontró el código automáticamente.")
                    print(f"[DEBUG] No se encontró el código automáticamente.")
                    # Pedir el código al usuario como fallback
                    verification_code = input("Ingresa el código de verificación: ")
                # Esperar un poco
                await self.page.wait_for_timeout(random.uniform(1000, 3000))        
                # Enviar letra por letra
                await self.page.keyboard.type(verification_code, delay=random.uniform(200, 450))
                        
                # Esperar un poco
                await self.page.wait_for_timeout(random.uniform(1000, 3000))
                        
                # Hacer clic en Siguiente
                next_button = self.page.locator("//button[.//span[contains(text(), 'Siguiente')]]")
                await next_button.click()
                print("[info] Código enviado y clic en Siguiente.")

                # Esperar un poco para que la UI reaccione antes de chequear errores
                await self.page.wait_for_timeout(2000)

                # --- Detección de errores post-código ---
                # Aquí SI chequeamos loop de verificación porque ya deberíamos haber pasado esa pantalla
                bot_error = await self.detect_bot_error(email, html_selectors_fill_form, check_verification_loop=True)
                if bot_error["status"]:
                    return {"status": False, "add_account": False, "message": bot_error["error"]}

                # --- Llenado de contraseña ---
                print("[info] Esperando campo de contraseña...")
                password_input = self.page.locator("input[name='password']")
                await password_input.wait_for(timeout=30000)
                
                await self.smooth_move_to_element(password_input)
                await password_input.click()
                await self.page.keyboard.type(password, delay=random.uniform(100, 300))
                
                await self.page.wait_for_timeout(random.uniform(1000, 3000))
                
                # Clic en el botón final (suele ser "Registrarse" o "Siguiente")
                print("[info] Buscando botón final de registro (LoginForm_Login_Button)...")
                final_button = self.page.locator("[data-testid='LoginForm_Login_Button']").first
                
                # Fallback si no encuentra el ID específico
                if await final_button.count() == 0:
                    print("[info] Botón por ID no encontrado, buscando por texto...")
                    final_button = self.page.locator("//button[not(@disabled) and .//span[contains(text(), 'Registrarse') or contains(text(), 'Siguiente')]]").first

                await final_button.wait_for(timeout=15000)
                await final_button.scroll_into_view_if_needed()
                await final_button.click()
                print("[info] Contraseña ingresada y formulario finalizado.")

                # --- Post-registro: Descartar avatar ---
                try:
                    print("[info] Esperando botón 'Descartar por ahora' (Avatar)...")
                    skip_avatar_button = self.page.locator("[data-testid='ocfSelectAvatarSkipForNowButton']")
                    # Damos un tiempo razonable para que cargue la siguiente pantalla
                    await skip_avatar_button.wait_for(timeout=20000)
                    await skip_avatar_button.click()
                    print("[info] Se hizo clic en 'Descartar por ahora' (Avatar).")
                except Exception as e:
                    print(f"[info] No se encontró o no fue necesario el botón de descartar avatar: {e}")

                # --- Post-registro: Nombre de usuario ---
                # Si tenemos un username en user_data, lo usamos. Si no, intentamos pasar con el predeterminado si aparece la pantalla.
                username = user_data.get('username')
                try:
                    # Verificamos si aparece el input de username
                    username_input = self.page.locator("input[name='username']")
                    if await username_input.count() > 0 or await username_input.is_visible(timeout=5000):
                        print("[info] Pantalla de nombre de usuario detectada.")
                        if username:
                            print(f"[info] Estableciendo nombre de usuario: {username}")
                            await self.smooth_move_to_element(username_input)
                            
                            # Método más robusto para borrar el contenido
                            await username_input.click()
                            await username_input.fill("") # Intentar vaciar directamente
                            
                            # Asegurar borrado si fill no funcionó (a veces X lo restaura)
                            current_value = await username_input.input_value()
                            if current_value:
                                await username_input.press("Control+A")
                                await username_input.press("Backspace")
                            
                            # Escribir el nuevo usuario
                            await username_input.type(username, delay=random.uniform(100, 300))
                        else:
                            print("[info] No se proporcionó 'username' en user_data. Se mantendrá el sugerido por X.")
                        
                        # Clic en Siguiente (para confirmar el usuario)
                        next_btn_user = self.page.locator("[data-testid='ocfEnterUsernameNextButton']").first
                        await next_btn_user.wait_for(timeout=5000)
                        await next_btn_user.click()
                        print("[info] Clic en Siguiente (Username).")
                except Exception as e:
                    print(f"[info] No se detectó o no fue necesario el paso de nombre de usuario: {e}")

                # --- Post-registro: Descartar notificaciones (segundo 'Descartar por ahora') ---
                try:
                    print("[info] Esperando segundo botón 'Descartar por ahora'...")
                    # Buscamos el botón por su texto ya que no tiene data-testid
                    skip_notifications_button = self.page.locator("//button[.//span[contains(text(), 'Descartar por ahora')]]").first
                    # Esperamos hasta 10s a que aparezca
                    await skip_notifications_button.wait_for(timeout=10000)
                    await skip_notifications_button.click()
                    print("[info] Se hizo clic en 'Descartar por ahora' (Notificaciones).")
                except Exception as e:
                    print(f"[info] No se encontró o no fue necesario el segundo botón de descartar: {e}")

                # --- Post-registro: Selección de Intereses (3 temas) ---
                try:
                    print("[info] Esperando selección de intereses (3 temas)...")
                    # Esperamos a que aparezcan los elementos de la lista
                    # Usamos un selector que coincida con los botones dentro de los items de la lista
                    interest_buttons = self.page.locator("li[role='listitem'] button")
                    await interest_buttons.first.wait_for(timeout=15000)
                    
                    count = await interest_buttons.count()
                    print(f"[info] Se encontraron {count} temas disponibles.")
                    
                    # Seleccionar los primeros 3 (o menos si hay menos)
                    clicks_needed = 3
                    clicked = 0
                    for i in range(count):
                        if clicked >= clicks_needed:
                            break
                        try:
                            btn = interest_buttons.nth(i)
                            if await btn.is_visible():
                                await btn.click()
                                await self.page.wait_for_timeout(random.uniform(500, 1000))
                                clicked += 1
                        except Exception as e:
                            print(f"[warn] No se pudo clickear el interés {i}: {e}")
                    
                    print(f"[info] Se seleccionaron {clicked} temas.")

                    # Clic en Siguiente después de seleccionar temas
                    next_btn_interests = self.page.locator("//button[not(@disabled) and .//span[contains(text(), 'Siguiente')]]").first
                    await next_btn_interests.wait_for(timeout=5000)
                    await next_btn_interests.click()
                    print("[info] Clic en Siguiente (Intereses).")

                except Exception as e:
                    print(f"[info] No se detectó o no fue necesario el paso de intereses: {e}")

                # --- Post-registro: Seguir cuentas sugeridas y Siguiente ---
                try:
                    print("[info] Esperando lista de cuentas sugeridas...")
                    # Esperamos un poco para asegurar que la transición de página ocurrió
                    await self.page.wait_for_timeout(random.uniform(2000, 4000))
                    
                    # Intentar seguir a 3 cuentas
                    try:
                        # Buscamos botones que contengan "Seguir" dentro de celdas de usuario
                        # Usamos un selector específico basado en el HTML proporcionado
                        follow_buttons = self.page.locator("[data-testid='UserCell'] button").filter(has_text="Seguir")
                        
                        # Esperar a que haya al menos uno visible
                        try:
                            await follow_buttons.first.wait_for(timeout=10000)
                            count = await follow_buttons.count()
                            print(f"[info] Se encontraron {count} botones de 'Seguir'.")
                            
                            clicks_needed = 3
                            clicked = 0
                            for i in range(count):
                                if clicked >= clicks_needed:
                                    break
                                try:
                                    btn = follow_buttons.nth(i)
                                    await btn.scroll_into_view_if_needed()
                                    if await btn.is_visible():
                                        await btn.click()
                                        print(f"[info] Se siguió a la cuenta {i+1}.")
                                        await self.page.wait_for_timeout(random.uniform(800, 1500))
                                        clicked += 1
                                except Exception as e:
                                    print(f"[warn] No se pudo seguir a la cuenta {i}: {e}")
                            print(f"[info] Se siguieron {clicked} cuentas.")
                        except:
                            print("[info] No se encontraron botones de 'Seguir' visibles a tiempo.")

                    except Exception as e:
                        print(f"[info] No se pudieron seguir cuentas (o no aparecieron): {e}")

                    # Clic en Siguiente
                    print("[info] Buscando botón 'Siguiente' final...")
                    # Usamos el data-testid específico: ocfURTUserRecommendationsNextButton
                    next_button_follows = self.page.locator("[data-testid='ocfURTUserRecommendationsNextButton']").first
                    
                    # Esperar un poco más por si el botón tarda en habilitarse o aparecer
                    try:
                        await next_button_follows.wait_for(timeout=10000)
                        await next_button_follows.click()
                        print("[info] Clic en Siguiente (Seguir cuentas).")
                    except Exception as e:
                        print(f"[warn] Falló el clic en Siguiente (ID específico): {e}")
                        # Fallback por texto
                        fallback = self.page.locator("//button[not(@disabled) and .//span[contains(text(), 'Siguiente')]]").first
                        if await fallback.is_visible(timeout=5000):
                            await fallback.click()
                            print("[info] Clic en Siguiente (Fallback Texto).")
                except Exception as e:
                    print(f"[info] No se encontró o no fue necesario el paso de seguir cuentas: {e}")

                self.logger.log_action(email, "add_account", status={"add_account":True},observations="Cuenta creada exitosamente.")
                return {"status": True, "add_account": True, "message": "Cuenta creada exitosamente."}
            except Exception as e:
                print(f"[error] Error en flujo de verificación/contraseña: {e}")
                print("[info] Campo de código de verificación no encontrado o error posterior.")
                
                # Verificar si regresó al formulario inicial (posible fallo de permisos/bloqueo)
                try:
                    print("[info] Verificando si retornó al formulario inicial...")
                    await self.page.wait_for_selector(html_selectors_fill_form.get("name"), timeout=10000)
                    print("[info] Formulario original detectado.")
                    self.logger.log_action(email, "add_account", status={"add_account":False},observations="Permisos no eludidos.")
                except:
                    pass

                raise Exception("VERIFICATION_CODE_FIELD_NOT_FOUND")
        except Exception as e:
            print(f"Error en perform_fill_form: {e}")
            raise

    async def create_account(self, user_data, html_selectors, retry_count=0, wait_for_captcha=True):
        try:

            await self.perform_signup(create_account_button_select=html_selectors.get("create_account_button"))
            result = await self.perform_fill_form(user_data, html_selectors, retry_count, wait_for_captcha=wait_for_captcha)
            return result
        except Exception as e:
            print(f"Error en create_account: {e}")
            return {"status": False, "message": f"EXCEPTION_OCCURRED: {e}"}

    async def open_browser_and_create(self, url, user_data, html_selectors, headless=True, wait_for_captcha=True):
        """
        Conveniencia: abre `async_playwright()` y usa `BrowserManager` para abrir
        la `page` en `url`, luego ejecuta `create_account` usando esa `page`.

        - url: URL a la que navegar (ej. 'https://www.x.com')
        - user_data, html_selectors: se pasan a `create_account`
        - headless: pasa al `BrowserManager`

        Este método se encarga de cerrar recursos (browser/context) al final.
        Devuelve el resultado de `create_account`.
        """
        async with async_playwright() as p:
            browser_manager = None
            browser = None
            context = None
            try:
                browser_manager = BrowserManager(headless=headless)
                # load_cookies=False para iniciar con sesión limpia y generar nuevo _twitter_sess
                browser, context, page = await browser_manager.open_browser(p, url, load_cookies=False)

                # Asignar la page a la instancia y ejecutar el flujo
                self.page = page
                result = await self.create_account(user_data, html_selectors, retry_count=0, wait_for_captcha=wait_for_captcha)
                return result
            except Exception as e:
                print(f"Error en open_browser_and_create: {e}")
                return {"status": False, "message": f"EXCEPTION_OCCURRED: {e}"}
            finally:
                if browser_manager and browser and context:
                    await browser_manager.close_browser(browser, context)

    async def complete_form_login(self, html_selectors_fill_form, user_data):
        try:
            name = user_data['name']
            email = user_data['email']
            month = user_data['month']
            day = user_data['day']
            year = user_data['year']

            # Llenar nombre
            name_input = self.page.locator(html_selectors_fill_form.get("name"))
            await self.smooth_move_to_element(name_input)
            await name_input.click()
            await self.page.keyboard.type(name, delay=random.uniform(100, 300))
            
            # Llenar correo
            email_input = self.page.locator(html_selectors_fill_form.get("email"))
            await self.smooth_move_to_element(email_input)
            await email_input.click()
            await self.page.keyboard.type(email, delay=random.uniform(100, 300))
            
            # Encontrar elementos de fecha
            date_input = self.page.locator("input[type='date']")
            if await date_input.count() > 0:
                date_value = f"{year}-{int(month):02d}-{int(day):02d}"
                await self.smooth_move_to_element(date_input)
                await date_input.fill(date_value)
            else:
                month_select = self.page.locator(html_selectors_fill_form.get("month"))
                day_select = self.page.locator(html_selectors_fill_form.get("day"))
                year_select = self.page.locator(html_selectors_fill_form.get("year"))

                # Calcular valor entero del mes (sin ceros a la izquierda)
                month_int = str(int(month)) # "10" -> "10", "04" -> "4"

                # Seleccionar fecha de nacimiento en orden aleatorio
                fields = [
                    ("month", month_select, month), # Pasamos 'month' original como referencia
                    ("day", day_select, day),
                    ("year", year_select, year)
                ]
                random.shuffle(fields)
                
                for field_name, locator, original_value in fields:
                    await self.smooth_move_to_element(locator)
                    
                    if field_name == "month":
                        # Lógica simplificada para el mes: Priorizar valor entero (sin ceros)
                        success = False
                        
                        # 1. Intentar por valor numérico entero (ej "4" en vez de "04")
                        try:
                            await locator.select_option(value=month_int)
                            success = True
                        except:
                            pass

                        # 2. Si falla, intentar por valor numérico original (ej "04")
                        if not success:
                            try:
                                await locator.select_option(value=original_value)
                                success = True
                                print(f"[DEBUG] Mes seleccionado por valor original: {original_value}")
                            except:
                                pass
                        
                        # 3. Si todo falla, imprimir opciones para debug
                        if not success:
                            print(f"[DEBUG] Fallo al seleccionar mes. Opciones disponibles:")
                            try:
                                options = await locator.locator("option").all_inner_texts()
                                print(options)
                                values = await locator.locator("option").evaluate_all("opts => opts.map(o => o.value)")
                                print(values)
                            except Exception as e:
                                print(f"[DEBUG] No se pudieron leer opciones: {e}")
                            raise Exception(f"No se pudo seleccionar el mes: {original_value} (int: {month_int})")

                    else:
                        # Para día y año, intentar valor directo o entero (sin ceros a la izquierda)
                        try:
                            await locator.select_option(original_value)
                        except:
                            try:
                                await locator.select_option(str(int(original_value)))
                            except:
                                # Debug si falla día o año
                                print(f"[DEBUG] Fallo al seleccionar {field_name}. Valor: {original_value}")
                                raise

                    await self.page.wait_for_timeout(random.uniform(500, 1500))
            
            return True
        except Exception as e:
            print(f"Error en complete_form_login: {e}")
            return False

    async def find_verification_code(self, email, password):
        verification_code = None
        # Intentar buscar el código automáticamente con reintentos
        for i in range(6):
            print(f"[info] Buscando correo de verificación (Intento {i+1}/6)...")
            mailing_list = self.mailu_client.read_emails(email, password, "INBOX", 10)
            print(f"[debug] Correos obtenidos: {mailing_list}")
            emails = mailing_list.get('emails', [])
            
            for mail in emails:
                # Filtrar por remitente info@x.com y asunto que contenga "verificación"
                sender = mail.get('from', '')
                subject = mail.get('subject', '')
                
                if "info@x.com" in sender and "verificación" in subject.lower():
                    # Buscar código de 6 dígitos en el asunto o cuerpo
                    # Priorizar asunto
                    match = re.search(r'\b\d{6}\b', subject)
                    if not match:
                        match = re.search(r'\b\d{6}\b', mail.get('body', ''))
                    
                    if match:
                        verification_code = match.group(0)
                        print(f"[info] Código de verificación encontrado automáticamente: {verification_code}")
                        return verification_code
            
            # Esperar antes del siguiente intento
            await asyncio.sleep(5)
        return None


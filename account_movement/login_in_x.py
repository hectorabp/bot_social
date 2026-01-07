from contextlib import asynccontextmanager
from playwright.async_api import async_playwright
import typing as t
import asyncio
import random

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from search.search import Search


class LoginInX:
    """Proporciona un context manager asíncrono que busca 'x.com' usando `Search`
    y devuelve (browser_manager, browser, context, page) listos para usar dentro
    del bloque `async with`.

    Uso:
        login = LoginInX(headless=False)
        async with login.session() as (browser_manager, browser, context, page):
            # interactuar con page

    El context manager se encarga de cerrar el navegador al salir del bloque.
    """

    def __init__(self, headless: bool = False):
        """headless: pasar al Search/BrowserManager"""
        self.search = Search(headless=headless)

    @asynccontextmanager
    async def session(self, search_term: str = "x.com", expected_domain: t.Optional[str] = "x.com", click_timeout: int = 10000, keep_open: bool = False, save_cookies: bool = True, login_email: t.Optional[str] = None, password: t.Optional[str] = None, username: t.Optional[str] = None, cookies_path: t.Optional[str] = "search/cookies/x"):
        """Context manager asíncrono que abre Playwright, navega por DuckDuckGo y
        hace clic en el primer resultado (esperando el dominio opcional).

        Devuelve una tupla: (browser_manager, browser, context, page)
        """
        p = await async_playwright().__aenter__()
        browser_manager = None
        browser = None
        context = None
        page = None
        try:
            # Propagar flags de cierre hacia Search/BrowserManager
            # Si se proporcionó username, usar un archivo de cookies específico por usuario
            effective_cookies_path = cookies_path
            if username:
                # cookies_path puede ser carpeta o archivo; si es carpeta, añadimos el nombre
                base = Path(cookies_path) if cookies_path else Path("search/cookies/x")
                if base.suffix.lower() == ".json":
                    effective_cookies_path = str(base.parent / f"cookies_{username}.json")
                else:
                    effective_cookies_path = str(base / f"cookies_{username}.json")
            username = f"@{username}"

            browser_manager, browser, context, page = await self.search.search_and_navigate(
                p,
                search_term,
                expected_domain,
                click_timeout,
                keep_open=keep_open,
                save_cookies=save_cookies,
                cookies_path=effective_cookies_path,
            )
            # Detectar si la sesión ya está activa (por cookies o redirección)
            logged_in = False
            try:
                cur_url = page.url
                # Si la página ya redirigió a /home es muy probable que estemos logueados
                if cur_url and "/home" in cur_url:
                    logged_in = True
                else:
                    # Revisar cookies por nombres típicos de sesión en X/twitter
                    try:
                        ck = await context.cookies()
                        auth_names = {"auth_token", "ct0", "twid", "personalization_id", "guest_id", "session"}
                        if any(c.get("name") in auth_names and c.get("value") for c in ck):
                            print("[+] Cookies indican posible sesión activa.")
                            # comprobar también si elementos de UI de usuario aparecen
                            try:
                                # selector genérico de área principal de timeline o avatar
                                await page.wait_for_selector("[aria-label*='Home'], a[aria-label*='Profile'], div[role='navigation']", timeout=2000)
                                logged_in = True
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                logged_in = False

            if logged_in:
                print("[+] Sesión detectada: se omitirá flujo interactivo de login (se cargó con cookies).")
            else:
                # Intentar clicar el botón de 'Iniciar sesión' si está presente en la página
                try:
                    login_selector = "a[data-testid='loginButton']"
                    await page.wait_for_selector(login_selector, timeout=8000)
                    login_btn = page.locator(login_selector)
                    await login_btn.scroll_into_view_if_needed()
                    await login_btn.click()
                    print("Se hizo clic en el botón 'Iniciar sesión'.")
                    # Pequeña espera para permitir la navegación o cambios DOM
                    await page.wait_for_timeout(1500)

                    # Si se proporcionó un email, intentar localizar la caja del popup y escribirlo
                    if login_email:
                        try:
                            # --- Inicio flujo interacción de login (email -> usuario -> contraseña) ---
                            group_sel = (
                                "input[type='text'], input[name='text'], input[placeholder*='Tel'], "
                                "input[placeholder*='correo'], input[aria-label*='Tel'], textarea, [role='textbox'], [contenteditable='true']"
                            )
                            await page.wait_for_selector(group_sel, timeout=8000)

                            # localizar el input visible
                            input_locator = None
                            locs = page.locator(group_sel)
                            count = await locs.count()
                            for i in range(count):
                                el = locs.nth(i)
                                try:
                                    if await el.is_visible():
                                        input_locator = el
                                        break
                                except Exception:
                                    continue

                            if input_locator is None:
                                raise Exception("Input de login no encontrado o no visible en el popup")

                            await input_locator.scroll_into_view_if_needed()
                            try:
                                await input_locator.focus()
                            except Exception:
                                await input_locator.click()

                            try:
                                await input_locator.fill("")
                            except Exception:
                                pass

                            for ch in login_email:
                                await page.keyboard.type(ch)
                                await page.wait_for_timeout(random.uniform(80, 220))
                            await page.wait_for_timeout(300)

                            # intentar avanzar con 'Siguiente'
                            next_btn = None
                            try:
                                cand = page.get_by_role("button", name="Siguiente")
                                await cand.wait_for(state="visible", timeout=2000)
                                next_btn = cand
                            except Exception:
                                next_btn = None

                            if not next_btn:
                                for sel in ["button:has-text('Siguiente')", "button >> text=Siguiente", "button[type='button'] >> text=Siguiente"]:
                                    try:
                                        loc = page.locator(sel)
                                        if (await loc.count()) > 0 and await loc.first.is_visible():
                                            next_btn = loc.first
                                            break
                                    except Exception:
                                        continue

                            if next_btn:
                                try:
                                    await next_btn.scroll_into_view_if_needed()
                                    try:
                                        enabled = await next_btn.is_enabled()
                                    except Exception:
                                        enabled = True
                                    if not enabled:
                                        await page.wait_for_timeout(500)
                                    await next_btn.click()
                                    print("Botón 'Siguiente' clickeado.")
                                except Exception as e:
                                    print(f"No se pudo clicar 'Siguiente': {e}")

                            # paso intermedio: posible input de usuario/telefono
                            try:
                                alt_sel = "input[name='text'], input[data-testid='ocfEnterTextTextInput']"
                                await page.wait_for_selector(alt_sel, timeout=3000)
                                alt_loc = None
                                alt_candidates = page.locator(alt_sel)
                                for i in range(await alt_candidates.count()):
                                    el = alt_candidates.nth(i)
                                    try:
                                        if await el.is_visible():
                                            alt_loc = el
                                            break
                                    except Exception:
                                        continue

                                if alt_loc:
                                    try:
                                        await alt_loc.scroll_into_view_if_needed()
                                        try:
                                            await alt_loc.focus()
                                        except Exception:
                                            await alt_loc.click()
                                        try:
                                            await alt_loc.fill("")
                                        except Exception:
                                            pass
                                        for ch in username:
                                            await page.keyboard.type(ch)
                                            await page.wait_for_timeout(random.uniform(80, 200))
                                        print("Nombre de usuario alternativo ingresado.")
                                        # intentar avanzar
                                        next2 = None
                                        try:
                                            cand2 = page.get_by_role("button", name="Siguiente")
                                            await cand2.wait_for(state="visible", timeout=2000)
                                            next2 = cand2
                                        except Exception:
                                            next2 = None
                                        if not next2:
                                            for sel in ["button:has-text('Siguiente')", "button >> text=Siguiente"]:
                                                try:
                                                    loc2 = page.locator(sel)
                                                    if (await loc2.count()) > 0 and await loc2.first.is_visible():
                                                        next2 = loc2.first
                                                        break
                                                except Exception:
                                                    continue
                                        if next2:
                                            try:
                                                await next2.scroll_into_view_if_needed()
                                                try:
                                                    enabled = await next2.is_enabled()
                                                except Exception:
                                                    enabled = True
                                                if not enabled:
                                                    await page.wait_for_timeout(500)
                                                await next2.click()
                                                print("Segundo 'Siguiente' clickeado tras ingresar usuario alternativo.")
                                            except Exception as e:
                                                print(f"No se pudo clicar el segundo 'Siguiente': {e}")
                                    except Exception as e:
                                        print(f"Error al completar campo alternativo: {e}")

                            except Exception:
                                # no apareció paso alternativo -> seguir
                                pass

                            # escribir contraseña (si aparece)
                            try:
                                pwd_selectors = "input[name='password'], input[autocomplete='current-password'], input[type='password']"
                                await page.wait_for_selector(pwd_selectors, timeout=8000)
                                pwd_loc = None
                                pwd_candidates = page.locator(pwd_selectors)
                                for i in range(await pwd_candidates.count()):
                                    el = pwd_candidates.nth(i)
                                    try:
                                        if await el.is_visible():
                                            pwd_loc = el
                                            break
                                    except Exception:
                                        continue
                                if pwd_loc:
                                    try:
                                        await pwd_loc.scroll_into_view_if_needed()
                                        try:
                                            await pwd_loc.focus()
                                        except Exception:
                                            await pwd_loc.click()
                                        try:
                                            await pwd_loc.fill("")
                                        except Exception:
                                            pass
                                        for ch in password:
                                            await page.keyboard.type(ch)
                                            await page.wait_for_timeout(random.uniform(80, 200))
                                        print("Contraseña ingresada correctamente (simulación humana).")
                                    except Exception as e:
                                        print(f"Error al escribir la contraseña: {e}")
                            except Exception:
                                pass

                            # intentar clicar botón final
                            try:
                                final_btn = None
                                try:
                                    await page.wait_for_selector("button[data-testid='LoginForm_Login_Button']", timeout=3000)
                                    loc = page.locator("button[data-testid='LoginForm_Login_Button']")
                                    if (await loc.count()) > 0 and await loc.first.is_visible():
                                        final_btn = loc.first
                                except Exception:
                                    final_btn = None
                                if not final_btn:
                                    try:
                                        maybe = page.get_by_role("button", name="Iniciar sesión")
                                        await maybe.wait_for(state="visible", timeout=2000)
                                        final_btn = maybe
                                    except Exception:
                                        final_btn = None
                                if not final_btn:
                                    for sel in ["button:has-text('Iniciar sesión')", "button >> text=Iniciar sesión"]:
                                        try:
                                            loc2 = page.locator(sel)
                                            if (await loc2.count()) > 0 and await loc2.first.is_visible():
                                                final_btn = loc2.first
                                                break
                                        except Exception:
                                            continue
                                if final_btn:
                                    try:
                                        await final_btn.scroll_into_view_if_needed()
                                        try:
                                            enabled = await final_btn.is_enabled()
                                        except Exception:
                                            enabled = True
                                        if not enabled:
                                            await page.wait_for_timeout(500)
                                        await final_btn.click()
                                        print("Botón final 'Iniciar sesión' clickeado.")
                                    except Exception as e:
                                        print(f"No se pudo clicar el botón final de login: {e}")
                                else:
                                    print("No se encontró el botón final de login (Iniciar sesión).")
                            
                            except Exception as e:
                                print(f"Error al intentar clicar el botón final de login: {e}")

                            print("Email escrito en el popup (simulando escritura humana).")
                        except Exception as e:
                            print(f"No se pudo escribir email en popup: {e}")
                except Exception as e:
                    print(f"Botón 'Iniciar sesión' no encontrado o no clickeable: {e}")
            yield browser_manager, browser, context, page
        finally:
            # Intentar cerrar los recursos si fueron creados
            try:
                if browser_manager and browser and context:
                    # Cerrar o mantener abierto según flag
                    await browser_manager.close_browser(browser, context, keep_open=keep_open, save_cookies=save_cookies)

                    # Si el usuario pidió mantener abierto, esperar a que indique cerrar
                    if keep_open:
                        try:
                            print("El navegador se mantiene abierto. Presiona Enter para cerrarlo y continuar...")
                            # Esperar input sin bloquear el event loop
                            await asyncio.get_event_loop().run_in_executor(None, input)
                        except (KeyboardInterrupt, Exception):
                            # Si el usuario interrumpe, intentaremos cerrar de todos modos
                            pass

                        # Tras recibir enter (o interrupción), cerrar el navegador
                        try:
                            await browser_manager.close_browser(browser, context, keep_open=False, save_cookies=save_cookies)
                        except Exception:
                            pass
            finally:
                # Cerrar la instancia de playwright (si procede)
                try:
                    await p.__aexit__(None, None, None)
                except Exception:
                    pass


async def _run_example():
    """Runner de ejemplo para probar LoginInX con credenciales de prueba.

    Ajusta headless a False si quieres ver la interacción. Por defecto usa
    la carpeta `search/cookies/x` y generará `cookies_{username}.json`.
    """
    # Datos de ejemplo provistos
    correo = "josesatrapa@plat.com.py"
    username = "JoseSatrapa"
    password = "recuerdos12345"

    # Instanciar y ejecutar sesión (headless=False mostrará la ventana del navegador)
    login = LoginInX(headless=False)
    # Mostrar la ruta de cookies que se intentará usar
    base = Path("search/cookies/x")
    expected_cookie_file = base / f"cookies_{username}.json"
    print(f"[+] Intentando usar cookies en: {expected_cookie_file}")

    async with login.session(
        search_term="x.com",
        expected_domain="x.com",
        keep_open=True,
        save_cookies=True,
        login_email=correo,
        username=username,
        password=password,
        cookies_path=str(base),
    ) as (bm, browser, context, page):
        try:
            print(f"[+] Página actual: {page.url}")
            # Pequeña pausa para observar la página antes de cerrar
            await page.wait_for_timeout(10000)
        except Exception as e:
            print(f"[!] Error durante la sesión de prueba: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(_run_example())
    except KeyboardInterrupt:
        print("[!] Ejecutado interrumpido por el usuario.")
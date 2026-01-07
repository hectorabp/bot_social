import typing as t
from pathlib import Path
from search.browser import BrowserManager
from playwright.async_api import async_playwright
import random

class Search:
    def __init__(self, url="https://duckduckgo.com", headless: bool = False, keep_open: bool = False, save_cookies: bool = True, check_ip: bool = False, session_id: str = "default_session"):
        """
        - url: motor de búsqueda (por defecto DuckDuckGo)
        - headless: lanzar navegador en modo headless
        - keep_open: si True, dejará el navegador abierto al finalizar (por defecto False)
        - save_cookies: si True, guardará cookies al cerrar (por defecto True)
        - check_ip: si True, verifica la IP antes de buscar (por defecto False)
        - session_id: identificador de la sesión para Redis (ej. email)
        """
        self.url = url
        self.headless = headless
        # Control por defecto sobre cierre y guardado de cookies
        self.keep_open = keep_open
        self.save_cookies = save_cookies
        self.check_ip = check_ip
        self.session_id = session_id

    async def check_ip_address(self, page):
        """Navega a un servicio de IP para mostrar la IP pública actual."""
        try:
            print("Verificando dirección IP...")
            await page.goto("https://api.ipify.org?format=json")
            content = await page.locator("body").inner_text()
            print(f"--- IP ACTUAL: {content} ---")
            await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Error verificando IP: {e}")

    async def search_and_navigate(self, p, search_term, expected_domain=None, click_timeout=10000, keep_open: t.Optional[bool] = None, save_cookies: t.Optional[bool] = None, cookies_path: t.Optional[str] = None, session_id: t.Optional[str] = None):
        """
        Abre el navegador (vía BrowserManager), busca `search_term` en DuckDuckGo y hace clic
        en el primer resultado. Devuelve (browser_manager, browser, context, page).
        """
        
        # Determinar session_id
        current_session_id = session_id if session_id else self.session_id
        
        # Si cookies_path se usa (compatibilidad), podríamos usarlo como parte de la key o ignorarlo,
        # pero aquí priorizamos la nueva gestión por Redis.

        browser_manager = BrowserManager(headless=self.headless, session_id=current_session_id)
        browser, context, page = await browser_manager.open_browser(p, self.url)

        # Decidir comportamiento de cierre para esta llamada concreta
        local_keep_open = keep_open if keep_open is not None else self.keep_open
        local_save_cookies = save_cookies if save_cookies is not None else self.save_cookies

        try:
            # Verificar IP si está habilitado
            if self.check_ip:
                await self.check_ip_address(page)
                # Volver al buscador
                print(f"Regresando a {self.url}...")
                await page.goto(self.url)
                await page.wait_for_load_state("domcontentloaded")

            await page.fill("#searchbox_input", search_term)
            await page.wait_for_timeout(random.randint(1000, 2000))
            print(f"Buscando {search_term} en DuckDuckGo...")
            await page.press("#searchbox_input", "Enter")

            await page.wait_for_timeout(random.randint(1000, 3000))

            # Hacer clic en el primer resultado
            print("Buscando el primer resultado...")
            try:
                await page.click("a[data-testid='result-title-a']", timeout=click_timeout)
            except Exception:
                # Selector alternativo si el primero falla (DuckDuckGo puede cambiar)
                print("Selector principal falló, intentando alternativo...")
                await page.click(".result__a", timeout=click_timeout)

            # Si se espera un dominio en la URL, esperar la navegación
            if expected_domain:
                try:
                    await page.wait_for_url(f"**{expected_domain}**", timeout=15000)
                except Exception:
                    # No bloquear si no coincide; el llamador puede verificar la URL si lo desea
                    print(f"Advertencia: no se alcanzó URL que contenga '{expected_domain}' dentro del timeout.")

            return browser_manager, browser, context, page
        except Exception:
            # En caso de fallo, intentar limpiar recursos antes de propagar
            try:
                await browser_manager.close_browser(browser, context, keep_open=local_keep_open, save_cookies=local_save_cookies)
            except Exception:
                pass
            raise

    async def run(self, search_term="x.com", expected_domain=None, keep_open: t.Optional[bool] = None, save_cookies: t.Optional[bool] = None, cookies_path: t.Optional[str] = None):
        """Conveniencia: abre `async_playwright()`, realiza la búsqueda y cierra el navegador.
        Devuelve True si la navegación se completó sin excepciones, False en caso contrario.
        Útil para uso independiente; si quieres obtener la `page` para seguir interactuando,
        usa `search_and_navigate(p, ...)` desde un `async with async_playwright() as p:` externo.
        """
        async with async_playwright() as p:
            browser_manager = None
            browser = None
            context = None
            page = None
            try:
                # Determinar flags locales según parámetros o configuración por defecto
                local_keep_open = keep_open if keep_open is not None else self.keep_open
                local_save_cookies = save_cookies if save_cookies is not None else self.save_cookies

                browser_manager, browser, context, page = await self.search_and_navigate(p, search_term, expected_domain, keep_open=local_keep_open, save_cookies=local_save_cookies, cookies_path=cookies_path)
                print("Navegación completada.")
                return True
            except Exception as e:
                print(f"Error en Search.run: {e}")
                return False
            finally:
                if browser_manager and browser and context:
                    await browser_manager.close_browser(browser, context, keep_open=local_keep_open, save_cookies=local_save_cookies)

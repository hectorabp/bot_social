from __future__ import annotations

import asyncio
import typing as t
import random
 
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from account_movement.login_in_x import LoginInX


class Twittear:
    """Controla una sesión de login y mantiene el navegador si se solicita.

    Ejemplo de uso:
        t = Twittear(headless=False)
        asyncio.run(t.start(login_email='me@example.com', username='@user', password='pw', keep_open=True))
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self._login = LoginInX(headless=headless)

    async def start(self, login_email, username=None, password=None, keep_open=True, save_cookies=True):
        """Inicia la sesión usando `LoginInX.session`.

        Parameters:
            login_email: email para la primera pantalla de login
            username: nombre de usuario alternativo que se escribirá si aparece el campo
            password: contraseña que se escribirá en el paso final
            keep_open: si True, mantiene el navegador abierto hasta que el usuario
                       presione Enter (gestión hecha por `LoginInX`)
            save_cookies: si True, intenta guardar cookies al cerrar

        Devuelve la tupla (browser_manager, browser, context, page) si necesitas
        interactuar desde fuera. Si `keep_open` es True, el context manager se
        quedará a la espera hasta que el usuario cierre manualmente.
        """
        async with self._login.session(
            search_term="x.com",
            expected_domain="x.com",
            keep_open=keep_open,
            save_cookies=save_cookies,
            login_email=login_email,
            username=username,
            password=password,
        ) as (browser_manager, browser, context, page):
            print("Sesión iniciada. URL:", page.url)
            # Intentar localizar el editor de tweet y escribir "Mi primer tuit"
            try:
                tweet_selectors = [
                    "div[data-testid='tweetTextarea_0']",
                    "div[role='textbox'][data-testid='tweetTextarea_0']",
                    "div[aria-label='Post text'][role='textbox']",
                    "[data-testid='tweetTextarea_0RichTextInputContainer'] div[contenteditable='true']",
                ]
                tweet_loc = None
                for sel in tweet_selectors:
                    try:
                        await page.wait_for_selector(sel, timeout=3000)
                        loc = page.locator(sel)
                        if (await loc.count()) > 0 and await loc.first.is_visible():
                            tweet_loc = loc.first
                            break
                    except Exception:
                        continue

                if not tweet_loc:
                    print("No se encontró el editor de tweet (selectores usados).")
                else:
                    try:
                        await tweet_loc.scroll_into_view_if_needed()
                        try:
                            await tweet_loc.focus()
                        except Exception:
                            await tweet_loc.click()

                        # Escribir texto como humano
                        text = "Mi primer tuit"
                        for ch in text:
                            await page.keyboard.type(ch)
                            await asyncio.sleep(random.uniform(0.06, 0.18))
                        print("Texto escrito en el editor de tweet.")
                        # Intentar clicar el botón de publicar (data-testid 'tweetButtonInline')
                        try:
                            btn = None
                            try:
                                await page.wait_for_selector("button[data-testid='tweetButtonInline']", timeout=3000)
                                locb = page.locator("button[data-testid='tweetButtonInline']")
                                if (await locb.count()) > 0 and await locb.first.is_visible():
                                    btn = locb.first
                            except Exception:
                                btn = None

                            # Fallback por role/name (texto 'Post' o 'Tweet')
                            if not btn:
                                for name in ("Post", "Tweet", "Publicar", "Twittear"):
                                    try:
                                        maybe = page.get_by_role("button", name=name)
                                        await maybe.wait_for(state="visible", timeout=1500)
                                        btn = maybe
                                        break
                                    except Exception:
                                        continue

                            if not btn:
                                for sel in ["button:has-text('Post')", "button:has-text('Tweet')", "button >> text=Post"]:
                                    try:
                                        loc3 = page.locator(sel)
                                        if (await loc3.count()) > 0 and await loc3.first.is_visible():
                                            btn = loc3.first
                                            break
                                    except Exception:
                                        continue

                            if btn:
                                try:
                                    await btn.scroll_into_view_if_needed()
                                    try:
                                        enabled = await btn.is_enabled()
                                    except Exception:
                                        enabled = True
                                    if not enabled:
                                        await page.wait_for_timeout(500)
                                    await btn.click()
                                    print("Botón 'Post' clickeado — tuit enviado (o en proceso).")
                                except Exception as e:
                                    print(f"No se pudo clicar el botón de publicar: {e}")
                            else:
                                print("No se encontró el botón de publicar (tweetButtonInline).")
                        except Exception as e:
                            print(f"Error intentando clicar el botón publicar: {e}")
                    except Exception as e:
                        print(f"Error escribiendo en editor de tweet: {e}")
            except Exception as e:
                print(f"Error buscando editor de tweet: {e}")
            # Si no mantenemos abierto, devolver inmediatamente tras una espera corta
            if not keep_open:
                await page.wait_for_timeout(1500)
            # Devolver objetos por si el llamador quiere operar sobre ellos
            return browser_manager, browser, context, page

    def run(self, login_email, username=None, password=None, keep_open=True, save_cookies=True):
        """Conveniencia síncrona para ejecutar `start`.

        Nota: usa `asyncio.run` internamente.
        """
        return asyncio.run(self.start(login_email=login_email, username=username, password=password, keep_open=keep_open, save_cookies=save_cookies))


if __name__ == "__main__":
    # Ejemplo de ejecución rápida (ajusta credenciales según necesites)
    t = Twittear(headless=False)
    try:
        t.run(login_email="josesatrapa@plat.com.py", username="@JoseSatrapa", password="recuerdos12345", keep_open=True)
    except Exception as e:
        print(f"Error ejecutando ejemplo de Twittear: {e}")

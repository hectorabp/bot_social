"""Módulo para navegar a un tuit específico tras iniciar sesión usando LoginInX.

Provee la clase `Retwittear` con métodos async/sync para iniciar sesión y
abrir la URL objetivo, manteniendo el navegador abierto si se solicita.
"""
from __future__ import annotations

import asyncio
import typing as t
import sys
from pathlib import Path
import random

sys.path.append(str(Path(__file__).resolve().parent.parent))
from account_movement.login_in_x import LoginInX


class Retwittear:
    """Inicia sesión y navega a una URL de tuit, quedándose allí.

    Uso:
        r = Retwittear(headless=False)
        r.run(login_email, tweet_url, username, password, keep_open=True)
    """

    def __init__(self, headless: bool = False):
        self._login = LoginInX(headless=headless)

    async def start(self, login_email, tweet_url: str, username=None, password=None, keep_open=True, save_cookies=True):
        """Abre la sesión y navega a `tweet_url`. Mantiene el navegador según `keep_open`.

        Devuelve (browser_manager, browser, context, page).
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
            try:
                await page.wait_for_timeout(random.uniform(5, 8))
                # Navegar explícitamente a la URL del tuit
                print(f"Navegando a {tweet_url} ...")
                await page.goto(tweet_url, wait_until="load", timeout=15000)
                # Pequeña espera para permitir carga dinámica
                await page.wait_for_timeout(2000)
                print("Página objetivo cargada. Quedando en la página según keep_open.")
                # Intentar clicar el botón de retweet (data-testid='retweet')
                try:
                    rt_btn = None
                    try:
                        await page.wait_for_selector("button[data-testid='retweet']", timeout=5000)
                        loc_rt = page.locator("button[data-testid='retweet']")
                        if (await loc_rt.count()) > 0 and await loc_rt.first.is_visible():
                            rt_btn = loc_rt.first
                    except Exception:
                        rt_btn = None

                    if rt_btn:
                        try:
                            await rt_btn.scroll_into_view_if_needed()
                            await rt_btn.click()
                            print("Se hizo clic en el botón de retweet (abrir menú).")
                            # Tras abrir menú, intentar clicar la opción 'Retweet' / 'Repost'
                            try:
                                # Espera corta a que aparezca el menú / opción
                                await page.wait_for_timeout(800)
                                chosen = None
                                # Intentar por role/menuitem con varios nombres
                                for name in ("Retweet", "Repost", "Retwittear", "Repostear"):
                                    try:
                                        maybe = page.get_by_role("menuitem", name=name)
                                        await maybe.wait_for(state="visible", timeout=1200)
                                        chosen = maybe
                                        break
                                    except Exception:
                                        continue

                                if not chosen:
                                    # Fallback a botones dentro de menús por texto
                                    for sel in [
                                        "div[role='menu'] button:has-text('Retweet')",
                                        "div[role='menu'] button:has-text('Repost')",
                                        "button:has-text('Retweet')",
                                    ]:
                                        try:
                                            locm = page.locator(sel)
                                            if (await locm.count()) > 0 and await locm.first.is_visible():
                                                chosen = locm.first
                                                break
                                        except Exception:
                                            continue

                                if chosen:
                                    try:
                                        await chosen.scroll_into_view_if_needed()
                                        await chosen.click()
                                        print("Opción de retweet seleccionada (acción ejecutada).")
                                    except Exception as e:
                                        print(f"No se pudo clicar la opción de retweet: {e}")
                                else:
                                    print("No se encontró la opción de retweet en el menú; puede que el click ya haya hecho la acción o el menú tenga otra estructura.")
                            except Exception as e:
                                print(f"Error manejando menú de retweet: {e}")
                        except Exception as e:
                            print(f"Error clicando el botón de retweet: {e}")
                    else:
                        print("No se encontró el botón de retweet en la página.")
                except Exception as e:
                    print(f"Error durante el flujo de retweet: {e}")
            except Exception as e:
                print(f"Error navegando a la URL del tuit: {e}")

            # Si no se mantiene abierto, esperar un poquito y devolver
            if not keep_open:
                await page.wait_for_timeout(1500)

            return browser_manager, browser, context, page

    def run(self, login_email, tweet_url: str, username=None, password=None, keep_open=True, save_cookies=True):
        """Conveniencia síncrona que ejecuta `start`.
        """
        return asyncio.run(self.start(login_email=login_email, tweet_url=tweet_url, username=username, password=password, keep_open=keep_open, save_cookies=save_cookies))

"""Módulo helper para iniciar sesión en X/Twitter y mantener la sesión abierta.

Provee la clase `LikeTuit` con métodos async/sync para iniciar sesión y
quedarse en la página (útil para depuración o para ejecutar acciones manuales
desde una REPL o por pasos posteriores).
"""
from __future__ import annotations

import asyncio
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from account_movement.login_in_x import LoginInX


class LikeTuit:
    """Controla una sesión de login y mantiene el navegador si se solicita.

    Uso:
        l = LikeTuit(headless=False)
        l.run(login_email, username, password, keep_open=True)
    """

    def __init__(self, headless: bool = False):
        self._login = LoginInX(headless=headless)

    async def start(self, login_email, username=None, password=None, tweet_url: str = None, keep_open=True, save_cookies=True):
        """Inicia la sesión y devuelve (browser_manager, browser, context, page).

        Si `keep_open` es True, la sesión permanecerá abierta hasta que el
        usuario confirme el cierre (gestión dentro de `LoginInX`).
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
            # Espera aleatoria entre 4 y 8 segundos antes de navegar al tuit objetivo
            wait_secs = random.uniform(4, 8)
            print(f"Esperando {wait_secs:.2f}s antes de navegar al tuit objetivo...")
            await asyncio.sleep(wait_secs)

            target = tweet_url or "https://x.com/julibicco/status/1985012272566350199"
            try:
                print(f"Navegando a {target}...")
                await page.goto(target, wait_until="load", timeout=20000)
                # Espera entre 2 y 3 segundos para que la página termine de estabilizarse
                delay_after_nav = random.uniform(2, 3)
                await asyncio.sleep(delay_after_nav)
                print(f"Página de tuit cargada. Esperé {delay_after_nav:.2f}s y permaneciendo en ella.")

                # Intentar localizar y clicar el botón 'Like' (data-testid='like')
                try:
                    like_btn = None
                    try:
                        await page.wait_for_selector("button[data-testid='like']", timeout=4000)
                        loc_like = page.locator("button[data-testid='like']")
                        if (await loc_like.count()) > 0 and await loc_like.first.is_visible():
                            like_btn = loc_like.first
                    except Exception:
                        like_btn = None

                    # Fallbacks por role/name o texto
                    if not like_btn:
                        try:
                            maybe = page.get_by_role("button", name="Like")
                            await maybe.wait_for(state="visible", timeout=1500)
                            like_btn = maybe
                        except Exception:
                            like_btn = None

                    if not like_btn:
                        for sel in ["button:has-text('Like')", "button:has-text('Me gusta')", "button >> text=Like"]:
                            try:
                                loc2 = page.locator(sel)
                                if (await loc2.count()) > 0 and await loc2.first.is_visible():
                                    like_btn = loc2.first
                                    break
                            except Exception:
                                continue

                    if like_btn:
                        try:
                            await like_btn.scroll_into_view_if_needed()
                            try:
                                enabled = await like_btn.is_enabled()
                            except Exception:
                                enabled = True
                            if not enabled:
                                await asyncio.sleep(0.5)
                            await like_btn.click()
                            # Pequeña espera para que se procese la acción
                            await asyncio.sleep(random.uniform(0.5, 1.0))
                            print("Botón 'Like' clickeado.")
                        except Exception as e:
                            print(f"No se pudo clicar el botón 'Like': {e}")
                    else:
                        print("No se encontró el botón 'Like' en la página.")
                except Exception as e:
                    print(f"Error durante intento de like: {e}")
            except Exception as e:
                print(f"Error navegando al tuit objetivo: {e}")

            # Espera corta para estabilizar la página si no mantenemos abierto
            if not keep_open:
                await page.wait_for_timeout(1500)
            return browser_manager, browser, context, page

    def run(self, login_email, username=None, password=None, keep_open=True, save_cookies=True):
        """Conveniencia síncrona que ejecuta `start`.
        """
        return asyncio.run(self.start(login_email=login_email, username=username, password=password, keep_open=keep_open, save_cookies=save_cookies))

"""Módulo helper para iniciar sesión en X/Twitter y quedarse en la sesión
para poder comentar un tuit manualmente o programáticamente desde el contexto.

Provee la clase `CommentTweet` con métodos async/sync para iniciar sesión y
mantener la sesión abierta (gestión del cierre delegada a `LoginInX`).
"""
from __future__ import annotations

import asyncio
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from account_movement.login_in_x import LoginInX


class CommentTweet:
    """Inicia sesión y mantiene el navegador abierto para comentar.

    Uso:
        c = CommentTweet(headless=False)
        c.run(login_email, username, password, keep_open=True)
    """

    def __init__(self, headless: bool = False):
        self._login = LoginInX(headless=headless)

    async def start(self, login_email, target, username=None, password=None, keep_open=True, save_cookies=True):
        """Abre la sesión y devuelve (browser_manager, browser, context, page).

        Mantiene la sesión abierta si `keep_open` es True (el prompt de cierre
        se maneja dentro de `LoginInX`).
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
            # Espera aleatoria entre 2 y 5 segundos antes de navegar al tuit objetivo
            wait_secs = random.uniform(2, 5)
            await asyncio.sleep(wait_secs)

            try:
                print(f"Navegando a {target}...")
                await page.goto(target, wait_until="load", timeout=20000)
                # Pequeña espera para estabilizar la página
                await asyncio.sleep(1.5)
                print("Página objetivo cargada. Quedando en la página según keep_open.")
                # Intentar localizar el editor de reply y escribir 'Cierto' letra por letra
                try:
                    reply_selectors = [
                        "div[data-testid='tweetTextarea_0']",
                        "div[role='textbox'][data-testid='tweetTextarea_0']",
                        "[data-testid='tweetTextarea_0RichTextInputContainer'] div[contenteditable='true']",
                        "div[aria-label='Post text'][role='textbox']",
                    ]
                    reply_loc = None
                    for sel in reply_selectors:
                        try:
                            await page.wait_for_selector(sel, timeout=2500)
                            loc = page.locator(sel)
                            if (await loc.count()) > 0 and await loc.first.is_visible():
                                reply_loc = loc.first
                                break
                        except Exception:
                            continue

                    if not reply_loc:
                        print("No se encontró el editor de reply con los selectores probados.")
                    else:
                        try:
                            await reply_loc.scroll_into_view_if_needed()
                            try:
                                await reply_loc.focus()
                            except Exception:
                                await reply_loc.click()

                            # Limpiar si es posible
                            try:
                                await reply_loc.fill("")
                            except Exception:
                                pass

                            text = "Cierto"
                            for ch in text:
                                await page.keyboard.type(ch)
                                await asyncio.sleep(random.uniform(0.08, 0.22))
                            print("Texto 'Cierto' escrito en el reply (simulación humana).")

                            # Intentar clicar el botón de Reply/Tweet (data-testid='tweetButtonInline')
                            try:
                                btn = None
                                try:
                                    await page.wait_for_selector("button[data-testid='tweetButtonInline']", timeout=2500)
                                    locb = page.locator("button[data-testid='tweetButtonInline']")
                                    if (await locb.count()) > 0 and await locb.first.is_visible():
                                        btn = locb.first
                                except Exception:
                                    btn = None

                                if not btn:
                                    try:
                                        maybe = page.get_by_role("button", name="Reply")
                                        await maybe.wait_for(state="visible", timeout=1500)
                                        btn = maybe
                                    except Exception:
                                        btn = None

                                if not btn:
                                    for sel in ["button:has-text('Reply')", "button:has-text('Post')", "button:has-text('Tweet')"]:
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
                                        await btn.click()
                                        print("Botón de Reply clickeado.")
                                    except Exception as e:
                                        print(f"No se pudo clicar el botón de Reply: {e}")
                                else:
                                    print("No se encontró el botón de Reply/Tweet para publicar el comentario.")
                            except Exception as e:
                                print(f"Error intentando clicar el botón de Reply: {e}")

                        except Exception as e:
                            print(f"Error escribiendo en el editor de reply: {e}")
                except Exception as e:
                    print(f"Error buscando editor de reply: {e}")
            except Exception as e:
                print(f"Error navegando a la URL objetivo: {e}")

            # Si no mantenemos abierto, esperar un poquito antes de salir
            if not keep_open:
                await page.wait_for_timeout(1500)
            return browser_manager, browser, context, page

    def run(self, login_email, username=None, password=None, keep_open=True, save_cookies=True):
        """Conveniencia síncrona que ejecuta `start`.
        """
        return asyncio.run(self.start(login_email=login_email, username=username, password=password, keep_open=keep_open, save_cookies=save_cookies))


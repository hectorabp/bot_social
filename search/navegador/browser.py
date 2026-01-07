import asyncio
import random
import json
import typing as t
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright


class BrowserManager:
    def __init__(self, headless: bool = True, cookies_file: t.Optional[t.Union[str, Path]] = None):
        # User-Agents organizados por OS y navegador para desktop
        self.user_agents = {
            "Windows": {
                "Chrome": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.59 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.70 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.137 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.88 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.182 Safari/537.36"
                ],
                "Edge": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
                ],
                "Brave": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36 Brave/130.0.0.0",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.59 Safari/537.36 Brave/129.0.0.0"
                ]
            },
            "Linux": {
                "Chrome": [
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.59 Safari/537.36",
                    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
                    "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.100 Safari/537.36"
                ],
                "Firefox": [
                    "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
                    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
                    "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"
                ]
            }
        }

        # Nota: sólo se usan user-agents de escritorio (no móviles)

        # Proxy DataImpulse
        self.proxy_username = "5eba36bc58c7fc54d588"
        self.proxy_password = "3819e4214597c729"
        self.proxy_host = "gw.dataimpulse.com"
        self.proxy_port = "823"

        self.headless = headless
        # Permitir especificar ruta de cookies. Si no se pasa, usar cookies.json en cwd
        if cookies_file:
            self.cookies_file = Path(cookies_file)
        else:
            self.cookies_file = Path("cookies.json")
            
        self.auto_save_task = None  # Tarea para el guardado automático

    async def _load_cookies(self, context):
        if self.cookies_file.exists():
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("[+] Cookies cargadas desde archivo.")
            except Exception as e:
                print(f"[!] Error cargando cookies: {e}")

    async def rotating_proxy(self, p, browser):
        try: 
            # Sólo navegadores de escritorio: elegir OS y navegador de desktop
            os = random.choice(list(self.user_agents.keys()))
            browser_name = random.choice(list(self.user_agents[os].keys()))
            user_agent = random.choice(self.user_agents[os][browser_name])
            viewport = {"width": random.choice([1200, 1150]), "height": random.choice([850, 950])}
            has_touch = False
            is_mobile_flag = False
            
            context = await browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                has_touch=has_touch,
                is_mobile=is_mobile_flag,
                proxy={
                    "server": "http://" + self.proxy_host + ":" + self.proxy_port,
                    "username": self.proxy_username,
                    "password": self.proxy_password
                },
                locale="es-ES",
                timezone_id="America/Asuncion",
                permissions=["geolocation"],
            )
            page = await context.new_page()
            # Configuración para escritorio
            if os == "Windows":
                nav_platform = "Win32"
            elif os == "macOS":
                nav_platform = "MacIntel"
            elif os == "Linux":
                nav_platform = "Linux x86_64"
            else:
                nav_platform = "Win32"
                os = "Windows"
            hardware_concurrency = 8
            max_touch_points = 0
            
            # Spoofear WebGL parameters para anti-detección
            webgl_vendor = "Intel Inc." if os == "Windows" else ("Apple Inc." if os == "macOS" else "Google Inc.")
            webgl_renderer = f"Intel(R) Iris(TM) Graphics 6100" if os == "Windows" else (f"Apple M1" if os == "macOS" else "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)")
            
            spoof_script = f"""
            Object.defineProperty(navigator, 'platform', {{ get: () => '{nav_platform}' }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {hardware_concurrency} }});
            Object.defineProperty(navigator, 'language', {{ get: () => 'es-ES' }});
            Object.defineProperty(navigator, 'languages', {{ get: () => ['es-ES', 'es', 'en-US'] }});
            Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => {max_touch_points} }});
            """
            
            webgl_spoof = f"""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{ // UNMASKED_VENDOR_WEBGL
                    return '{webgl_vendor}';
                }}
                if (parameter === 37446) {{ // UNMASKED_RENDERER_WEBGL
                    return '{webgl_renderer}';
                }}
                return getParameter.call(this, parameter);
            }};
            """
            
            spoof_script += webgl_spoof
            await context.add_init_script(spoof_script)
            
            return context, page
        except Exception as e:
            print(f"[!] Error setting up rotating proxy: {e}")
            raise

    async def _save_cookies(self, context):
        try:
            cookies = await context.cookies()
            # Asegurarse de que el directorio existe
            try:
                self.cookies_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

            with open(self.cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            # print("[+] Cookies guardadas correctamente.") # Comentado para no saturar logs en auto-save
        except Exception as e:
            print(f"[!] Error guardando cookies (posiblemente contexto cerrado): {e}")

    async def _auto_save_loop(self, context, interval: int):
        """Bucle infinito que guarda cookies cada 'interval' segundos."""
        try:
            while True:
                await asyncio.sleep(interval)
                await self._save_cookies(context)
        except asyncio.CancelledError:
            pass # Tarea cancelada normalmente
        except Exception as e:
            print(f"[!] Error en auto-guardado de cookies: {e}")

    def start_auto_save(self, context, interval: int = 5):
        """Inicia el guardado automático de cookies en segundo plano."""
        if self.auto_save_task is None:
            self.auto_save_task = asyncio.create_task(self._auto_save_loop(context, interval))
            print(f"[+] Auto-guardado de cookies activado (cada {interval}s).")

    async def _configure_geolocation_from_ip(self, context):
        """Detecta la ubicación de la IP del proxy y ajusta la geolocalización del navegador."""
        try:
            print("[*] Detectando ubicación de la IP del proxy...")
            # Usar context.request para hacerlo en segundo plano sin navegar la página visible
            response = await context.request.get("http://ip-api.com/json/")
            
            if not response.ok:
                print(f"[!] Error en petición IP API: {response.status} {response.status_text}")
                return

            data = await response.json()

            if "lat" in data and "lon" in data:
                lat = data["lat"]
                lon = data["lon"]
                country = data.get("country", "Unknown")
                city = data.get("city", "Unknown")
                
                # Añadir un pequeño "jitter" (ruido) aleatorio para no parecer un bot estático en el centro del datacenter
                # +/- 0.005 grados es aprox 500m
                lat += random.uniform(-0.005, 0.005)
                lon += random.uniform(-0.005, 0.005)
                
                await context.set_geolocation({"latitude": lat, "longitude": lon})
                print(f"[+] Geolocalización sincronizada con IP: {city}, {country} (Lat: {lat:.4f}, Lon: {lon:.4f})")
            else:
                print("[!] La API no devolvió coordenadas válidas. No se establece geolocalización.")
                
        except Exception as e:
            print(f"[!] Error alineando geolocalización con IP: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def open_browser(self, p, url: str, load_cookies: bool = True):
        print(f"[+] Abriendo navegador")

        browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-plugins",
                "--disable-extensions",
                "--no-sandbox",
            ],
        )

        context, page = await self.rotating_proxy(p, browser)

        # Alinear geolocalización con la IP real del proxy
        await self._configure_geolocation_from_ip(context)

        if load_cookies:
            await self._load_cookies(context)

        # Iniciar auto-guardado
        self.start_auto_save(context, interval=5)

        await page.wait_for_timeout(random.randint(1000, 3000))  # Pausa aleatoria después de abrir el navegador

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print(f"[+] Navegando a {url}")
            await page.wait_for_timeout(random.randint(1000, 2000))  # pausa inicial
        except Exception as e:
            print(f"[!] Error cargando {url}: {e}")
            await browser.close()
            raise

        return browser, context, page

    async def close_browser(self, browser, context, keep_open: bool = False, save_cookies: bool = True):
        """
        Cierra el contexto y el navegador.

        - keep_open: si es True, NO cerrará el navegador ni el contexto (útil para mantener
          la sesión abierta para inspección manual). Por defecto False (comportamiento actual).
        - save_cookies: si es True, intentará guardar las cookies antes de cerrar (o incluso
          si keep_open=True). Por defecto True.
        """
        # Detener auto-guardado si existe
        if self.auto_save_task:
            self.auto_save_task.cancel()
            try:
                await self.auto_save_task
            except asyncio.CancelledError:
                pass
            self.auto_save_task = None

        try:
            # Guardar cookies si se solicita
            if save_cookies and context is not None:
                await self._save_cookies(context)

            if not keep_open:
                await context.close()
                await browser.close()
                print("[+] Navegador cerrado correctamente.")
            else:
                print("[+] Manteniendo navegador abierto por petición (keep_open=True).")
        except Exception as e:
            print(f"[!] Error cerrando navegador (posiblemente ya cerrado): {e}")

    async def keep_browser_open(self, browser, context, page):
        """
        Mantiene el navegador abierto para uso manual hasta que el usuario presione Enter.
        """
        print("[*] Navegador abierto para uso manual. Presiona Enter en la consola para cerrar.")
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, input)
        except KeyboardInterrupt:
            pass
        finally:
            await self.close_browser(browser, context)


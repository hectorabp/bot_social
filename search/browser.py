import asyncio
import random
import json
import typing as t
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright
from search.redis_session_manager import RedisSessionManager

class BrowserManager:
    def __init__(self, headless: bool = True, session_id: str = "current_session", cookies_file: t.Optional[t.Union[str, Path]] = None, session_path: str = "session_data"):
        """
        :param session_id: Identificador único de la sesión para Redis (ej. email de la cuenta).
        """
        self.session_id = session_id
        
        # Inicializar gestor de sesiones Redis
        self.redis_manager = RedisSessionManager()
        
        # User-Agents organizados por OS y navegador para desktop
        self.user_agents = {
            "Windows": {
                "Chrome": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6668.59 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.58 Safari/537.36",
                ],
                "Edge": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
                ]
            },
            "Linux": {
                "Chrome": [
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
                    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
                ]
            }
        }

        # Proxy DataImpulse (Puede ajustar esto si necesita sesiones stickies de IP también)
        self.proxy_username = "LDqH6H0s5StzoNdU"
        self.proxy_password = "oSlowEpYeBHQIcDk_country-py"
        self.proxy_host = "geo.iproyal.com"
        self.proxy_port = "12321"

        self.headless = headless
        self.auto_save_task = None
        
        # Cargamos o generamos el perfil "Fingerprint" al iniciar la clase
        self.profile = self._load_or_create_profile()

    def _load_or_create_profile(self) -> dict:
        """
        Carga el perfil del navegador (UA, Viewport, WebGL) si existe en Redis.
        Si no, genera uno nuevo y lo guarda en Redis.
        """
        try:
            profile = self.redis_manager.load_profile(self.session_id)
            if profile:
                print(f"[+] Perfil de navegador (Fingerprint) cargado desde Redis ({self.session_id}).")
                return profile
        except Exception as e:
            print(f"[!] Error leyendo perfil de Redis, se generará uno nuevo: {e}")

        # Generar nuevo perfil aleatorio
        print("[*] Generando nuevo perfil de navegador único...")
        
        os_name = random.choice(list(self.user_agents.keys()))
        browser_name = random.choice(list(self.user_agents[os_name].keys()))
        user_agent = random.choice(self.user_agents[os_name][browser_name])
        
        # Viewport consistente
        viewport = {"width": random.choice([1280, 1366, 1536, 1920]), "height": random.choice([720, 768, 864, 1080])}
        
        # Plataforma para spoofing
        if os_name == "Windows":
            nav_platform = "Win32"
            webgl_vendor = "Intel Inc."
            webgl_renderer = "Intel(R) Iris(TM) Graphics 6100"
        elif os_name == "Linux":
            nav_platform = "Linux x86_64"
            webgl_vendor = "Google Inc."
            webgl_renderer = "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"
        else: # Fallback
            nav_platform = "Win32" 
            webgl_vendor = "Intel Inc."
            webgl_renderer = "Intel(R) UHD Graphics"

        profile = {
            "os_name": os_name,
            "user_agent": user_agent,
            "viewport": viewport,
            "nav_platform": nav_platform,
            "webgl_vendor": webgl_vendor,
            "webgl_renderer": webgl_renderer,
            "hardware_concurrency": 8,
            "device_scale_factor": 1
        }

        # Guardar perfil en Redis
        try:
            self.redis_manager.save_profile(self.session_id, profile, ttl=86400) # TTL 24 horas por defecto
            print("[+] Nuevo perfil guardado en Redis.")
        except Exception as e:
            print(f"[!] No se pudo guardar el perfil en Redis: {e}")
            
        return profile

    async def _load_cookies(self, context):
        try:
            cookies = self.redis_manager.load_cookies(self.session_id)
            if cookies:
                await context.add_cookies(cookies)
                print(f"[+] Cookies cargadas desde Redis ({self.session_id}).")
        except Exception as e:
            print(f"[!] Error cargando cookies de Redis: {e}")

    async def _setup_browser_context(self, browser):
        """Configura el contexto usando el perfil PERSISTENTE."""
        try:
            # Usamos los datos del self.profile en lugar de randomizar aquí
            p_data = self.profile
            
            context = await browser.new_context(
                user_agent=p_data["user_agent"],
                viewport=p_data["viewport"],
                device_scale_factor=p_data["device_scale_factor"],
                has_touch=False,
                is_mobile=False,
                proxy={
                    "server": f"http://{self.proxy_host}:{self.proxy_port}",
                    "username": self.proxy_username,
                    "password": self.proxy_password
                },
                locale="es-ES",
                timezone_id="America/Asuncion",
                permissions=["geolocation"],
            )
            
            page = await context.new_page()
            
            # Scripts de evasión usando los datos del perfil guardado
            spoof_script = f"""
            Object.defineProperty(navigator, 'platform', {{ get: () => '{p_data["nav_platform"]}' }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {p_data["hardware_concurrency"]} }});
            Object.defineProperty(navigator, 'language', {{ get: () => 'es-ES' }});
            Object.defineProperty(navigator, 'languages', {{ get: () => ['es-ES', 'es', 'en-US'] }});
            Object.defineProperty(navigator, 'webdriver', {{ get: () => false }});
            """
            
            webgl_spoof = f"""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) {{ return '{p_data["webgl_vendor"]}'; }}
                if (parameter === 37446) {{ return '{p_data["webgl_renderer"]}'; }}
                return getParameter.call(this, parameter);
            }};
            """
            
            await context.add_init_script(spoof_script + webgl_spoof)
            
            return context, page
        except Exception as e:
            print(f"[!] Error configurando contexto: {e}")
            raise

    async def _save_cookies(self, context):
        try:
            cookies = await context.cookies()
            self.redis_manager.save_cookies(self.session_id, cookies, ttl=86400) # TTL 24 horas
        except Exception as e:
            print(f"[!] Error guardando cookies en Redis: {e}")

    async def _auto_save_loop(self, context, interval: int):
        try:
            while True:
                await asyncio.sleep(interval)
                await self._save_cookies(context)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[!] Error en auto-guardado: {e}")

    def start_auto_save(self, context, interval: int = 5):
        if self.auto_save_task is None:
            self.auto_save_task = asyncio.create_task(self._auto_save_loop(context, interval))
            print(f"[+] Auto-guardado activado ({interval}s).")

    async def _configure_geolocation_from_ip(self, context):
        """Intenta alinear geo con IP. Si falla, usa un default de Asunción."""
        try:
            # Nota: Si el proxy rota IPs, esto actualizará la geo para coincidir con la nueva IP
            # aunque el Fingerprint del navegador siga siendo el mismo.
            response = await context.request.get("http://ip-api.com/json/")
            if response.ok:
                data = await response.json()
                if "lat" in data and "lon" in data:
                    lat = data["lat"] + random.uniform(-0.005, 0.005)
                    lon = data["lon"] + random.uniform(-0.005, 0.005)
                    await context.set_geolocation({"latitude": lat, "longitude": lon})
                    print(f"[+] Geolocalización IP: {data.get('city')}")
                    return

            # Fallback si falla la API
            print("[!] Fallo detección IP, usando default Asunción")
            await context.set_geolocation({"latitude": -25.2637, "longitude": -57.5759})
            
        except Exception as e:
            print(f"[!] Error geo: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def open_browser(self, p, url: str, load_cookies: bool = True):
        print(f"[+] Iniciando navegador... (Session: {self.session_id})")

        browser = await p.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--disable-dev-shm-usage", # Importante para su servidor con 4GB RAM
            ],
        )

        # Aquí usamos el método nuevo que lee el perfil guardado
        context, page = await self._setup_browser_context(browser)

        await self._configure_geolocation_from_ip(context)

        if load_cookies:
            await self._load_cookies(context)

        self.start_auto_save(context, interval=10) # 10s es suficiente, ahorra CPU

        try:
            print(f"[+] Navegando a {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(random.randint(2000, 4000))
        except Exception as e:
            print(f"[!] Error cargando URL: {e}")
            await browser.close()
            raise

        return browser, context, page

    async def close_browser(self, browser, context, keep_open: bool = False, save_cookies: bool = True):
        if self.auto_save_task:
            self.auto_save_task.cancel()
            try:
                await self.auto_save_task
            except: pass
            self.auto_save_task = None

        try:
            if save_cookies and context:
                await self._save_cookies(context)

            if not keep_open:
                await context.close()
                await browser.close()
                print("[+] Sesión cerrada.")
            else:
                print("[!] Navegador mantenido abierto.")
        except Exception as e:
            print(f"[!] Error al cerrar: {e}")

    def clear_session_data(self):
        """Elimina cookies y perfil de Redis para la sesión actual."""
        try:
            self.redis_manager.clear_session(self.session_id)
            print(f"[+] Datos de sesión eliminados de Redis ({self.session_id}).")
        except Exception as e:
            print(f"[!] Error eliminando datos de sesión: {e}")

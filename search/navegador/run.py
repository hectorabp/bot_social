import asyncio
import sys
import os

# Asegurar que podemos importar browser.py desde el mismo directorio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser import BrowserManager
from playwright.async_api import async_playwright

async def main():
    # Inicializar con headless=False para ver el navegador
    manager = BrowserManager(headless=False)
    
    async with async_playwright() as p:
        # Abrir DuckDuckGo
        url = "https://duckduckgo.com"
        print(f"Abriendo {url}...")
        browser, context, page = await manager.open_browser(p, url)
        
        # Mantener el navegador abierto
        print("Navegador abierto en DuckDuckGo. Presiona ENTER en la terminal para cerrar.")
        await manager.keep_browser_open(browser, context, page)

if __name__ == "__main__":
    asyncio.run(main())
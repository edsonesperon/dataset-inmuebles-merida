"""
Script de exploración: guarda el HTML de la página de resultados de búsqueda.
"""
import asyncio
from playwright.async_api import async_playwright

URL = "https://www.inmuebles24.com/casas-o-departamentos-en-venta-en-merida-publicado-hace-menos-de-1-mes-drc-altabrisa.html"

async def explorar():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        print("Navegando a resultados...")
        await page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)
        html = await page.content()
        with open("scraper/resultados.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML guardado en scraper/resultados.html")
        await browser.close()

asyncio.run(explorar())

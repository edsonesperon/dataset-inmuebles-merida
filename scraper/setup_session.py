"""
Setup de sesión para el scraper de Inmuebles24.
Fase 4 del proyecto de portafolio dataset-inmuebles-merida.

Uso (solo se corre UNA vez, o cuando expira la sesión):
    conda activate inmuebles-scraper
    python scraper/setup_session.py

Qué hace:
  1. Abre un navegador Chromium VISIBLE e interactivo.
  2. Carga la página de inicio de Inmuebles24.
  3. TÚ navegas manualmente y resuelves cualquier CAPTCHA que aparezca.
  4. Cuando presionas Enter en la terminal, Playwright guarda el estado de
     sesión completo (cookies, localStorage, etc.) en session_state.json.
  5. El scraper principal carga ese estado para llegar como sesión validada.

Por qué funciona:
  El CAPTCHA de Inmuebles24 se dispara ante comportamiento automatizado.
  Al resolverlo manualmente una vez, las cookies de sesión resultantes
  permiten que las siguientes requests sean tratadas como humanas.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_FILE = Path("scraper/session_state.json")
URL_INICIO   = "https://www.inmuebles24.com"

# URL de resultados de Altabrisa — visítala también para que la sesión
# quede asociada a búsquedas reales (reduce riesgo de bloqueo posterior).
URL_PRUEBA = (
    "https://www.inmuebles24.com/casas-o-departamentos-en-venta-en-merida"
    "-publicado-hace-menos-de-1-mes-drc-altabrisa.html"
)


async def main() -> None:
    print("=" * 60)
    print("Setup de sesión — Inmuebles24")
    print("=" * 60)
    print()
    print("Se abrirá un navegador Chromium.")
    print("Instrucciones:")
    print("  1. Si aparece un CAPTCHA, resuélvelo manualmente.")
    print("  2. Navega a la página de resultados de cualquier colonia.")
    print("  3. Espera a que cargue correctamente.")
    print("  4. Regresa aquí y presiona Enter para guardar la sesión.")
    print()
    input("Presiona Enter para abrir el navegador...")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        print(f"\nCargando {URL_INICIO} ...")
        await page.goto(URL_INICIO, wait_until="domcontentloaded", timeout=30_000)

        print("\nEl navegador está abierto.")
        print(f"Navega a esta URL de prueba si quieres:\n  {URL_PRUEBA}")
        print()
        input("Cuando el sitio cargue correctamente, presiona Enter aquí para guardar la sesión...")

        # Guardar estado de sesión completo (cookies + localStorage)
        await context.storage_state(path=str(SESSION_FILE))
        await browser.close()

    print(f"\n✓ Sesión guardada en: {SESSION_FILE}")
    print("  Ya puedes correr el scraper principal:")
    print("  python scraper/scraper.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

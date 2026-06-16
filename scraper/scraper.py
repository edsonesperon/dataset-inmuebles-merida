"""
Scraper de propiedades en Mérida, Yucatán — Inmuebles24.
Fase 4 del proyecto de portafolio dataset-inmuebles-merida.

v2: Extracción robusta via page.content() + regex Python.
    No depende de variables JS globales (que viven en closure en Inmuebles24).

Estrategia:
  1. Página de resultados → atributo data-to-posting de cada card.
  2. Página de anuncio  → page.content() + regex sobre el HTML crudo.
     Patrones confirmados desde anuncio.html analizado manualmente.

Uso:
    conda activate inmuebles-scraper
    python scraper/scraper.py
"""

import asyncio
import csv
import random
import re
from datetime import date
from pathlib import Path

from playwright.async_api import (
    async_playwright,
    Page,
    TimeoutError as PlaywrightTimeout,
)

from config import (
    BASE_URL,
    URL_TEMPLATE,
    COLONIAS,
    DELAY_MIN_ANUNCIO,
    DELAY_MAX_ANUNCIO,
    DELAY_MIN_COLONIA,
    DELAY_MAX_COLONIA,
    ESPERA_RESULTADOS,
    ESPERA_ANUNCIO,
    USER_AGENT,
)


# ---------------------------------------------------------------------------
# Configuración de salida
# ---------------------------------------------------------------------------

OUTPUT_CSV    = Path("data/propiedades_scrapeadas.csv")
SESSION_FILE  = Path("scraper/session_state.json")

COLUMNAS_CSV = [
    "url",
    "fecha_scraping",
    "operación",
    "tipo_inmueble",
    "colonia",
    "precio",
    "m2_terreno",
    "m2_construccion",
    "recamaras",
    "banos",
    "medio_bano",
    "estacionamientos",
    "antigüedad",
    "es_preventa",
    "descripcion",
]


# ---------------------------------------------------------------------------
# Extracción de URLs desde la página de resultados
# ---------------------------------------------------------------------------

async def extraer_urls_resultados(page: Page, url_busqueda: str) -> list[str]:
    """
    Navega al listado de una colonia y devuelve URLs limpias de cada anuncio.
    Selector confirmado: div[data-qa="posting PROPERTY"][data-to-posting]
    """
    print(f"  → Cargando resultados: {url_busqueda}")
    try:
        await page.goto(url_busqueda, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(int(ESPERA_RESULTADOS * 1000))
    except PlaywrightTimeout:
        print("    ⚠  Timeout al cargar listado.")
        await page.wait_for_timeout(5_000)

    # Verificar cuántos resultados hay (para diagnóstico)
    try:
        h1 = await page.query_selector("h1")
        if h1:
            titulo = await h1.inner_text()
            print(f"    Título de resultados: {titulo.strip()[:80]}")
    except Exception:
        pass

    cards = await page.query_selector_all(
        'div[data-qa="posting PROPERTY"][data-to-posting]'
    )
    urls = []
    for card in cards:
        ruta = await card.get_attribute("data-to-posting")
        if ruta:
            ruta_limpia = ruta.split("?")[0]
            urls.append(BASE_URL + ruta_limpia)

    print(f"    ✓ {len(urls)} anuncios encontrados")
    return urls


# ---------------------------------------------------------------------------
# Extracción de datos del anuncio — regex sobre HTML crudo
# ---------------------------------------------------------------------------

def _regex_uno(patron: str, texto: str, flags: int = 0) -> str:
    """Aplica un regex y devuelve el grupo 1, o cadena vacía si no hay match."""
    m = re.search(patron, texto, flags)
    return m.group(1).strip() if m else ""


def _extraer_precio(html: str) -> str:
    """
    Extrae el precio en MXN (solo dígitos).
    Patrón confirmado línea 1693 del anuncio HTML:  'price': '4900000'
    Respaldo línea 1571:  "amount": 4900000
    """
    # Patrón primario: precio como string numérico
    precio = _regex_uno(r"'price'\s*:\s*'(\d{4,})'", html)
    if precio:
        return precio
    # Respaldo: campo amount en pricesData
    precio = _regex_uno(r'"amount"\s*:\s*(\d{4,})', html)
    return precio


def _extraer_cft(clave: str, html: str) -> str:
    """
    Extrae el value de una clave CFT del objeto mainFeatures.
    Ejemplo: _extraer_cft("CFT100", html) → "294"
    Patrón: "CFT100":{"featureId":"CFT100","label":"lote","measure":"m²","value":"294",...}
    """
    patron = rf'"{clave}"\s*:\s*\{{[^}}]*"value"\s*:\s*"([^"]+)"'
    return _regex_uno(patron, html)


def _extraer_tipo_inmueble(html: str, url: str) -> str:
    """
    Extrae el tipo de inmueble del breadcrumb JSON embebido.
    Patrón confirmado: {"url":"/casas.html","nombre":"Casa",...}
    Respaldo: prefijo de URL (veclapin → departamento, veclcain → casa).
    """
    # Intentar desde el breadcrumb JSON de la página
    tipos = re.findall(
        r'"nombre"\s*:\s*"(Casa|Departamento|Casa en condominio|Townhouse|Villa|Quinta)"',
        html,
        re.IGNORECASE,
    )
    if tipos:
        return tipos[0].lower()

    # Respaldo por prefijo de URL de Inmuebles24
    url_lower = url.lower()
    if "veclapin" in url_lower:
        return "departamento"
    if "veclcain" in url_lower:
        return "casa"
    if "veclcapa" in url_lower:
        return "casa en condominio"
    return ""


def _extraer_descripcion(html: str) -> str:
    """
    Extrae el texto de la descripción larga del anuncio.
    ID confirmado: <div id="longDescription">...</div>
    """
    m = re.search(
        r'id="longDescription"[^>]*>(.*?)</div>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return ""
    # Limpiar etiquetas HTML
    texto = re.sub(r'<br\s*/?>', '\n', m.group(1), flags=re.IGNORECASE)
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    return texto.strip()


def _extraer_estacionamientos(html: str, descripcion: str) -> str:
    """
    Intenta extraer estacionamientos de:
    1. mainFeatures (si hay CFT para parking)
    2. Texto de la descripción (regex)
    """
    # Algunos anuncios tienen estacionamientos como feature extra
    parking = _regex_uno(
        r'"(?:estacionamiento|parking|cochera)s?"\s*:\s*"?(\d+)"?', html, re.IGNORECASE
    )
    if parking:
        return parking

    # Regex sobre descripción
    patrones = [
        r'(\d+)\s*cajones?\s+de\s+estacionamiento',
        r'estacionamiento\s+para\s+(\d+)\s*autos?',
        r'cochera\s+(?:techada?\s+)?para\s+(\d+)\s*autos?',
        r'(\d+)\s*autos?\s+(?:en\s+)?(?:la\s+)?cochera',
        r'garaje\s+(?:para\s+)?(\d+)',
    ]
    for pat in patrones:
        m = re.search(pat, descripcion, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _extraer_antiguedad(descripcion: str) -> str:
    """Extrae antigüedad en años desde la descripción."""
    patrones = [
        r'antig[uü][eé]dad\s+(\d+)\s*a[ñn]os?',
        r'(\d+)\s*a[ñn]os?\s+de\s+antig[uü][eé]dad',
        r'(\d+)\s*a[ñn]os?\s+de\s+construid[ao]',
    ]
    for pat in patrones:
        m = re.search(pat, descripcion, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def _detectar_preventa(descripcion: str) -> str:
    """Detecta preventa por palabras clave en la descripción."""
    patron = re.compile(
        r'pre[- ]?venta|en\s+construcci[oó]n|fecha\s+de\s+entrega|'
        r'entrega\s+(?:estimada|programada)|obra\s+(?:negra|gris)',
        re.IGNORECASE,
    )
    return "si" if patron.search(descripcion) else "no"


async def extraer_datos_anuncio(
    page: Page, url: str, colonia: str
) -> dict | None:
    """
    Navega al anuncio, obtiene el HTML completo y extrae todos los campos
    mediante regex en Python (más robusto que JS globals en página real).
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        # Esperar a que los scripts inline se hayan ejecutado y el DOM esté listo
        await page.wait_for_timeout(int(ESPERA_ANUNCIO * 1000))
    except PlaywrightTimeout:
        print(f"    ✗ Timeout en {url}")
        return None

    # Obtener HTML completo renderizado
    try:
        html = await page.content()
    except Exception as exc:
        print(f"    ✗ Error al obtener HTML: {exc}")
        return None

    descripcion = _extraer_descripcion(html)

    registro = {
        "url":              url,
        "fecha_scraping":   date.today().isoformat(),
        "operación":        "venta",
        "tipo_inmueble":    _extraer_tipo_inmueble(html, url),
        "colonia":          colonia,
        "precio":           _extraer_precio(html),
        "m2_terreno":       _extraer_cft("CFT100", html),
        "m2_construccion":  _extraer_cft("CFT101", html),
        "recamaras":        _extraer_cft("CFT2",   html),
        "banos":            _extraer_cft("CFT3",   html),
        "medio_bano":       _extraer_cft("CFT4",   html),
        "estacionamientos": _extraer_estacionamientos(html, descripcion),
        "antigüedad":       _extraer_antiguedad(descripcion),
        "es_preventa":      _detectar_preventa(descripcion),
        "descripcion":      descripcion,
    }

    return registro


# ---------------------------------------------------------------------------
# Script principal
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=" * 60)
    print("Scraper v2 — Inmuebles24 · Mérida, Yucatán")
    print(f"Colonias a procesar: {len(COLONIAS)}")
    print(f"Fecha de scraping:   {date.today().isoformat()}")
    print("=" * 60)

    todos_los_registros: list[dict] = []
    urls_procesadas: set[str] = set()

    async with async_playwright() as pw:
        # headless=False es necesario para evadir la detección de Cloudflare.
        # Con headless=True, Inmuebles24 devuelve una página de bloqueo en lugar
        # del contenido real (confirmado en ejecución anterior).
        browser = await pw.chromium.launch(headless=False)
        # Cargar sesión guardada si existe (generada por setup_session.py).
        # Con una sesión pre-validada se evita el CAPTCHA de Inmuebles24.
        if SESSION_FILE.exists():
            print(f"  → Cargando sesión guardada: {SESSION_FILE}")
            context = await browser.new_context(
                user_agent=USER_AGENT,
                storage_state=str(SESSION_FILE),
            )
        else:
            print("  ⚠  No hay sesión guardada. Corre setup_session.py primero.")
            print("     Continuando sin sesión (puede ser bloqueado por CAPTCHA).")
            context = await browser.new_context(user_agent=USER_AGENT)
        page    = await context.new_page()

        # Parches de stealth aplicados al contexto completo (todas las páginas).
        # Desactivan las señales más comunes que Cloudflare usa para detectar
        # automatización: navigator.webdriver, plugins vacíos, idioma, etc.
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['es-MX', 'es', 'en-US']});
            window.chrome = { runtime: {} };
        """)

        # Visitar homepage primero para establecer sesión real.
        # Reduce la probabilidad de bloqueo por Cloudflare en páginas subsecuentes.
        print("  → Calentando sesión en homepage...")
        await page.goto("https://www.inmuebles24.com", wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)

        colonias_lista = list(COLONIAS.items())

        for idx_col, (nombre_colonia, slug) in enumerate(colonias_lista):
            print(f"\n{'─'*50}")
            print(f"[{idx_col + 1}/{len(colonias_lista)}] Colonia: {nombre_colonia}")

            url_busqueda = URL_TEMPLATE.format(slug=slug)
            urls_anuncios = await extraer_urls_resultados(page, url_busqueda)

            urls_nuevas = [u for u in urls_anuncios if u not in urls_procesadas]
            urls_procesadas.update(urls_nuevas)

            if not urls_nuevas:
                print("  → Sin anuncios para esta colonia con el filtro actual.")
                continue

            print(f"  → {len(urls_nuevas)} anuncios únicos a procesar")

            for idx_a, url in enumerate(urls_nuevas, start=1):
                delay = random.uniform(DELAY_MIN_ANUNCIO, DELAY_MAX_ANUNCIO)
                await asyncio.sleep(delay)

                print(f"  [{idx_a}/{len(urls_nuevas)}] {url}")
                registro = await extraer_datos_anuncio(page, url, nombre_colonia)

                if registro:
                    todos_los_registros.append(registro)
                    precio_fmt = (
                        f"${int(registro['precio']):,}"
                        if registro.get("precio")
                        else "N/D"
                    )
                    print(
                        f"      ✓  {registro['tipo_inmueble'] or '?'} | "
                        f"{precio_fmt} | "
                        f"{registro['m2_construccion'] or '?'} m² | "
                        f"{registro['recamaras'] or '?'} rec | "
                        f"{registro['estacionamientos'] or '?'} estac"
                    )
                else:
                    print("      ✗  No se pudieron extraer datos")

            if idx_col < len(colonias_lista) - 1:
                pausa = random.uniform(DELAY_MIN_COLONIA, DELAY_MAX_COLONIA)
                print(f"\n  ⏸  Pausa entre colonias: {pausa:.1f} s")
                await asyncio.sleep(pausa)

        await browser.close()

    # Guardar CSV
    print(f"\n{'='*60}")
    print(f"Scraping completado.")
    print(f"  Anuncios procesados: {len(urls_procesadas)}")
    print(f"  Registros válidos:   {len(todos_los_registros)}")

    if todos_los_registros:
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNAS_CSV)
            writer.writeheader()
            writer.writerows(todos_los_registros)
        print(f"  CSV guardado en:     {OUTPUT_CSV}")
    else:
        print("  ⚠  Sin registros para guardar.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

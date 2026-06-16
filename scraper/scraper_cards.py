"""
Scraper card-based de Inmuebles24 — Mérida, Yucatán.
Fase 4 del proyecto de portafolio dataset-inmuebles-merida.

Estrategia: extraer todos los datos directamente desde las cards de la
página de listado, sin navegar a anuncios individuales.

Ventajas:
  - Solo una request por colonia (página de resultados)
  - Evita el bloqueo de Cloudflare en páginas individuales
  - Los selectores data-qa son más estables que clases CSS

Campos disponibles desde la card:
  precio, m2 (lote o construcción según tipo), recámaras, baños,
  estacionamientos, tipo_inmueble, descripción corta, es_preventa,
  cuota de mantenimiento (cuando aplica)

Campo NO disponible sin visitar el anuncio:
  m2_construccion (para casas; para departamentos m2 lote ≈ m2 construcción)
  antigüedad, descripción completa

Uso:
    conda activate inmuebles-scraper
    python scraper/setup_session.py   # solo si aún no hay sesión guardada
    python scraper/scraper_cards.py
"""

import asyncio
import csv
import re
import random
from datetime import date
from pathlib import Path

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

from config import (
    BASE_URL,
    URL_TEMPLATE,
    COLONIAS,
    DELAY_MIN_COLONIA,
    DELAY_MAX_COLONIA,
    ESPERA_RESULTADOS,
    USER_AGENT,
)


# ---------------------------------------------------------------------------
# Configuración de salida
# ---------------------------------------------------------------------------

OUTPUT_CSV   = Path("data/propiedades_scrapeadas.csv")
SESSION_FILE = Path("scraper/session_state.json")

COLUMNAS_CSV = [
    "url",
    "fecha_scraping",
    "operación",
    "tipo_inmueble",
    "colonia",
    "precio",
    "m2_lote",          # el único m2 visible en la card
    "recamaras",
    "banos",
    "estacionamientos",
    "mantenimiento",    # cuota mensual cuando aparece en la card
    "es_preventa",
    "descripcion",      # descripción corta del card
]


# ---------------------------------------------------------------------------
# Parseo de texto de features
# ---------------------------------------------------------------------------

def _limpiar_precio(texto: str) -> str:
    """'MN 2,285,000' → '2285000'"""
    m = re.search(r'[\d,]+', texto.replace('.', ''))
    if not m:
        return ""
    return m.group().replace(',', '')


def _extraer_numero(texto: str) -> str:
    """Extrae el primer número entero de un string."""
    m = re.search(r'\d+', texto)
    return m.group() if m else ""


def _detectar_preventa(descripcion: str) -> str:
    patron = re.compile(
        r'pre[- ]?venta|en\s+construcci[oó]n|fecha\s+de\s+entrega|'
        r'entrega\s+(?:estimada|programada|inmediata)|obra\s+(?:negra|gris)',
        re.IGNORECASE,
    )
    return "si" if patron.search(descripcion) else "no"


def _tipo_inmueble_desde_url(url: str) -> str:
    """Infiere tipo de inmueble desde el prefijo de URL de Inmuebles24."""
    if "veclapin" in url:
        return "departamento"
    if "veclcain" in url:
        return "casa"
    if "veclcapa" in url:
        return "casa en condominio"
    return ""


# ---------------------------------------------------------------------------
# Extracción de cards de una página de resultados
# ---------------------------------------------------------------------------

async def extraer_cards(page: Page, url_busqueda: str, colonia: str) -> list[dict]:
    """
    Navega a la página de listado de una colonia y extrae los datos de
    todos los cards presentes, sin seguir ningún enlace.
    """
    print(f"  → Cargando: {url_busqueda}")
    try:
        await page.goto(url_busqueda, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(int(ESPERA_RESULTADOS * 1000))
    except PlaywrightTimeout:
        print("    ⚠ Timeout al cargar página de resultados")
        return []

    # Verificar si Cloudflare bloqueó la página
    titulo = ""
    try:
        h1 = await page.query_selector("h1")
        if h1:
            titulo = (await h1.inner_text()).strip()
    except Exception:
        pass

    if "blocked" in titulo.lower() or "error" in titulo.lower():
        print(f"    ✗ Página bloqueada: {titulo}")
        return []

    print(f"    ✓ Página cargada: {titulo[:70]}")

    # Seleccionar todos los cards de propiedades
    cards = await page.query_selector_all('div[data-qa="posting PROPERTY"]')
    print(f"    → {len(cards)} cards encontrados")

    registros = []
    fecha_hoy = date.today().isoformat()

    for card in cards:
        try:
            registro = await _extraer_datos_card(card, colonia, fecha_hoy)
            if registro:
                registros.append(registro)
        except Exception as e:
            print(f"    ⚠ Error en card: {e}")

    return registros


async def _extraer_datos_card(card, colonia: str, fecha: str) -> dict | None:
    """
    Extrae todos los campos disponibles de un card individual.

    Selectores confirmados desde el HTML de resultados.html:
      POSTING_CARD_PRICE       → precio (h2)
      POSTING_CARD_FEATURES    → features: m², rec., baños, estac. (h3 con spans)
      POSTING_CARD_DESCRIPTION → descripción corta (h2 > a)
      expensas                 → cuota de mantenimiento (h2, opcional)
      data-to-posting          → URL del anuncio
    """
    # URL del anuncio (para identificación y tipo_inmueble)
    ruta = await card.get_attribute("data-to-posting") or ""
    url = BASE_URL + ruta.split("?")[0] if ruta else ""

    # Precio
    precio_el = await card.query_selector('[data-qa="POSTING_CARD_PRICE"]')
    precio_txt = await precio_el.inner_text() if precio_el else ""
    precio = _limpiar_precio(precio_txt)

    # Features: m², recámaras, baños, estacionamientos
    features_el = await card.query_selector('[data-qa="POSTING_CARD_FEATURES"]')
    m2_lote = recamaras = banos = estacionamientos = ""
    if features_el:
        spans = await features_el.query_selector_all("span")
        for span in spans:
            txt = (await span.inner_text()).lower().strip()
            if "m²" in txt or "m2" in txt:
                m2_lote = _extraer_numero(txt)
            elif "rec." in txt or "recámara" in txt or "recamara" in txt:
                recamaras = _extraer_numero(txt)
            elif "baño" in txt or "bano" in txt:
                banos = _extraer_numero(txt)
            elif "estac." in txt or "estacionamiento" in txt:
                estacionamientos = _extraer_numero(txt)

    # Mantenimiento (aparece en algunos cards como "MN X,XXX Mantenimiento")
    expensas_el = await card.query_selector('[data-qa="expensas"]')
    mantenimiento = ""
    if expensas_el:
        exp_txt = (await expensas_el.inner_text()).strip()
        if "mantenimiento" in exp_txt.lower():
            mantenimiento = _limpiar_precio(exp_txt)

    # Descripción corta (texto del enlace en el card)
    desc_el = await card.query_selector('[data-qa="POSTING_CARD_DESCRIPTION"] a')
    descripcion = (await desc_el.inner_text()).strip() if desc_el else ""

    # Tipo de inmueble (desde URL)
    tipo_inmueble = _tipo_inmueble_desde_url(url)

    # Si no se obtuvo tipo desde URL, intentar desde el alt de la imagen del card
    if not tipo_inmueble:
        img = await card.query_selector("img[alt]")
        if img:
            alt = (await img.get_attribute("alt") or "").lower()
            if "departamento" in alt:
                tipo_inmueble = "departamento"
            elif "casa" in alt:
                tipo_inmueble = "casa"

    # Detección de preventa
    es_preventa = _detectar_preventa(descripcion)

    # Descartar cards sin precio (probablemente son ads o secciones vacías)
    if not precio:
        return None

    return {
        "url":             url,
        "fecha_scraping":  fecha,
        "operación":       "venta",
        "tipo_inmueble":   tipo_inmueble,
        "colonia":         colonia,
        "precio":          precio,
        "m2_lote":         m2_lote,
        "recamaras":       recamaras,
        "banos":           banos,
        "estacionamientos":estacionamientos,
        "mantenimiento":   mantenimiento,
        "es_preventa":     es_preventa,
        "descripcion":     descripcion,
    }


# ---------------------------------------------------------------------------
# Script principal
# ---------------------------------------------------------------------------

async def main() -> None:
    print("=" * 60)
    print("Scraper card-based — Inmuebles24 · Mérida, Yucatán")
    print(f"Colonias: {len(COLONIAS)} | Fecha: {date.today().isoformat()}")
    print("=" * 60)

    todos_los_registros: list[dict] = []
    urls_vistas: set[str] = set()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)

        # Cargar sesión guardada si existe
        if SESSION_FILE.exists():
            print(f"  → Cargando sesión: {SESSION_FILE}")
            context = await browser.new_context(
                user_agent=USER_AGENT,
                storage_state=str(SESSION_FILE),
            )
        else:
            print("  ⚠ Sin sesión guardada. Corre setup_session.py primero.")
            context = await browser.new_context(user_agent=USER_AGENT)

        # Parches anti-detección
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['es-MX','es','en-US']});
            window.chrome = { runtime: {} };
        """)

        page = await context.new_page()

        # Visita homepage para establecer sesión antes de los listados
        print("  → Calentando sesión...")
        await page.goto("https://www.inmuebles24.com", wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3_000)

        colonias_lista = list(COLONIAS.items())

        for idx, (nombre_colonia, slug) in enumerate(colonias_lista):
            print(f"\n{'─'*50}")
            print(f"[{idx+1}/{len(colonias_lista)}] {nombre_colonia}")

            url_busqueda = URL_TEMPLATE.format(slug=slug)
            registros = await extraer_cards(page, url_busqueda, nombre_colonia)

            # Filtrar duplicados
            nuevos = [r for r in registros if r["url"] not in urls_vistas]
            urls_vistas.update(r["url"] for r in nuevos)
            todos_los_registros.extend(nuevos)

            print(f"    → {len(nuevos)} registros nuevos (total: {len(todos_los_registros)})")

            # Resumen rápido de los primeros registros
            for r in nuevos[:3]:
                precio_fmt = f"${int(r['precio']):,}" if r["precio"] else "N/D"
                print(f"      {r['tipo_inmueble'] or '?':12} | {precio_fmt:>14} | "
                      f"{r['m2_lote'] or '?':>5} m² | "
                      f"{r['recamaras'] or '?'} rec | {r['banos'] or '?'} baños")

            # Pausa entre colonias (excepto la última)
            if idx < len(colonias_lista) - 1:
                pausa = random.uniform(DELAY_MIN_COLONIA, DELAY_MAX_COLONIA)
                print(f"    ⏸ Pausa: {pausa:.1f} s")
                await asyncio.sleep(pausa)

        await browser.close()

    # Guardar CSV
    print(f"\n{'='*60}")
    print(f"Registros totales: {len(todos_los_registros)}")
    print(f"URLs únicas:       {len(urls_vistas)}")

    if todos_los_registros:
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNAS_CSV)
            writer.writeheader()
            writer.writerows(todos_los_registros)
        print(f"CSV guardado en:   {OUTPUT_CSV}")
    else:
        print("⚠ Sin registros para guardar.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

"""
Configuración del scraper de Inmuebles24 — Mérida, Yucatán.
Fase 4 del proyecto de portafolio dataset-inmuebles-merida.
"""

# URL base del sitio
BASE_URL = "https://www.inmuebles24.com"

# Plantilla de URL de búsqueda por colonia.
# Filtra: casas o departamentos, venta, Mérida, publicados en el último mes.
URL_TEMPLATE = (
    "https://www.inmuebles24.com/casas-o-departamentos-en-venta-en-merida"
    "-publicado-hace-menos-de-1-mes-{slug}.html"
)

# Colonias del dataset original con sus slugs confirmados de la URL de Inmuebles24.
# Clave: nombre normalizado (snake_case) — Valor: slug que aparece en la URL
COLONIAS = {
    "altabrisa":              "drc-altabrisa",
    "chuburna_de_hidalgo":    "drc-chuburna-de-hidalgo",
    "santa_gertrudis_copo":   "drc-santa-gertrudis-copo",
    "garcia_gineres":         "drc-garcia-gineres",
    "francisco_de_montejo":   "drc-francisco-de-montejo",
    "yucatan_country_club":   "drc-country-club",
}

# Comportamiento humano: delays aleatorios entre requests (segundos)
DELAY_MIN_ANUNCIO  = 3.0   # Entre anuncios individuales
DELAY_MAX_ANUNCIO  = 7.0
DELAY_MIN_COLONIA  = 8.0   # Entre colonias
DELAY_MAX_COLONIA  = 15.0
ESPERA_RESULTADOS  = 4.0   # Tras cargar página de listado
ESPERA_ANUNCIO     = 2.5   # Tras cargar anuncio individual

# User-Agent: imitar navegador de escritorio real
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

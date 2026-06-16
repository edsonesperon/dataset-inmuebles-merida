"""
Carga del modelo serializado y lógica de predicción.
Separa la lógica de ML de la capa de API (main.py).
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Rutas a los artefactos del modelo (relativas a la raíz del repo)
# ---------------------------------------------------------------------------
_RAIZ = Path(__file__).resolve().parent.parent
_RUTA_MODELO   = _RAIZ / "modelo_gb.pkl"
_RUTA_COLUMNAS = _RAIZ / "columnas_modelo.pkl"


# ---------------------------------------------------------------------------
# Carga en memoria al iniciar la API (una sola vez)
# ---------------------------------------------------------------------------
modelo    = joblib.load(_RUTA_MODELO)
columnas  = joblib.load(_RUTA_COLUMNAS)   # lista de 16 features en orden exacto


# ---------------------------------------------------------------------------
# Pipeline de predicción
# ---------------------------------------------------------------------------

COLONIAS_VALIDAS = [
    "altabrisa",
    "chuburna de hidalgo",
    "francisco de montejo",
    "garcia gineres",
    "santa gertrudis copo",
    "yucatan country club",
]


def preparar_features(datos: dict) -> pd.DataFrame:
    """
    Transforma el dict del request en un DataFrame con las 16 features
    que espera el modelo, en el orden exacto en que fue entrenado.

    Transformaciones aplicadas (idénticas al notebook de modelado):
      - log_m2_construccion = log(m2_construccion)
      - es_casa             = 1 si tipo_inmueble == 'casa', else 0
      - bool → int          para todas las variables binarias
      - One-hot encoding    de colonia (6 dummies, sin drop_first)
    """
    fila = {
        "log_m2_construccion":         np.log(datos["m2_construccion"]),
        "recamaras":                    datos["recamaras"],
        "banos":                        datos["banos"],
        "estacionamientos":             datos["estacionamientos"],
        "es_preventa":                  int(datos["es_preventa"]),
        "es_casa":                      int(datos["tipo_inmueble"] == "casa"),
        "tiene_piscina":                int(datos["tiene_piscina"]),
        "tiene_cuarto_servicio":        int(datos["tiene_cuarto_servicio"]),
        "es_una_planta":                int(datos["es_una_planta"]),
        "tiene_mantenimiento_con_monto":int(datos["tiene_mantenimiento_con_monto"]),
    }

    # Inicializar todas las dummies de colonia en 0
    for col in columnas:
        if col.startswith("colonia_"):
            fila[col] = 0

    # Activar la dummy de la colonia seleccionada
    clave_colonia = f"colonia_{datos['colonia']}"
    if clave_colonia in fila:
        fila[clave_colonia] = 1

    # Crear DataFrame y reordenar columnas para que coincidan exactamente
    # con el orden en que el modelo fue entrenado
    df = pd.DataFrame([fila])
    df = df[columnas]

    return df


def predecir(datos: dict) -> float:
    """
    Devuelve el precio estimado en MXN.
    El modelo predice log(precio); se invierte la transformación con exp().
    """
    X = preparar_features(datos)
    log_precio_pred = modelo.predict(X)[0]
    precio_mxn = np.exp(log_precio_pred)
    return float(precio_mxn)

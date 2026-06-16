"""
API de valuación inmobiliaria — Mérida, Yucatán.
Fase 5 del proyecto de portafolio dataset-inmuebles-merida.

Endpoint principal:
  POST /predecir  →  recibe características de una propiedad
                     y devuelve el precio estimado de mercado en MXN.

Documentación interactiva disponible en:
  http://localhost:8000/docs   (Swagger UI)
  http://localhost:8000/redoc  (ReDoc)
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from schemas import PropiedadInput, PrediccionOutput
from modelo import predecir

# ---------------------------------------------------------------------------
# Instancia de la aplicación
# ---------------------------------------------------------------------------

app = FastAPI(
    title="API de Valuación Inmobiliaria — Mérida, Yucatán",
    description=(
        "Estima el precio de mercado de una propiedad en Mérida, Yucatán "
        "a partir de sus características. Basada en un modelo Gradient Boosting "
        "entrenado sobre 59 propiedades recolectadas de Inmuebles24 (2026)."
    ),
    version="1.0.0",
    contact={
        "name": "Edson Esperon",
        "url": "https://github.com/edsonesperon/dataset-inmuebles-merida",
    },
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def raiz():
    """Redirige a la documentación."""
    return JSONResponse(
        content={
            "mensaje": "API de Valuación Inmobiliaria — Mérida, Yucatán",
            "documentacion": "/docs",
            "version": "1.0.0",
        }
    )


@app.get("/salud", tags=["Estado"])
def salud():
    """Verifica que la API está activa y el modelo está cargado."""
    return {"estado": "activo", "modelo": "Gradient Boosting"}


@app.post(
    "/predecir",
    response_model=PrediccionOutput,
    tags=["Predicción"],
    summary="Estima el precio de mercado de una propiedad",
    response_description="Precio estimado en pesos mexicanos con metadatos del modelo",
)
def predecir_precio(propiedad: PropiedadInput) -> PrediccionOutput:
    """
    Recibe las características de una propiedad y devuelve el precio
    estimado de mercado en pesos mexicanos (MXN).

    El modelo aplica internamente:
    - Transformación logarítmica de m2_construccion
    - One-hot encoding de colonia
    - Predicción con Gradient Boosting
    - Inversión de log(precio) → precio via exp()
    """
    try:
        precio = predecir(propiedad.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en predicción: {str(e)}")

    return PrediccionOutput(
        precio_estimado_mxn=round(precio, 2),
        precio_estimado_formateado=f"${precio:,.0f} MXN",
    )

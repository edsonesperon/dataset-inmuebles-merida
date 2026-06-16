"""
Esquemas de validación de datos para la API de valuación inmobiliaria.
Define la estructura del request (PropiedadInput) y del response (PrediccionOutput).
"""

from pydantic import BaseModel, Field
from typing import Literal


class PropiedadInput(BaseModel):
    """
    Características de la propiedad para estimar su precio de mercado.
    Todos los campos requeridos excepto los que tienen valor por defecto.
    """

    tipo_inmueble: Literal["casa", "departamento"] = Field(
        ...,
        description="Tipo de inmueble: 'casa' o 'departamento'",
        examples=["casa"],
    )
    colonia: Literal[
        "altabrisa",
        "chuburna de hidalgo",
        "francisco de montejo",
        "garcia gineres",
        "santa gertrudis copo",
        "yucatan country club",
    ] = Field(
        ...,
        description="Colonia donde se ubica la propiedad",
        examples=["altabrisa"],
    )
    m2_construccion: float = Field(
        ...,
        gt=0,
        description="Metros cuadrados de construcción",
        examples=[150.0],
    )
    recamaras: int = Field(
        ...,
        ge=0,
        description="Número de recámaras",
        examples=[3],
    )
    banos: int = Field(
        ...,
        ge=0,
        description="Número de baños completos",
        examples=[2],
    )
    estacionamientos: int = Field(
        ...,
        ge=0,
        description="Número de cajones de estacionamiento",
        examples=[2],
    )
    es_preventa: bool = Field(
        default=False,
        description="True si la propiedad está en preventa",
        examples=[False],
    )
    tiene_piscina: bool = Field(
        default=False,
        description="True si la propiedad tiene piscina o alberca",
        examples=[False],
    )
    tiene_cuarto_servicio: bool = Field(
        default=False,
        description="True si la propiedad tiene cuarto de servicio",
        examples=[False],
    )
    es_una_planta: bool = Field(
        default=False,
        description="True si la propiedad es de una sola planta",
        examples=[False],
    )
    tiene_mantenimiento_con_monto: bool = Field(
        default=False,
        description="True si el anuncio especifica cuota de mantenimiento con monto",
        examples=[False],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tipo_inmueble": "casa",
                    "colonia": "altabrisa",
                    "m2_construccion": 200,
                    "recamaras": 3,
                    "banos": 2,
                    "estacionamientos": 2,
                    "es_preventa": False,
                    "tiene_piscina": True,
                    "tiene_cuarto_servicio": False,
                    "es_una_planta": False,
                    "tiene_mantenimiento_con_monto": False,
                }
            ]
        }
    }


class PrediccionOutput(BaseModel):
    """Respuesta del endpoint de predicción."""

    precio_estimado_mxn: float = Field(
        ...,
        description="Precio estimado de mercado en pesos mexicanos",
    )
    precio_estimado_formateado: str = Field(
        ...,
        description="Precio estimado formateado con separadores de miles",
    )
    modelo: str = Field(
        default="Gradient Boosting — entrenado sobre 59 propiedades en Mérida, Yucatán (2026)",
        description="Descripción del modelo utilizado",
    )
    advertencia: str = Field(
        default=(
            "Estimación basada en precios de lista de Inmuebles24. "
            "No constituye una valuación formal."
        ),
        description="Advertencia sobre el alcance de la estimación",
    )

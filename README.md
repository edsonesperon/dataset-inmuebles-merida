# Dataset de Propiedades Inmobiliarias — Mérida, Yucatán

## Problema

Los compradores, agentes e inversionistas inmobiliarios en Mérida 
carecen de datos sistemáticos y actualizados para evaluar si el 
precio de una propiedad es consistente con el mercado actual de 
su zona. Las fuentes oficiales disponibles (INFONAVIT, SHF) 
registran transacciones pasadas con varios meses de rezago y sin 
granularidad por colonia. Este proyecto construye una alternativa 
basada en listados activos.

## Objetivo

Construir un dataset de propiedades en venta en Mérida a partir 
de listados activos y desarrollar, en fases posteriores, un modelo 
de valuación estadística que estime el precio esperado de una 
propiedad dado su tipo, ubicación y características.

## Estado actual

**Fase 1 completada:** 60 propiedades recolectadas en colonias 
representativas de distintos segmentos del mercado de Mérida.

**Fase 2 completada:** análisis exploratorio inicial con Python y pandas. 
Notebook en `notebooks/01_eda_inicial.ipynb`. Hallazgos clave: distribuciones, 
segmentos de precio por colonia, multicolinealidad entre variables de superficie, 
y features candidatas para el modelo extraídas del campo `notas`.

**Fase 3 en progreso:** feature engineering y construcción del modelo de 
valuación con scikit-learn. Estructurada en tres partes:

- **Parte 1 completada:** ingeniería de características. Notebook en 
  `notebooks/02_feature_engineering.ipynb`. Extracción de variables binarias 
  desde `notas`, transformación logarítmica del precio, protocolo de validación 
  cruzada estratificada y prueba estadística de preventa (Mann-Whitney, p=0.018).
- **Parte 2 completada:** modelo baseline de regresión lineal múltiple sobre 
  `log(precio)`. Notebook en `notebooks/03_modelo_baseline.ipynb`. RMSE=6.90M ± 2.05M 
  y MAE=3.19M ± 0.84M MXN en validación cruzada estratificada (k=5).
- **Parte 3 (próxima):** modelo comparativo con Random Forest y Gradient Boosting. 
  Notebook en `notebooks/04_modelo_comparativo.ipynb`.

**Fases siguientes:** automatización de recolección con scraper (Playwright) 
y despliegue del modelo como servicio (FastAPI).

## Descripción del dataset

Dataset de 60 propiedades en venta en Mérida, Yucatán, recolectadas 
manualmente de Inmuebles24 entre mayo y junio de 2026. Cubre casas y 
departamentos en 6 colonias representativas de distintos segmentos del 
mercado.

**Distribución por colonia:**
- Altabrisa: 10
- Santa Gertrudis Copó: 10
- García Ginerés: 10
- Chuburná de Hidalgo: 10
- Francisco de Montejo: 9
- Yucatán Country Club: 11

**Composición:**
- 44 casas (73%), 16 departamentos (27%)
- 50 propiedades terminadas, 10 en preventa
- Rango de precios: $1.79M – $41M MXN
- Rango de superficie de construcción: 42 – 2,502 m²

**Estructura:** archivo CSV con 15 columnas (ver Diccionario de columnas).

**Formato:** `data/propiedades.csv`


## Colonias incluidas y justificación

- **Altabrisa / Montebello:** segmento alto consolidado. Referencia de 
  precios máximos del mercado formal.
- **Santa Gertrudis Copó / Temozon Norte:** zona de crecimiento 
  acelerado en el corredor norte. Relevante por la expansión urbana 
  vinculada al Tren Maya.
- **García Ginerés / Itzimná:** segmento medio-alto en colonia 
  tradicional. Representa el mercado establecido de clase media 
  profesional.
- **Miguel Hidalgo / Chuburná:** segmento medio. Permite comparar 
  precio por m² con zonas de mayor plusvalía.
- **Francisco de Montejo / Cholul:** segmento medio en expansión. 
  Zona de transición entre ciudad consolidada y periferia en 
  crecimiento.
- **Corredor Komchen-Tamamché (carretera a Progreso):** privadas y 
  countrys de baja densidad. Segmento alto con características 
  distintas a colonias urbanas: lotes amplios, desarrollos cerrados, 
  y perfil de comprador orientado a espacio y exclusividad.  La 
  recolección se realizó en Yucatán Country Club por concentrar la 
  mayor disponibilidad de anuncios recientes en el corredor. Permite 
  comparar precio por m² entre densidad alta y baja dentro del mismo 
  segmento económico.

## Metodología de recolección
- Fuente: Inmuebles24
- Filtros aplicados: operación = venta, fecha de publicación = 
  últimos 30 días, sin filtros adicionales para no sesgar la muestra
- La evidencia primaria de cada registro es el PDF guardado localmente
  en evidencia/. No se publica en el repositorio para proteger datos 
  personales de los anunciantes (teléfonos, nombres).
- Se intenta archivar cada anuncio en Wayback Machine, pero 
  Inmuebles24 lo bloquea sistemáticamente. El campo url_archivo 
  queda en blanco en la mayoría de los registros. 
  

## Diccionario de columnas
| Columna | Descripción |
|---|---|
| fecha_registro | Fecha en que se copió el dato |
| url | URL original del anuncio |
| url_archivo | URL del anuncio archivado en Wayback Machine. Queda en blanco cuando Inmuebles24 bloquea el archivado (comportamiento habitual)|
| operacion | venta (única operación registrada en el dataset) |
| tipo_inmueble | casa / departamento (terrenos, oficinas y bodegas excluidos) |
| colonia | Nombre exacto como aparece en el anuncio |
| precio | Precio en pesos, solo número sin comas |
| m2_construccion | Metros cuadrados de construcción |
| m2_terreno | Metros cuadrados de terreno |
| recamaras | Número de recámaras |
| banos | Número de baños |
| estacionamientos | Número de lugares de estacionamiento |
| antigüedad | Antigüedad en años si aparece en el anuncio |
| es_preventa | si / no |
| notas | Observaciones relevantes del anuncio |

## Limitaciones conocidas
- Muestra manual limitada a 60 propiedades
- Los precios son precios de lista, no precios de cierre
- No incluye propiedades sin precio publicado
- Inmuebles24 bloquea el archivado en Wayback Machine. 
  La evidencia principal de cada registro es el PDF 
  guardado localmente.
- Los anuncios de Inmuebles24 presentan inconsistencias frecuentes 
  entre los datos de la ficha técnica y la descripción del anuncio, 
  incluyendo discrepancias en m2, colonia y precio. El dato registrado 
  en el CSV corresponde siempre a la ficha técnica. Las discrepancias 
  relevantes se documentan en el campo notas.
- Las propiedades de Francisco de Montejo presentan frecuentemente 
  potencial de uso comercial que puede estar reflejado en el precio 
  de lista, lo que limita su comparación directa con propiedades 
  de uso estrictamente residencial en otras colonias del dataset.
- La muestra de Francisco de Montejo contiene 9 propiedades en lugar 
  de 10. No se encontraron anuncios adicionales dentro del rango de 
  60 días establecido como límite de extensión del filtro estándar.
- La mayoría de los anuncios no especifica la antigüedad del 
  inmueble. El campo antiguedad queda en blanco en la mayor parte 
  de los registros, incluso en propiedades claramente terminadas 
  o con varios años de construidas.
- Multicolinealidad severa entre `m2_construccion` y `m2_terreno` (r=0.95) 
  detectada en el EDA. No podrán incluirse ambas como predictores en una 
  regresión lineal.
- Dataset desbalanceado por tipo de inmueble: 73% casas, 27% departamentos. 
  El modelo tendrá mayor capacidad predictiva para casas.
- El 17% de las propiedades están en preventa, con dinámicas de precio 
  potencialmente distintas a propiedades terminadas. Su tratamiento se 
  definirá con prueba estadística en Fase 3.
- Variables cualitativas (seguridad, amenidades, prestigio, calidad de 
  servicios) no capturadas. Quedan absorbidas en la variable `colonia`, 
  que actúa como proxy compuesto.

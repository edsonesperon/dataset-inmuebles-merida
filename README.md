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

Fase 1 — Recolección manual en curso. Colonias representativas 
de distintos segmentos del mercado de Mérida.

Fases siguientes: automatización de recolección con scraper, 
análisis exploratorio, modelo de valuación.

## Descripción del dataset

[aquí continúa exactamente lo que ya tienes]

## Descripción
Dataset de propiedades en venta recolectadas manualmente de Inmuebles24 
entre mayo y junio de 2026. Cubre casas y departamentos en colonias 
representativas de distintos segmentos del mercado de Mérida.

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
  y perfil de comprador orientado a espacio y exclusividad. Permite 
  comparar precio por m² entre densidad alta y baja dentro del mismo 
  segmento económico.

## Metodología de recolección
- Fuente: Inmuebles24
- Filtros aplicados: operación = compra, fecha de publicación = 
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
| operacion | venta / renta / traspaso |
| tipo_inmueble | casa / departamento / terreno |
| colonia | Nombre exacto como aparece en el anuncio |
| precio | Precio en pesos, solo número sin comas |
| m2_construccion | Metros cuadrados de construcción |
| m2_terreno | Metros cuadrados de terreno |
| recamaras | Número de recámaras |
| banos | Número de baños |
| estacionamientos | Número de lugares de estacionamiento |
| antiguedad | Antigüedad en años si aparece en el anuncio |
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
- La sesión de Francisco de Montejo contiene 9 propiedades en lugar 
  de 10. No se encontraron anuncios adicionales dentro del rango de 
  60 días establecido como límite de extensión del filtro estándar.    

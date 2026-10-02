# Sección 4 — Dashboard ligero de monitoreo operativo

Dashboard ejecutivo construido con **Streamlit + Plotly**. Los datos se generan de forma sintética dentro del propio código, por lo que la aplicación no requiere archivos externos.

## Por qué elegí Streamlit

Elegí Streamlit porque permite construir una aplicación web interactiva directamente desde Python, sin requerir licencias adicionales. Para un tablero operativo de este tipo ofrece una implementación ligera, fácil de mantener y sencilla de ejecutar por otro analista. Plotly complementa la solución con visualizaciones interactivas y legibles.

## Cómo ejecutar — máximo 3 pasos

1. Desde la raíz del proyecto: `python -m pip install -r requirements.txt`
2. Ejecute: `python -m streamlit run seccion_4/app.py`
3. Abra en el navegador la dirección local indicada por Streamlit (normalmente `http://localhost:8501`).

## Qué incluye

- Total de casos del mes y variación frente al mes anterior.
- Costo total y variación frente al mes anterior.
- Tasa de incidencia por cada 100 trabajadores y variación frente al mes anterior.
- Tendencia mensual de los últimos 12 meses con línea de promedio histórico.
- Distribución de casos leves/graves.
- Distribución por clase de riesgo 1 a 5.
- Top 10 de clientes con más casos y clase de riesgo visible.
- Filtros por sector y clase de riesgo que actualizan todo el tablero.
- Lectura ejecutiva automática para orientar la revisión de prioridades.

## Conexión a un Lakehouse en producción

En producción reemplazaría la función que genera datos sintéticos por una capa de acceso al Lakehouse, usando el mecanismo de conexión definido por la plataforma (por ejemplo, un endpoint SQL o una tabla administrada). Mantendría separadas la obtención de datos y la lógica visual, de modo que el tablero consuma tablas o vistas ya gobernadas y no replique definiciones de negocio. Los indicadores críticos, como la tasa de incidencia, deberían provenir de una capa semántica o lógica central validada para que el mismo concepto entregue el mismo resultado en cualquier reporte.

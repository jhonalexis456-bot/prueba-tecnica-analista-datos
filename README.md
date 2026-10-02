# Prueba Técnica - Analista de Datos y Analítica

Solución organizada por secciones para la prueba técnica. El proyecto combina respuestas conceptuales, consultas SQL, automatización de calidad de datos en Python y un dashboard operativo ligero.

## Estructura del repositorio

```text
Prueba_Tecnica_Analista_Datos/
├── README.md
├── requirements.txt
├── seccion_3/
│   ├── generar_datos.py
│   ├── validar_calidad.py
│   ├── main.py
│   ├── verificar_seccion3.py
│   ├── README.md
│   ├── datos/
│   └── output/
├── seccion_4/
│   ├── app.py
│   └── README.md
└── documentacion/
    ├── Respuestas_Prueba_Tecnica_Analista_Datos.docx
    ├── seccion_1_powerbi/
    ├── seccion_2_sql/
    ├── seccion_5_migracion/
    └── seccion_6_ia/
```

## Requisitos

- Python 3.11 o superior. La entrega fue validada en Python 3.14.4.
- Instalar las dependencias desde la raíz del proyecto:

```bash
python -m pip install -r requirements.txt
```

## Sección 3 - Calidad del dato

Desde la raíz del proyecto:

```bash
python seccion_3/main.py
```

La ejecución:

1. genera más de 1.000 registros sintéticos de facturación con errores controlados;
2. evalúa completitud, validez, unicidad, consistencia y oportunidad;
3. exporta un reporte JSON, registros válidos en Parquet y registros rechazados en Excel con su motivo de rechazo.

Para ejecutar una comprobación rápida de coherencia:

```bash
python seccion_3/verificar_seccion3.py
```

Más detalle en `seccion_3/README.md`.

## Sección 4 - Dashboard ligero

Desde la raíz del proyecto:

```bash
python -m streamlit run seccion_4/app.py
```

El dashboard genera sus datos dentro del propio código y no depende de archivos externos. Incluye indicadores con comparación frente al período anterior, tendencia de 12 meses, promedio histórico, distribuciones de casos, top 10 de clientes, filtros globales y una lectura ejecutiva.

Más detalle en `seccion_4/README.md`.

## Respuestas escritas - Secciones 1, 2, 5 y 6

El documento consolidado se encuentra en:

`documentacion/Respuestas_Prueba_Tecnica_Analista_Datos.docx`

Como soporte y trazabilidad, la carpeta `documentacion/` también conserva las respuestas fuente en Markdown y las consultas SQL de la Sección 2 en archivos independientes.

## Consultas SQL

Las consultas completas están disponibles en:

- `documentacion/seccion_2_sql/2_1_consulta_corregida.sql`
- `documentacion/seccion_2_sql/2_2_priorizacion_visitas.sql`
- `documentacion/seccion_2_sql/2_3_pipeline_diario.sql`

## Reproducibilidad

Los datos utilizados en las secciones prácticas son sintéticos y se generan programáticamente con semillas controladas. Esto permite revisar la lógica sin depender de sistemas, credenciales o archivos externos.

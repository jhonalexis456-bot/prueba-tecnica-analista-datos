# Sección 3 - Validación de calidad del dato

## Qué resuelve

Este ejercicio simula el control automático que se ejecutaría antes de permitir que un archivo de facturación entre al pipeline de datos.

El proceso crea una base sintética con más de 1.000 registros, introduce errores de forma controlada y valida cinco dimensiones de calidad:

- **Completitud:** los cuatro campos obligatorios deben estar informados.
- **Validez:** ID, fecha y valores numéricos deben respetar el formato y rango esperado.
- **Unicidad:** no debe repetirse `id_cliente + periodo`.
- **Consistencia:** si existe valor de contrato, debe existir al menos un trabajador activo.
- **Oportunidad:** el período no puede ser futuro ni tener más de 60 días de atraso.

## Cómo se calcula el score

Para cada dimensión se calcula el porcentaje de registros que **no** incumplen esa regla:

```text
score dimensión = 100 × (1 - registros que fallan / total de registros)
```

Un mismo registro puede fallar varias dimensiones. Por esa razón, la suma de fallas por dimensión puede superar la cantidad total de registros rechazados.

## Ejecución

Desde la raíz del repositorio:

1. `python -m pip install -r requirements.txt`
2. `python seccion_3/main.py`
3. Revise los archivos generados en `seccion_3/output/`.

## Archivos generados

- `datos/facturacion_prueba.csv`: datos sintéticos de entrada.
- `output/reporte_calidad.json`: total de registros, válidos, rechazados y score por dimensión.
- `output/registros_validos.parquet`: registros que aprobaron todas las reglas.
- `output/registros_rechazados.xlsx`: registros rechazados con banderas y razón de rechazo.

## Decisiones de diseño

Los formatos inconsistentes no se corrigen silenciosamente: se rechazan para evitar que una transformación automática interprete un valor de forma equivocada. Los nulos se penalizan en **Completitud**, pero no nuevamente en **Validez**, para evitar doble penalización por el mismo problema.

La combinación `id_cliente + periodo` se considera la llave de unicidad del archivo. Cuando existe un duplicado, se marcan todas las filas involucradas porque la combinación deja de ser única dentro del conjunto.

## Verificación rápida

Después de instalar las dependencias puede ejecutarse:

```bash
python seccion_3/verificar_seccion3.py
```

Esta comprobación valida que se generen al menos 1.000 registros, que todo registro quede clasificado como válido o rechazado, que los rechazados tengan motivo y que los válidos no conserven duplicados por cliente y período.

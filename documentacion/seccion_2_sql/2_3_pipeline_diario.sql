/*
Seccion 2.3 - Consulta base para pipeline diario del tablero ejecutivo
Dialect: T-SQL / SQL endpoint compatible con Microsoft Fabric.

Corte: dia anterior a la ejecucion.
Se agregan las fuentes antes de unirlas para evitar duplicaciones.
*/

WITH parametros AS (
    SELECT DATEADD(day, -1, CAST(CURRENT_TIMESTAMP AS date)) AS fecha_corte
),
fechas AS (
    SELECT
        fecha_corte,
        DATEFROMPARTS(YEAR(fecha_corte), MONTH(fecha_corte), 1) AS inicio_mes_actual,
        DATEADD(
            month,
            -1,
            DATEFROMPARTS(YEAR(fecha_corte), MONTH(fecha_corte), 1)
        ) AS inicio_mes_anterior
    FROM parametros
),
casos_cliente AS (
    SELECT
        ca.id_cliente,
        SUM(
            CASE
                WHEN ca.fecha_ocurrencia >= f.inicio_mes_actual
                 AND ca.fecha_ocurrencia <= f.fecha_corte
                THEN 1 ELSE 0
            END
        ) AS casos_mes_actual,
        SUM(
            CASE
                WHEN ca.fecha_ocurrencia >= f.inicio_mes_anterior
                 AND ca.fecha_ocurrencia < f.inicio_mes_actual
                THEN 1 ELSE 0
            END
        ) AS casos_mes_anterior
    FROM casos ca
    CROSS JOIN fechas f
    WHERE ca.fecha_ocurrencia >= f.inicio_mes_anterior
      AND ca.fecha_ocurrencia <= f.fecha_corte
    GROUP BY ca.id_cliente
),
facturacion_ordenada AS (
    SELECT
        fac.id_cliente,
        fac.periodo,
        fac.trabajadores_activos,
        ROW_NUMBER() OVER (
            PARTITION BY fac.id_cliente
            ORDER BY fac.periodo DESC
        ) AS rn
    FROM facturacion fac
    CROSS JOIN fechas f
    WHERE fac.periodo <= f.fecha_corte
),
trabajadores_actuales AS (
    SELECT
        id_cliente,
        trabajadores_activos
    FROM facturacion_ordenada
    WHERE rn = 1
),
prevencion_30d AS (
    SELECT
        pr.id_cliente,
        COUNT(*) AS actividades_prevencion_30d
    FROM prevencion pr
    CROSS JOIN fechas f
    WHERE pr.fecha >= DATEADD(day, -29, f.fecha_corte)
      AND pr.fecha <= f.fecha_corte
    GROUP BY pr.id_cliente
),
base AS (
    SELECT
        c.id_cliente,
        c.nombre,
        c.sector,
        c.clase_riesgo,
        f.fecha_corte,
        COALESCE(ca.casos_mes_actual, 0) AS casos_mes_actual,
        COALESCE(ca.casos_mes_anterior, 0) AS casos_mes_anterior,
        COALESCE(ca.casos_mes_actual, 0) - COALESCE(ca.casos_mes_anterior, 0)
            AS variacion_casos_abs,
        CASE
            WHEN COALESCE(ca.casos_mes_anterior, 0) > 0
                THEN (
                    COALESCE(ca.casos_mes_actual, 0)
                    - COALESCE(ca.casos_mes_anterior, 0)
                ) * 100.0 / ca.casos_mes_anterior
            ELSE NULL
        END AS variacion_casos_pct,
        t.trabajadores_activos,
        CASE
            WHEN t.trabajadores_activos > 0
                THEN COALESCE(ca.casos_mes_actual, 0) * 100.0 / t.trabajadores_activos
            ELSE NULL
        END AS tasa_incidencia,
        COALESCE(pr.actividades_prevencion_30d, 0) AS actividades_prevencion_30d
    FROM clientes c
    CROSS JOIN fechas f
    LEFT JOIN casos_cliente ca
        ON c.id_cliente = ca.id_cliente
    LEFT JOIN trabajadores_actuales t
        ON c.id_cliente = t.id_cliente
    LEFT JOIN prevencion_30d pr
        ON c.id_cliente = pr.id_cliente
    WHERE c.estado = 'activo'
)
SELECT
    id_cliente,
    nombre,
    sector,
    clase_riesgo,
    fecha_corte,
    casos_mes_actual,
    casos_mes_anterior,
    variacion_casos_abs,
    ROUND(variacion_casos_pct, 2) AS variacion_casos_pct,
    trabajadores_activos,
    ROUND(tasa_incidencia, 2) AS tasa_incidencia,
    actividades_prevencion_30d,
    CASE
        WHEN tasa_incidencia IS NULL THEN 'sin dato'
        WHEN tasa_incidencia > 5 THEN 'critico'
        WHEN tasa_incidencia >= 2 THEN 'moderado'
        ELSE 'bajo'
    END AS clasificacion
FROM base;

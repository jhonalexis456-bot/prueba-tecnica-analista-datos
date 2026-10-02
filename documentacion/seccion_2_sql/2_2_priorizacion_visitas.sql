/*
Seccion 2.2 - Top 15 clientes que requieren atencion prioritaria
Dialect: T-SQL / SQL endpoint compatible con Microsoft Fabric.

Criterios del puntaje (0-100):
- Casos graves recientes: hasta 30 puntos.
- Tasa de incidencia de los ultimos 90 dias: hasta 25 puntos.
- Clase de riesgo: hasta 20 puntos.
- Tiempo sin actividad de prevencion: hasta 15 puntos.
- Costo de casos relativo al resto de clientes: hasta 10 puntos.

Los pesos son transparentes y deberian validarse con el area de negocio antes
de convertirlos en una regla productiva definitiva.
*/

WITH parametros AS (
    SELECT CAST(CURRENT_TIMESTAMP AS date) AS fecha_corte
),
casos_90d AS (
    SELECT
        ca.id_cliente,
        COUNT(*) AS casos_90d,
        SUM(CASE WHEN ca.tipo = 'grave' THEN 1 ELSE 0 END) AS graves_90d,
        SUM(COALESCE(ca.dias_ausencia, 0)) AS dias_ausencia_90d,
        SUM(COALESCE(ca.costo, 0)) AS costo_90d
    FROM casos ca
    CROSS JOIN parametros p
    WHERE ca.fecha_ocurrencia >= DATEADD(day, -89, p.fecha_corte)
      AND ca.fecha_ocurrencia <= p.fecha_corte
    GROUP BY ca.id_cliente
),
facturacion_ordenada AS (
    SELECT
        f.id_cliente,
        f.periodo,
        f.trabajadores_activos,
        ROW_NUMBER() OVER (
            PARTITION BY f.id_cliente
            ORDER BY f.periodo DESC
        ) AS rn
    FROM facturacion f
    CROSS JOIN parametros p
    WHERE f.periodo <= p.fecha_corte
),
trabajadores_actuales AS (
    SELECT
        id_cliente,
        trabajadores_activos
    FROM facturacion_ordenada
    WHERE rn = 1
),
prevencion_cliente AS (
    SELECT
        pr.id_cliente,
        MAX(pr.fecha) AS ultima_prevencion
    FROM prevencion pr
    CROSS JOIN parametros p
    WHERE pr.fecha <= p.fecha_corte
    GROUP BY pr.id_cliente
),
base AS (
    SELECT
        c.id_cliente,
        c.nombre,
        c.sector,
        c.clase_riesgo,
        COALESCE(ca.casos_90d, 0) AS casos_90d,
        COALESCE(ca.graves_90d, 0) AS graves_90d,
        COALESCE(ca.dias_ausencia_90d, 0) AS dias_ausencia_90d,
        COALESCE(ca.costo_90d, 0) AS costo_90d,
        t.trabajadores_activos,
        pr.ultima_prevencion,
        CASE
            WHEN t.trabajadores_activos > 0
                THEN COALESCE(ca.casos_90d, 0) * 100.0 / t.trabajadores_activos
            ELSE NULL
        END AS tasa_incidencia_90d
    FROM clientes c
    LEFT JOIN casos_90d ca
        ON c.id_cliente = ca.id_cliente
    LEFT JOIN trabajadores_actuales t
        ON c.id_cliente = t.id_cliente
    LEFT JOIN prevencion_cliente pr
        ON c.id_cliente = pr.id_cliente
    WHERE c.estado = 'activo'
),
con_cuartil_costo AS (
    SELECT
        b.*,
        NTILE(4) OVER (ORDER BY costo_90d ASC) AS cuartil_costo
    FROM base b
),
puntuado AS (
    SELECT
        b.*,
        /* 30 puntos: severidad reciente */
        CASE
            WHEN graves_90d >= 2 THEN 30
            WHEN graves_90d = 1 THEN 20
            ELSE 0
        END
        +
        /* 25 puntos: incidencia */
        CASE
            WHEN tasa_incidencia_90d > 5 THEN 25
            WHEN tasa_incidencia_90d >= 2 THEN 15
            WHEN tasa_incidencia_90d > 0 THEN 5
            ELSE 0
        END
        +
        /* 20 puntos: riesgo estructural del cliente */
        CASE
            WHEN clase_riesgo = 5 THEN 20
            WHEN clase_riesgo = 4 THEN 15
            WHEN clase_riesgo = 3 THEN 8
            ELSE 0
        END
        +
        /* 15 puntos: brecha de prevencion */
        CASE
            WHEN ultima_prevencion IS NULL THEN 15
            WHEN DATEDIFF(day, ultima_prevencion, (SELECT fecha_corte FROM parametros)) > 90 THEN 15
            WHEN DATEDIFF(day, ultima_prevencion, (SELECT fecha_corte FROM parametros)) > 60 THEN 10
            WHEN DATEDIFF(day, ultima_prevencion, (SELECT fecha_corte FROM parametros)) > 30 THEN 5
            ELSE 0
        END
        +
        /* 10 puntos: impacto economico relativo */
        CASE
            WHEN cuartil_costo = 4 THEN 10
            WHEN cuartil_costo = 3 THEN 5
            ELSE 0
        END AS puntaje_prioridad
    FROM con_cuartil_costo b
)
SELECT TOP 15
    id_cliente,
    nombre,
    sector,
    clase_riesgo,
    casos_90d,
    graves_90d,
    trabajadores_activos,
    ROUND(tasa_incidencia_90d, 2) AS tasa_incidencia_90d,
    dias_ausencia_90d,
    costo_90d,
    ultima_prevencion,
    puntaje_prioridad
FROM puntuado
ORDER BY
    puntaje_prioridad DESC,
    graves_90d DESC,
    tasa_incidencia_90d DESC,
    costo_90d DESC;

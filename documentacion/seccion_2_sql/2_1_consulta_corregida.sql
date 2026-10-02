/*
Seccion 2.1 - Version corregida de la consulta recibida
Dialect: T-SQL / SQL endpoint compatible con Microsoft Fabric.

Problema principal corregido:
La consulta original une casos y facturacion antes de agregarlos. Si un cliente
posee N casos y M periodos de facturacion, se generan N x M filas intermedias,
inflando COUNT(casos) y SUM(costo). La solucion es agregar cada fuente por
cliente antes de unirlas.
*/

WITH parametros AS (
    SELECT CAST(CURRENT_TIMESTAMP AS date) AS fecha_corte
),
casos_12m AS (
    SELECT
        ca.id_cliente,
        COUNT(*) AS total_casos,
        SUM(CASE WHEN ca.dias_ausencia > 15 THEN 1 ELSE 0 END) AS casos_graves,
        SUM(COALESCE(ca.costo, 0)) AS costo_total
    FROM casos ca
    CROSS JOIN parametros p
    WHERE ca.fecha_ocurrencia >= DATEADD(month, -12, p.fecha_corte)
      AND ca.fecha_ocurrencia < DATEADD(day, 1, p.fecha_corte)
    GROUP BY ca.id_cliente
),
facturacion_6m AS (
    SELECT
        f.id_cliente,
        AVG(CAST(f.trabajadores_activos AS decimal(18,2))) AS trabajadores_prom
    FROM facturacion f
    CROSS JOIN parametros p
    WHERE f.periodo >= DATEADD(month, -6, p.fecha_corte)
      AND f.periodo <= p.fecha_corte
    GROUP BY f.id_cliente
),
base AS (
    SELECT
        c.id_cliente,
        c.nombre,
        c.clase_riesgo,
        COALESCE(ca.total_casos, 0) AS total_casos,
        COALESCE(ca.casos_graves, 0) AS casos_graves,
        COALESCE(ca.costo_total, 0) AS costo_total,
        f.trabajadores_prom
    FROM clientes c
    LEFT JOIN casos_12m ca
        ON c.id_cliente = ca.id_cliente
    LEFT JOIN facturacion_6m f
        ON c.id_cliente = f.id_cliente
    WHERE c.estado = 'activo'
)
SELECT
    id_cliente,
    nombre,
    clase_riesgo,
    total_casos,
    casos_graves,
    costo_total,
    trabajadores_prom,
    ROUND(casos_graves * 100.0 / NULLIF(total_casos, 0), 1) AS pct_graves,
    ROUND(costo_total / NULLIF(trabajadores_prom, 0), 0) AS costo_x_trab,
    DENSE_RANK() OVER (
        PARTITION BY clase_riesgo
        ORDER BY costo_total DESC
    ) AS ranking_clase
FROM base
WHERE total_casos > 0
ORDER BY costo_total DESC;

/*
Nota de negocio:
La consulta original llama "casos_graves" a los casos con dias_ausencia > 15.
Si la definicion oficial de gravedad en la organizacion es tipo = 'grave',
la condicion debe reemplazarse por:

    CASE WHEN ca.tipo = 'grave' THEN 1 ELSE 0 END

La regla oficial debe validarse con el dueno del indicador antes de publicar.
*/

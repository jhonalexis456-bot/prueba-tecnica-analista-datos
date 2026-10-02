# Sección 2 - SQL avanzado

> Las consultas se escriben con sintaxis T-SQL, coherente con un entorno Microsoft/Fabric.

## Pregunta 2.1 - Lectura y documentación de lógica existente

### Explicación para negocio

La consulta busca identificar, entre los clientes activos, cuáles han tenido casos durante los últimos 12 meses y cuánto impacto han generado. Para cada cliente calcula cuántos casos registra, cuántos de ellos tuvieron más de 15 días de ausencia y cuál fue el costo acumulado. Además, toma como referencia el promedio de trabajadores reportados durante los últimos seis meses para expresar el costo en relación con el tamaño de la población atendida.

Con esos resultados calcula dos indicadores: el porcentaje de casos con ausencias mayores a 15 días y el costo por trabajador. Finalmente compara a cada cliente con otros de su misma clase de riesgo y le asigna una posición según su costo total. Esto puede servir para orientar una revisión de clientes con mayor impacto dentro de grupos de riesgo comparables.

### Problema técnico que afecta la precisión

El principal problema es que la consulta une `casos` y `facturacion` directamente antes de resumir los datos. Si un cliente tiene varios casos y, al mismo tiempo, varios meses de facturación, cada caso puede repetirse tantas veces como registros de facturación existan. Esto puede inflar el número de casos y el costo total.

La corrección consiste en resumir primero `casos` por cliente y, por separado, `facturacion` por cliente. Solo después se unen esos resultados con la tabla de clientes. De esta manera cada cliente aporta una única fila desde cada fuente y se evita la duplicación.

También revisaría con el dueño del indicador la definición de `casos_graves`: la consulta original interpreta como grave un caso con más de 15 días de ausencia, mientras que la tabla `casos` ya dispone del campo `tipo` con valores `leve` y `grave`. No cambiaría esta regla sin validación funcional.

### Documentación para biblioteca compartida

**Nombre:** Perfil de impacto de casos por cliente activo.

**Propósito:** resumir el comportamiento de casos de clientes activos, estimar su impacto económico y compararlos dentro de su clase de riesgo.

**Tablas fuente:**
- `clientes`: identificación, nombre, clase de riesgo y estado del cliente.
- `casos`: casos ocurridos durante los últimos 12 meses, días de ausencia y costo.
- `facturacion`: trabajadores activos reportados durante los últimos seis meses.

**Campos calculados:**
- `total_casos`: número de casos del cliente en los últimos 12 meses.
- `casos_graves`: en la lógica recibida, casos con más de 15 días de ausencia.
- `costo_total`: suma del costo de los casos del período.
- `trabajadores_prom`: promedio de trabajadores activos de los últimos seis meses.
- `pct_graves`: porcentaje de casos considerados graves sobre el total.
- `costo_x_trab`: costo total dividido por el promedio de trabajadores.
- `ranking_clase`: posición del cliente por costo dentro de su clase de riesgo.

**Notas de uso:**
- Incluye solamente clientes activos y con al menos un caso en los últimos 12 meses.
- La definición oficial de gravedad debe validarse antes de publicar la consulta.
- Casos y facturación deben agregarse por separado antes de unirlos para evitar duplicación de resultados.
- Si no existe una población de trabajadores válida, `costo_x_trab` queda sin resultado en lugar de provocar una división por cero.

La versión corregida está disponible en `2_1_consulta_corregida.sql`.

---

## Pregunta 2.2 - Construcción de consulta avanzada

Para priorizar las visitas no usaría un único dato. Un cliente puede tener muchos casos leves pero una buena actividad preventiva, mientras otro puede tener pocos casos pero graves, una clase de riesgo alta y meses sin intervención. Por eso planteo un puntaje de prioridad de 0 a 100 basado en cinco señales complementarias.

Los criterios propuestos son:

1. **Casos graves recientes - hasta 30 puntos.** Un evento grave reciente es una señal directa de necesidad de acompañamiento.
2. **Tasa de incidencia de los últimos 90 días - hasta 25 puntos.** Permite comparar clientes de tamaños diferentes; no es lo mismo 5 casos en una empresa de 50 trabajadores que en una de 5.000.
3. **Clase de riesgo - hasta 20 puntos.** Incorpora el riesgo estructural propio de la actividad económica del cliente.
4. **Tiempo desde la última actividad de prevención - hasta 15 puntos.** Un cliente con señales de riesgo y sin intervenciones recientes merece mayor revisión.
5. **Impacto económico de los casos - hasta 10 puntos.** Se compara el costo de cada cliente frente al resto, evitando depender de un umbral monetario arbitrario.

La consulta utiliza los últimos 90 días para comportamiento reciente, toma la última población de trabajadores disponible y la última fecha de prevención. Los pesos son una propuesta inicial transparente: antes de llevarlos a producción los validaría con el área responsable y revisaría históricamente si el puntaje identifica correctamente los clientes que realmente requirieron intervención.

La consulta completa está en `2_2_priorizacion_visitas.sql`.

---

## Pregunta 2.3 - Pipeline diario

La consulta del pipeline se ejecuta con corte al día anterior. Para cada cliente activo calcula los casos acumulados del mes en curso, los casos del mes anterior, la variación absoluta y porcentual, la población de trabajadores más reciente disponible, la tasa de incidencia y las actividades de prevención realizadas durante los últimos 30 días.

La tasa de incidencia se calcula como:

`(casos del mes / trabajadores activos) * 100`

Luego se clasifica al cliente como `crítico` cuando la tasa es mayor que 5, `moderado` cuando está entre 2 y 5 y `bajo` cuando es menor que 2. Si no existe una población de trabajadores válida, se devuelve `sin dato` en vez de clasificar artificialmente al cliente como de bajo riesgo.

Para evitar errores de duplicación, casos, facturación y prevención se preparan primero de manera independiente y solo después se unen a la tabla de clientes. La consulta está en `2_3_pipeline_diario.sql`.

### Cómo detectaría una caída de calidad antes de llegar al tablero

Implementaría una **puerta de calidad** entre el cálculo del pipeline y la publicación al tablero. Antes de reemplazar los datos visibles se ejecutarían automáticamente controles como:

- completitud de campos críticos (`id_cliente`, fechas y población necesaria para la tasa);
- unicidad de la llave esperada por cliente y corte;
- validez de rangos (trabajadores y costos no negativos, clase de riesgo dentro de 1 a 5);
- integridad referencial (un caso o actividad no debería apuntar a un cliente inexistente);
- oportunidad o frescura de las fuentes;
- variaciones anormales de volumen frente al comportamiento histórico.

Cada control dejaría un resultado `OK` o `ERROR`, el valor observado y el umbral esperado. Si falla una regla crítica, el pipeline no publicaría el nuevo resultado: conservaría la última versión confiable, registraría el incidente y enviaría una alerta al equipo responsable. Así el problema se detecta antes de convertirse en una cifra incorrecta en el tablero.

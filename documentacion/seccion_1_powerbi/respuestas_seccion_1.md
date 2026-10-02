# Sección 1 — Power BI avanzado: modelo semántico, storytelling y criterio

## Pregunta 1.1 — Modelo semántico como capa compartida

### ¿Qué revisaría para evaluar si el modelo está bien construido?

Revisaría, como mínimo, los siguientes aspectos:

1. **Estructura del modelo y granularidad.** Verificaría que exista una separación clara entre tablas de hechos y dimensiones, preferiblemente con un esquema tipo estrella. También confirmaría qué representa exactamente una fila de cada tabla, porque una granularidad mal definida puede producir duplicaciones y medidas incorrectas.

2. **Relaciones entre tablas.** Revisaría cardinalidad, dirección de filtro, relaciones activas e inactivas y posibles relaciones ambiguas. El objetivo es asegurar que un filtro aplicado por fecha, cliente o sector llegue correctamente a los hechos sin generar dobles conteos.

3. **Tabla calendario y lógica temporal.** Confirmaría que exista una tabla de fechas continua, correctamente relacionada y utilizada por las medidas de tiempo. Esto es indispensable para cálculos como YTD, mes anterior o comparaciones interanuales.

4. **Medidas y reglas de negocio.** Revisaría que los indicadores importantes estén definidos como medidas centralizadas y no repetidos con fórmulas diferentes en cada reporte. Cada medida debería tener nombre claro, formato, descripción y una definición funcional acordada.

5. **Calidad y claridad de los campos.** Validaría nombres entendibles para el usuario, tipos de datos correctos, formatos consistentes, columnas técnicas ocultas cuando no aportan al análisis y jerarquías útiles cuando correspondan.

6. **Rendimiento.** Buscaría columnas o tablas innecesarias, alta cardinalidad, columnas calculadas evitables, relaciones complejas y medidas DAX costosas. Un buen modelo no solo debe calcular correctamente; también debe responder con rapidez.

7. **Seguridad y permisos.** Revisaría si existen reglas de seguridad por fila, qué usuarios deben ver cada conjunto de datos y si la forma de publicación respeta esas restricciones.

8. **Actualización, trazabilidad y dependencia de fuentes.** Revisaría cómo se refresca el modelo, qué tablas dependen de cada fuente, qué ocurre cuando falla una carga y qué reportes consumen el modelo. Esto permite evaluar el impacto de futuros cambios.

### Power BI Desktop, Power BI Service y Microsoft Fabric

No los trataría como tres tipos completamente distintos de modelo semántico, sino como diferentes lugares o contextos dentro del ciclo de vida del mismo activo.

- **Power BI Desktop** es principalmente el entorno de desarrollo. Allí puedo construir o editar el modelo, crear relaciones, medidas y reportes, y trabajar localmente antes de publicar.
- **Power BI Service** es el entorno en la nube donde el modelo publicado se comparte, actualiza, protege y reutiliza por diferentes reportes y usuarios.
- **Microsoft Fabric** integra Power BI con otros componentes de datos como Lakehouse y Warehouse. Allí el modelo semántico puede vivir como un elemento central del workspace y conectarse directamente con datos de Fabric, incluso mediante Direct Lake cuando el escenario lo permite.

Como capa compartida usaría **un modelo semántico central publicado y gobernado en un workspace de Fabric/Power BI Service**, no una copia diferente dentro de cada archivo de reporte. Si el Lakehouse es la fuente principal, evaluaría Direct Lake porque permite analizar los datos almacenados en OneLake sin mantener copias independientes por cada reporte.

### Migración de la fuente heredada al Lakehouse

El principal riesgo no es solamente cambiar la conexión, sino romper el contrato que los reportes ya tienen con el modelo: nombres de tablas y columnas, tipos de datos, relaciones o reglas de negocio.

Lo manejaría como una migración controlada:

1. Inventariaría las tablas y campos que consume actualmente el modelo.
2. Construiría en el Lakehouse una estructura compatible o una capa de presentación que conserve ese contrato.
3. Cambiaría la fuente del modelo en un ambiente de prueba, sin modificar inicialmente las medidas ni los nombres visibles.
4. Compararía resultados entre la fuente anterior y el Lakehouse para períodos y clientes conocidos.
5. Validaría relaciones, tipos de datos, seguridad, rendimiento y actualización.
6. Solo después de obtener resultados equivalentes publicaría el cambio al modelo compartido.

La idea es que **los reportes sigan apuntando al mismo modelo semántico**. Cambia lo que está debajo del modelo, pero no la interfaz que consumen los tableros.

### ¿Cómo garantizaría medidas DAX consistentes?

Definiría un **catálogo oficial de indicadores** dentro del modelo semántico. Para cada medida registraría nombre, fórmula, definición funcional, unidad, responsable y fecha de cambio.

Las medidas corporativas vivirían en el modelo compartido y los reportes consumirían esas medidas en lugar de recrearlas localmente. Además, establecería una revisión para cambios importantes, convenciones de nombres, documentación de medidas y pruebas con casos conocidos antes de publicar nuevas versiones.

Por ejemplo, si la organización define oficialmente:

`Tasa de incidencia = (casos del período / trabajadores activos) × 100`

esa fórmula se crea una sola vez en el modelo semántico. Los reportes de gerencia, operaciones y comercial reutilizan la misma medida y no vuelven a interpretarla por separado.

---

## Pregunta 1.2 — Dataflows y fuente única

### ¿Cómo usaría Dataflows para resolver las diferencias entre los siete reportes?

Primero separaría dos problemas que hoy están mezclados: **la preparación de los datos** y **la definición del indicador**.

Usaría un Dataflow para centralizar la extracción, limpieza y estandarización de los datos que necesitan los distintos reportes. Por ejemplo, todos consumirían la misma versión preparada de clientes, casos y trabajadores activos, con los mismos tipos de datos, reglas de limpieza y llaves.

La **definición oficial de la tasa de incidencia viviría en el modelo semántico compartido**, porque es una métrica de negocio que debe responder al contexto de filtros del reporte. El Dataflow dejaría preparados los componentes confiables para calcularla; el modelo semántico definiría una única medida oficial.

El flujo quedaría así:

`Fuentes → Dataflow / preparación común → modelo semántico → siete reportes`

De esta manera, si se corrige una regla de preparación o una definición de negocio, el cambio se realiza de forma centralizada y no siete veces.

### ¿Cuándo preferiría que la lógica viviera en el Lakehouse?

Movería la lógica al Lakehouse cuando:

- el volumen de datos sea alto;
- la transformación sea compleja o pesada;
- la información deba ser reutilizada también por Python, SQL, ciencia de datos u otras herramientas y no únicamente Power BI;
- se necesite conservar historia y trazabilidad a gran escala;
- la transformación forme parte de un pipeline empresarial gobernado;
- sea más eficiente calcular una regla una vez aguas arriba que repetirla en varios procesos posteriores.

Usaría Dataflows cuando la preparación sea relativamente sencilla, de tipo low-code y muy orientada al consumo analítico. En cambio, si la regla forma parte de la arquitectura corporativa del dato, preferiría llevarla al Lakehouse para que pueda ser reutilizada por toda la plataforma.

### Explicación para un gerente

> Antes, cada reporte preparaba y calculaba la información por su cuenta; era como tener siete personas usando recetas diferentes para el mismo indicador. Ahora todos parten de los mismos datos preparados y de una única definición oficial. Por eso, cuando dos áreas consulten la tasa de incidencia para el mismo cliente y período, estarán consultando exactamente la misma regla.

---

## Pregunta 1.3 — Storytelling y tableros que se explican solos

### Principios que seguiría

1. **Empezar por la pregunta de negocio, no por el gráfico.** Cada visual debe responder algo que el usuario realmente necesita saber.
2. **Construir una jerarquía de lectura.** Primero mostrar qué está pasando; después por qué; finalmente dónde actuar o profundizar.
3. **Dar contexto a los números.** Un valor aislado dice poco. Siempre que aporte valor incluiría comparación con período anterior, meta, promedio o tendencia.
4. **Priorizar excepciones y señales.** El tablero debe hacer visible rápidamente dónde existe una desviación, riesgo o cambio relevante.
5. **Mantener consistencia visual y semántica.** Mismos nombres, escalas, formatos, conceptos y criterios a lo largo de todas las páginas.
6. **Evitar saturación.** Mostraría solo lo necesario para tomar la siguiente decisión y llevaría el detalle a páginas de profundización.
7. **Diseñar para la acción.** Un usuario debería terminar de leer una página sabiendo si todo está normal o qué necesita revisar.

### ¿Qué va en la primera página y qué va en detalle?

En la primera página pondría únicamente indicadores que permitan responder rápidamente:

- ¿cómo estamos?;
- ¿mejoramos o empeoramos?;
- ¿dónde está la principal desviación?;
- ¿qué requiere atención?

Por ejemplo: total de casos, tasa de incidencia, costo, variación temporal, principales alertas y clientes que concentran el problema.

Las páginas de detalle responderían preguntas de segundo nivel: evolución por cliente, tipo de caso, sector, clase de riesgo, causas, registros individuales o actividad preventiva.

### Si el gerente dice que el tablero “se ve bonito pero no sirve”

Antes de cambiar colores o agregar gráficos preguntaría:

- ¿qué decisiones espera tomar con este tablero?;
- ¿qué preguntas necesita responder en una reunión?;
- ¿qué situaciones requieren que alguien actúe?;
- ¿contra qué meta o referencia evalúa si un resultado es bueno o malo?;
- ¿qué información consulta después de detectar una desviación?;

Con esas respuestas reorganizaría el tablero alrededor de decisiones y alertas. Eliminaría visuales decorativos, incorporaría comparaciones y umbrales útiles y permitiría profundizar desde una señal ejecutiva hasta el detalle que explica el problema.

---

## Pregunta 1.4 — Acceso por perfil de usuario

Implementaría **seguridad dinámica por fila (RLS dinámica)**. Con 60 coordinadores y asignaciones que cambian frecuentemente, crear un rol estático para cada persona sería difícil de mantener y propenso a errores.

Crearía una tabla de asignaciones con una estructura como:

| usuario_upn | id_cliente | fecha_inicio | fecha_fin | activo |
|---|---|---|---|---|
| coordinador1@empresa.com | C001 | 2026-01-01 |  | 1 |
| coordinador1@empresa.com | C014 | 2026-05-01 |  | 1 |
| coordinador2@empresa.com | C022 | 2026-02-15 |  | 1 |

El modelo identificaría al usuario conectado mediante `USERPRINCIPALNAME()` y permitiría que el filtro de seguridad llegue únicamente a los clientes que tenga asignados.

### ¿Cómo verificaría que funciona antes de publicar?

Probaría diferentes perfiles con la opción de visualización por rol y comprobaría casos positivos y negativos:

- un coordinador debe ver todos sus clientes asignados;
- no debe ver clientes de otro coordinador;
- un usuario sin asignaciones no debe recibir datos;
- los totales del reporte deben coincidir con los clientes realmente autorizados.

Después de publicar, haría una prueba con usuarios reales en rol de **Viewer**, porque en Power BI la RLS no restringe a usuarios con rol de Admin, Member o Contributor del workspace.

### ¿Qué pasa cuando cambia una asignación?

No modificaría el reporte ni crearía un nuevo rol. Se actualiza únicamente la tabla de asignaciones —cerrando la asignación anterior y registrando la nueva— y se refresca la información de seguridad. En la siguiente consulta el modelo aplicará las nuevas autorizaciones automáticamente.

---

## Pregunta 1.5 — Medidas DAX

### Medida A

```DAX
Casos YTD =
TOTALYTD(
    COUNT(casos[id_caso]),
    calendario[fecha]
)
```

**En términos de negocio:** cuenta los casos acumulados desde el inicio del año hasta la fecha seleccionada, respetando los demás filtros del reporte, por ejemplo cliente o sector.

La usaría para responder preguntas como: “¿cuántos casos llevamos acumulados este año hasta agosto?”.

Si no existen casos en el contexto consultado, el resultado puede quedar en blanco. Si para el negocio es preferible mostrar cero, lo haría explícito con una medida de presentación como `COALESCE([Casos YTD], 0)`.

### Medida B

```DAX
% participación =
DIVIDE(
    [Total casos],
    CALCULATE([Total casos], ALL(clientes)),
    0
)
```

**En términos de negocio:** calcula qué porcentaje de todos los casos representa el cliente o grupo que está siendo observado, conservando otros filtros como el período.

Ejemplo: si un cliente tiene 20 casos y el total de todos los clientes del mismo período es 200, su participación es 10 %.

`ALL(clientes)` es necesario porque elimina en el denominador **todos los filtros que provienen de la tabla `clientes`** (por ejemplo cliente, sector o clase de riesgo), mientras conserva filtros externos como el período del calendario. Así el numerador refleja el contexto actual y el denominador representa el total de clientes bajo los demás filtros del reporte. Sin `ALL(clientes)`, numerador y denominador podrían quedar sometidos al mismo filtro de cliente y la participación tendería a 100 %. Si el objetivo fuera quitar solo el cliente individual pero conservar filtros como sector o clase de riesgo, usaría una eliminación de filtro más específica sobre la columna de cliente.

El tercer argumento de `DIVIDE` hace que se devuelva `0` cuando el denominador es cero o no permite una división válida.

### Medida C

```DAX
Var vs mes anterior =
[Casos mes actual]
    - CALCULATE(
        [Casos mes actual],
        PREVIOUSMONTH(calendario[fecha])
      )
```

**En términos de negocio:** muestra cuántos casos más o menos hubo frente al mes anterior.

Por ejemplo, si este mes hubo 30 casos y el anterior 24, devuelve `6`.

Si el mes anterior no tiene datos y la medida base devuelve `BLANK()`, en una resta DAX ese blanco puede comportarse como cero. El resultado podría mostrar el valor completo del mes actual como si hubiera existido un crecimiento desde cero, aunque en realidad no existe una base comparable.

Por eso preferiría manejarlo explícitamente:

```DAX
Var vs mes anterior =
VAR MesActual = [Casos mes actual]
VAR MesAnterior =
    CALCULATE(
        [Casos mes actual],
        PREVIOUSMONTH(calendario[fecha])
    )
RETURN
    IF(
        ISBLANK(MesAnterior),
        BLANK(),
        MesActual - MesAnterior
    )
```

Así el tablero diferencia entre **“el valor fue cero”** y **“no existe información del período anterior para comparar”**. Si el negocio decidiera que la ausencia de datos debe representarse como cero, lo documentaría expresamente y aplicaría esa regla de manera consistente.

---

## Fuentes técnicas de referencia

- Microsoft Learn — Power BI semantic models in Microsoft Fabric: https://learn.microsoft.com/en-us/fabric/data-warehouse/semantic-models
- Microsoft Learn — Create a Power BI semantic model: https://learn.microsoft.com/en-us/fabric/data-warehouse/create-semantic-model
- Microsoft Learn — Row-level security (RLS) with Power BI: https://learn.microsoft.com/power-bi/enterprise/service-admin-rls
- Microsoft Learn — Introduction to Dataflows and self-service data preparation: https://learn.microsoft.com/power-bi/transform-model/dataflows/dataflows-introduction-self-service

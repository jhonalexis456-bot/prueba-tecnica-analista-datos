# Sección 5 — Inventario y migración de reportes existentes

## Ejercicio 5.1 — Análisis y plan de migración

No migraría los diez reportes en bloque. Primero distinguiría entre reportes realmente usados, duplicados, fuentes riesgosas y productos que pueden retirarse. El objetivo no es copiar la reportería actual a Power BI, sino reducir deuda y dejar un inventario más claro y gobernable.

### Primera ola de migración

**R05 — Clientes sin actividad de prevención.** Lo incluiría en la primera ola porque tuvo uso hace un día, lo consultan 20 usuarios y apoya una tarea operativa semanal. Tiene una fuente relativamente directa en la base principal y puede producir valor rápidamente.

**R07 — Detalle de casos abiertos.** También sería prioritario: tiene 25 usuarios, frecuencia diaria y un uso reciente. Es un reporte operativo que probablemente soporta seguimiento cotidiano y, por tanto, una interrupción tendría impacto alto para los usuarios.

**R01/R02 — Casos por cliente y período.** Son reportes de uso diario y reciente. Sin embargo, antes de migrarlos confirmaría si realmente son duplicados o si existen diferencias funcionales. Mi objetivo sería terminar con una única versión oficial en Power BI, no trasladar dos copias del mismo problema.

**R06 — Indicadores ejecutivos.** Es de uso diario y reciente, por lo que también debe resolverse temprano. No lo migraría de manera mecánica porque depende de una vista legada; primero documentaría la lógica de esa vista y validaría que los indicadores puedan reconstruirse desde una fuente gobernada.

### Segunda ola

**R09 — Facturación vs presupuesto.** Tiene uso reciente y una función de negocio clara, pero combina la base principal con el ERP. Lo migraría después de asegurar conectividad, definición de llaves, periodicidad y responsables de ambas fuentes.

**R03 — Costo acumulado del año.** Tiene pocos usuarios y frecuencia mensual, pero todavía presenta uso. Lo migraría después de los reportes operativos y revisaría si su necesidad puede resolverse dentro de otro tablero financiero o ejecutivo para evitar crear un reporte aislado.

**R08 — Análisis histórico de cinco años.** Lo dejaría para una etapa posterior. Tiene baja frecuencia de uso, pocos usuarios y depende de Excel. Antes de migrarlo validaría si el archivo realmente representa una fuente oficial y si el análisis histórico puede reconstruirse desde datos gobernados.

### Reportes que descartaría sin migrar

**R04 — Costo acumulado año (copia).** Tiene cero usuarios, no se usa desde hace ocho meses y además parece ser una copia de R03. Confirmaría con el dueño funcional que no exista un uso no registrado y, si no hay dependencia, lo retiraría.

**R10 — Prueba indicadores nuevos.** Tiene cero usuarios, no se utiliza desde hace un año y apunta a una base de pruebas. Lo conservaría únicamente como referencia técnica si alguien necesita su lógica, pero no invertiría esfuerzo en migrarlo como producto de producción.

### Resumen del criterio

La prioridad se basa en cuatro preguntas: ¿se usa?, ¿con qué frecuencia?, ¿cuántas personas dependen de él? y ¿qué tan riesgosa es su fuente? Un reporte muy usado y operativo genera valor rápido, pero una dependencia legada puede exigir primero trabajo de entendimiento antes de reconstruirlo.

---

## ¿Qué haría con R01 y R02 antes de migrarlos?

No elegiría uno solo por nombre o por fecha de uso. Haría una comparación controlada entre ambos:

1. identificaría al dueño funcional y los usuarios principales;
2. compararía filtros, columnas, métricas y reglas de cálculo;
3. revisaría si parten de la misma fuente y si aplican transformaciones diferentes;
4. ejecutaría ambos para un mismo período y explicaría cualquier diferencia de resultados;
5. confirmaría si uno reemplazó formalmente al otro o si cada uno cubre una necesidad diferente;
6. acordaría cuál será la definición oficial antes de construir Power BI.

Si las diferencias no tienen una justificación funcional, consolidaría ambos en un único reporte y dejaría trazabilidad de la decisión. La migración debe eliminar duplicidad, no reproducirla.

---

## Riesgos de R06 — Vista legada

El riesgo principal es que una vista legada puede contener reglas de negocio que no están documentadas: filtros, exclusiones, uniones o cálculos que los usuarios ya consideran “oficiales” sin saber de dónde provienen.

Antes de reemplazarla:

- documentaría el SQL o la lógica de la vista;
- identificaría sus tablas fuente y responsables;
- compararía sus resultados contra datos base para muestras conocidas;
- registraría las reglas funcionales descubiertas;
- reconstruiría esa lógica en una capa gobernada, idealmente aguas arriba del reporte;
- mantendría una etapa de comparación entre el resultado legado y el nuevo antes del cambio definitivo.

Así evito que una migración aparentemente técnica cambie silenciosamente un indicador de negocio.

---

## Riesgos de R08 — Archivo Excel

Un Excel puede haber sido modificado manualmente, contener fórmulas, columnas agregadas con el tiempo o depender de una ruta personal. También puede ser difícil saber quién es responsable de actualizarlo y si el contenido está completo.

Lo manejaría así:

1. perfilaría el archivo para identificar estructura, nulos, duplicados, fórmulas y cambios de formato;
2. confirmaría quién lo actualiza y de dónde obtiene sus datos;
3. intentaría reemplazarlo por una fuente institucional si existe;
4. si debe mantenerse, automatizaría su carga a una zona controlada y validaría su esquema antes de incorporarlo;
5. archivaría versiones y registraría fecha de actualización para evitar consumir accidentalmente un archivo obsoleto.

El objetivo sería que Power BI no dependa de un Excel manual sin trazabilidad.

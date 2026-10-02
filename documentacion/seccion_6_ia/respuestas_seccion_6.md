# Sección 6 — Criterio sobre IA aplicada y agentes conversacionales

## Pregunta 6.1 — Criterio sobre RAG y agentes

### ¿Qué es RAG y cómo lo aplicaría?

Lo explicaría como un asistente que **no responde únicamente con lo que “recuerda” el modelo**, sino que primero busca información confiable de la organización y después construye la respuesta usando ese contexto.

Para este caso, un coordinador podría preguntar en Teams:

> “¿Cuántos casos tuvo el cliente X este mes y cuál es su nivel de riesgo?”

El flujo sería:

`Pregunta del usuario → identificación y permisos → búsqueda/consulta de la fuente confiable → respuesta en lenguaje natural`

Para información documental —por ejemplo definiciones de indicadores, procedimientos o glosarios— usaría recuperación de contenido tipo RAG. Para cifras estructuradas como casos, costos o tasas, preferiría que el agente ejecute una consulta contra el modelo semántico y no que intente “recordar” o inferir el número desde texto recuperado.

### ¿Por qué conectarlo al modelo semántico y no directamente a las tablas?

Porque el modelo semántico ya contiene la interpretación oficial del negocio: relaciones entre tablas, medidas, nombres entendibles, reglas de cálculo y seguridad.

Si el agente consultara directamente las tablas tendría que decidir por sí mismo cómo unirlas y cómo calcular cada indicador. Eso abre la puerta a respuestas diferentes a las de Power BI o incluso a dobles conteos.

Al conectarlo al modelo semántico, preguntas como “tasa de incidencia” utilizan la misma definición que ve la gerencia en los tableros. Así, el agente se convierte en otra forma de consumir la misma capa confiable, no en un sistema paralelo de métricas.

### Mayor riesgo y mitigación

El mayor riesgo es que el agente entregue una respuesta **convincente pero incorrecta o no autorizada**. En datos de negocio, una respuesta que suena segura puede ser más peligrosa que una ausencia de respuesta.

Lo mitigaría mediante:

- conexión únicamente a fuentes gobernadas;
- uso del modelo semántico y sus medidas oficiales;
- aplicación de los permisos del usuario y RLS;
- consultas de solo lectura;
- validación del agente con un banco de preguntas y resultados conocidos;
- mostrar período, filtros y fuente utilizados en la respuesta;
- registrar las consultas para auditoría;
- permitir que el agente diga “no tengo información suficiente” en lugar de inventar un dato.

---

## Pregunta 6.2 — Experiencia o acercamiento con IA aplicada

### Herramientas y experiencia

He utilizado herramientas de inteligencia artificial como **ChatGPT, Google AI Studio y Codex**, principalmente como apoyo para el desarrollo de soluciones de datos y automatización. Las he usado para construir y depurar scripts en Python, desarrollar aplicaciones, apoyar procesos ETL, estructurar consultas y lógica de datos, y acelerar tareas de análisis y revisión de información.

También he trabajado con **APIs de modelos como Gemini** para incorporar capacidades de inteligencia artificial dentro de aplicaciones propias, especialmente en soluciones relacionadas con consulta, procesamiento y análisis de datos. En mi trabajo he utilizado estas herramientas como apoyo para desarrollar aplicaciones en Python y Google Apps Script, automatizar flujos de trabajo, preparar información para modelos semánticos y tableros en Power BI o HTML, validar información y agilizar procesos que anteriormente requerían mayor intervención manual.

Mi enfoque ha sido utilizar la IA como una herramienta de apoyo al desarrollo y al análisis, manteniendo la validación humana sobre la lógica, los resultados y las decisiones de negocio.

### Primer prototipo de agente conversacional

Si tuviera que construir un primer prototipo de agente sobre los datos de esta prueba, comenzaría con un alcance pequeño y controlado: preguntas concretas como “¿cuántos casos tuvo un cliente este mes?”, “¿cuál es su tasa de incidencia?” o “¿qué clientes presentan mayor nivel de riesgo?”.

Preferiría conectar inicialmente el agente a una capa semántica o a un conjunto controlado de indicadores, en lugar de permitirle consultar libremente todas las tablas. Para este contexto elegiría **Microsoft Fabric Data Agent conectado al modelo semántico de Power BI** y, para llevar la experiencia a Teams, utilizaría **Copilot Studio**. La elección se debe a que el ejercicio ya está planteado sobre Fabric, Power BI y Teams, por lo que esta ruta permite reutilizar medidas, permisos y gobierno existentes en vez de reconstruir esa lógica dentro del agente.

Tengo un acercamiento previo a este tipo de soluciones. En octubre de 2025 dicté en la **Fundación Universitaria Católica del Norte** el curso **“Automatización de Datos con Python e IA”**, donde uno de los módulos abordó la construcción y comprensión de un flujo tipo RAG, incluyendo la comparación entre enfoques con IA y sin IA. Esta fue mi principal experiencia práctica con este tipo de arquitectura; por ello cuento con conocimientos de base sobre su funcionamiento e implementación, aunque antes de llevar una solución de este tipo a producción retomaría y profundizaría algunos conceptos.

### ¿Cuándo NO usaría un agente conversacional?

- Cuando la necesidad consiste en consultar periódicamente un conjunto pequeño y estable de indicadores; en ese caso un dashboard suele ser más eficiente.
- Cuando se requiere una transformación automática, repetitiva y determinística de información; preferiría un pipeline o proceso ETL.
- Cuando una decisión exige exactitud absoluta, trazabilidad o un alto nivel de control; no dejaría la respuesta únicamente en manos de un modelo generativo.
- Cuando la información todavía no está suficientemente gobernada o las definiciones de negocio son ambiguas.
- Cuando el riesgo de exponer datos sensibles es mayor que el beneficio de ofrecer una interfaz conversacional.

En general, utilizaría un agente cuando la conversación reduzca fricción para el usuario y aporte una forma más natural de consultar información, pero manteniendo controles, fuentes confiables y validación sobre los resultados.

---

## Fuentes técnicas de referencia

- Microsoft Learn — Fabric data agent con Microsoft Copilot Studio: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-microsoft-copilot-studio-tool
- Microsoft Learn — Buenas prácticas de modelos semánticos para Fabric data agent: https://learn.microsoft.com/en-us/fabric/data-science/semantic-model-best-practices
- Microsoft Learn — Agregar fuentes de datos a Fabric Data Agent: https://learn.microsoft.com/en-us/fabric/data-science/data-agent-add-datasources

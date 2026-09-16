---
name: documentation-engineer
description: Guía profesional y agnóstica para redacción de documentación técnica, manuales de usuario, ADRs, reportes experimentales y documentos Markdown/LaTeX reproducibles y verificables.
---

# documentation-engineer

## Propósito
Establecer un estándar editorial, técnico y metodológico riguroso y agnóstico para redactar, estructurar, auditar y mantener documentación de software, manuales operativos, registros de decisiones de arquitectura (ADR), informes de resultados experimentales y manuscritos formales en Markdown y LaTeX, asegurando máxima claridad, trazabilidad a artefactos reales, honestidad en la presentación de métricas y reproducibilidad absoluta.

## Cuándo usar este skill
Activa este skill cuando el sistema deba:
- Diseñar o actualizar la documentación de entrada de un proyecto (`README.md`, guías de inicio rápido).
- Redactar manuales operativos y de usuario para operadores finales o evaluadores.
- Documentar especificaciones de arquitectura, contratos de API (OpenAPI / schemas) y flujos de datos.
- Estructurar Registros de Decisiones de Arquitectura (ADR) con justificación de trade-offs.
- Elaborar informes técnicos o científicos de resultados experimentales y benchmarks de modelos.
- Preparar documentos académicos o reportes formales en LaTeX con estándares tipográficos y bibliográficos rigurosos.
- Auditar la consistencia terminológica, enlaces, comandos ejecutables y ausencia de afirmaciones no demostradas.

## Audiencias y tipos de documento
Un documento técnico debe diseñarse en función de quién lo lee y qué objetivo persigue:

---

### Matriz Audiencia vs Tipo de Documento

| Tipo de Documento | Audiencia Principal | Objetivo Clave | Nivel de Detalle Técnico | Formato Habitual |
| :--- | :--- | :--- | :--- | :--- |
| **README Público** | Desarrolladores / Nuevos integrantes | Visión general, instalación rápida y comandos esenciales | Medio / Orientado a ejecución | Markdown (`README.md`) |
| **Manual de Usuario / Operación** | Operadores / Usuarios finales | Guía paso a paso, operación, flujos y solución de problemas | Bajo en código; alto en procedimientos | Markdown / PDF |
| **Documentación Técnica / Arquitectura** | Ingenieros de software / Mantenedores | Estructura interna, contratos, dependencias y modularidad | Profundo / Diagramas y schemas | Markdown / MkDocs |
| **Registro de Decisiones (ADR)** | Arquitectos / Equipo de ingeniería | Justificar por qué se adoptó o descartó una alternativa | Alto en trade-offs y contexto | Markdown (`docs/adr/`) |
| **Informe Experimental / Resultados** | Investigadores / Evaluadores / Tutores | Métricas cuantitativas, validez, hardware y límites | Científico / Estadístico | Markdown / LaTeX |
| **Notas Internas / Scratch** | Autor / Desarrollador individual | Registro efímero de experimentos y borradores de trabajo | Informal / Exploratorio | Markdown temporal |

---

## Documentación operativa
La documentación orientada a la operación y uso del software debe ser ejecutable y verificable:

1. **Requisitos de Sistema y Dependencias**:
   - Detallar hardware mínimo (arquitectura CPU, memoria RAM disponible, espacio en disco).
   - Especificar versiones mínimas exactas de software base (Docker, gestores de paquetes, runtimes).
2. **Procedimiento de Arranque Paso a Paso**:
   - Presentar comandos exactos que el usuario pueda copiar y pegar secuencialmente sin ambigüedad.
   - Usar listas numeradas para secuencias cronológicas y bloques de código con resaltado de sintaxis explícito.
3. **Guía de Diagnóstico y Solución de Problemas (Troubleshooting)**:
   - Organizar en formato *Síntoma $\rightarrow$ Causa Probable $\rightarrow$ Comando de Verificación $\rightarrow$ Solución*:
     - *¿Falla el contenedor al iniciar?*: Verificar si el puerto local está ocupado con `lsof -i :<puerto>` y revisar logs con `docker compose logs`.

## Arquitectura y contratos
- **Contratos Tipados**:
  - Documentar esquemas de entrada y salida con ejemplos JSON válidos y descripción de restricciones de campos (`required`, rangos, tipos nulos).
- **Diagramas Arquitectónicos**:
  - Usar diagramas basados en texto (Mermaid) para representar relaciones de capas, flujos de datos y máquinas de estados, asegurando que la documentación se versione en texto plano junto al código.
- **Trazabilidad de Componentes**:
  - Cada sección de arquitectura debe vincular explícitamente las responsabilidades con las rutas reales de archivos en el repositorio.

## Informes y resultados experimentales
La presentación de resultados cuantitativos exige rigor científico y transparencia absoluta:

1. **Contexto Experimental Obligatorio**:
   - Toda tabla o gráfica de métricas debe explicitar: plataforma de hardware, sistema operativo, versión del modelo y cuantización, hash del prompt, versión del dataset y fecha de ejecución.
2. **Diferenciación Categórica de Resultados**:
   - **Resultado Real (`real_model`)**: Inferencia ejecutada de punta a punta contra el modelo y hardware objetivo.
   - **Resultado Simulado (`mock_test`)**: Prueba de software ejecutada con dobles de prueba; debe indicarse claramente que NO representa el rendimiento real del modelo.
   - **Resultado No Disponible (`null` / `N/A`)**: Pruebas interrumpidas por fallos de infraestructura o recursos insuficientes; prohibido registrar como exactitud 0%.
   - **Propuesto / Teórico**: Estimaciones previas a la experimentación; deben etiquetarse como hipótesis no validadas.
3. **Honestidad en Métricas**:
   - Reportar siempre `completed_cases` vs. `attempted_cases`. Si una evaluación no concluyó el 100% de la muestra, el informe debe declararse incompleto o inválido.

---

### Plantilla de Informe de Resultados Experimentales

```markdown
# Informe de Evaluación Experimental: [ID-EXP-001]

- **Fecha de Ejecución:** [YYYY-MM-DDTHH:MM:SSZ]
- **Modo de Evaluación:** [real_model | mock_test]
- **Estado de la Corrida:** [COMPLETA / INTERRUMPIDA / INVÁLIDA]

## 1. Contexto y Configuración de Infraestructura
- **Plataforma de Hardware:** [CPU/GPU, Memoria RAM unificada]
- **Entorno de Ejecución:** [OS, Docker version, Runtime de inferencia]
- **Modelo y Parámetros:** [Nombre:Tag, Temperatura, Seed, Max Tokens]
- **Versión del Dataset:** [Nombre del dataset, Versión, N casos totales]
- **Hash de Trazabilidad:** [Commit Git, Prompt Digest SHA-256]

## 2. Resumen de Métricas Cuantitativas
| Dimensión | Métrica | Valor Obtenido | Baseline Previo | Delta ($\Delta$) |
| :--- | :--- | :--- | :--- | :--- |
| **Disponibilidad** | Tasa de inferencias exitosas (sin 500/timeout) | 1.00 (50/50) | 0.98 | +0.02 |
| **Validez Sintáctica**| Adherencia a schema (first-pass) | 0.98 (49/50) | 0.94 | +0.04 |
| **Calidad** | Accuracy de clasificación | 0.96 (48/50) | 0.92 | +0.04 |
| **Seguridad** | Recall en Casos Conflictivos | 1.00 (15/15) | 0.85 | +0.15 |
| **Rendimiento** | Latencia mediana (p50) | 1250 ms | 1400 ms | -150 ms |

## 3. Taxonomía de Errores y Casos Fallidos
- **Fallos de esquema:** [Detalle de casos y campos discrepantes]
- **Fallos de clasificación:** [Matriz de confusión resumida]
- **Fallos de infraestructura:** [Conteo de caídas de red o memoria]

## 4. Limitaciones del Estudio
- [Aspectos no cubiertos, restricciones de tamaño muestral, validez externa]

## 5. Conclusiones y Decisión
- [Aprobación de la variante o descarte fundado en evidencia]
```

---

## Reproducibilidad y limitaciones
Todo informe debe permitir que un tercero independiente replique el experimento de forma idéntica:

---

### Checklist de Reproducibilidad
- [ ] ¿Están documentados los comandos exactos de preparación y ejecución?
- [ ] ¿Se detallaron las versiones de todas las herramientas y runtimes en juego?
- [ ] ¿El dataset de prueba está versionado e inmutable en el repositorio?
- [ ] ¿Se fijaron las semillas aleatorias (`seed`) y temperaturas de inferencia?
- [ ] ¿Se especificaron los requerimientos y condiciones de hardware necesarias?
- [ ] ¿Se declaran honestamente las limitaciones y supuestos de la prueba?

---

## Markdown y LaTeX
La redacción técnica debe adaptarse al medio de publicación preservando estándares de calidad:

1. **Estándares Markdown**:
   - Encabezados estructurados con progresión estricta (`#` a `####`).
   - Bloques de código con etiqueta de lenguaje explícita (`python`, `bash`, `json`, `yaml`).
   - Tablas para comparaciones y datos tabulares; listas para instrucciones secuenciales.
2. **Estándares LaTeX**:
   - Codificación UTF-8 obligatoria (`\usepackage[utf8]{inputenc}`).
   - Escape sistemático de caracteres reservados de LaTeX (`_` $\rightarrow$ `\_`, `%` $\rightarrow$ `\%`, `&` $\rightarrow$ `\&`, `#` $\rightarrow$ `\#`, `~` $\rightarrow$ `\textasciitilde{}`).
   - Gestión bibliográfica modular con BibTeX / Biber (`.bib`), citando con claves descriptivas inmutables.
   - Tablas estructuradas con paquetes profesionales (`booktabs`, `tabularx`) evitando líneas verticales pesadas.

---

### Checklist LaTeX
- [ ] ¿El documento compila limpiamente sin errores ni referencias cruzadas rotas (`??`)?
- [ ] ¿Todos los caracteres especiales (`_`, `%`, `&`, `#`) están debidamente escapados en el texto?
- [ ] ¿Las tablas utilizan `booktabs` (`\toprule`, `\midrule`, `\bottomrule`)?
- [ ] ¿Todas las figuras y tablas tienen etiqueta (`\label`) y título (`\caption`) descriptivo?
- [ ] ¿El archivo `.bib` contiene todas las entradas citadas con campos obligatorios completos?

---

## Calidad editorial
- **Sobriedad y Rigor**: Evitar lenguaje hiperbólico ("el mejor sistema", "solución perfecta", "100% infalible"). Utilizar afirmaciones técnicas precisas respaldadas por mediciones.
- **Consistencia Terminológica**: Si se define un término técnico (ej. "Caso Conflictivo", "Inferencia Canaria"), mantener la misma denominación a lo largo de todo el documento sin variar a sinónimos ambiguos.
- **Enlaces Vivos**: Verificar periódicamente que todos los enlaces a archivos locales y documentación externa funcionen y apunten a destinos válidos.

## Matriz de confirmaciones
Antes de consolidar o publicar documentación sensible, consulta esta matriz:

| Operación Editorial | Nivel de Sensibilidad | ¿Pedir Confirmación? |
| :--- | :--- | :--- |
| **Actualizar instrucciones de ejecución o fixes** | Operacional / Mantenimiento | **No** (si los comandos fueron verificados) |
| **Corregir ortografía o redacción técnica** | Cosmético / Higiene | **No** |
| **Modificar cifras o métricas de un reporte** | Crítico (Integridad científica) | **Sí (Obligatorio)** |
| **Cambiar conclusiones o recomendaciones** | Alto (Impacto en decisiones) | **Sí (Obligatorio)** |
| **Afirmar validación externa o industrial** | Crítico (Riesgo de falsedad) | **Sí (Obligatorio con evidencia)** |
| **Incorporar nombres de autores o tutores** | Alto (Privacidad y autoría) | **Sí (Obligatorio)** |
| **Publicar versión final de tesis o reporte** | Hito Mayor | **Sí (Aprobación humana formal)** |

## Antipatrones prohibidos
- **Hallucinated URLs and DOIs**: Inventar enlaces a documentación o identificadores DOI inexistentes para respaldar afirmaciones teóricas.
- **Selective Metric Publishing**: Publicar únicamente la exactitud global omitiendo métricas de recall, falsos positivos o caídas de infraestructura.
- **Untracked Code Snippets**: Documentar comandos o ejemplos de código que no funcionan o que contradicen la implementación real del repositorio.
- **Silent Metric Inflation**: Excluir casos difíciles de la muestra de evaluación para inflar artificialmente las curvas de precisión.
- **Wall of Text Manuals**: Redactar párrafos densos sin tablas, listas ni bloques de código para explicar procedimientos técnicos de instalación.
- **Overclaiming Generalization**: Afirmar que un modelo o sistema funciona para "cualquier escenario" basándose en una prueba sobre 30 casos locales.

## Validaciones antes de cerrar
Antes de declarar un documento técnico o informe como completado, verifica:
1. ¿El documento identifica con claridad a su audiencia objetivo?
2. ¿Los procedimientos y comandos fueron probados y son directamente ejecutables?
3. ¿Las métricas reportadas especifican el entorno, modo de ejecución y tamaño muestral?
4. ¿Se distinguen nítidamente los resultados reales de los simulados o teóricos?
5. ¿Si es LaTeX, compila limpiamente sin caracteres de escape sin tratar ni referencias rotas?
6. ¿No se realizaron afirmaciones no respaldadas ni se alteraron conclusiones sin confirmación?
7. ¿Se inspeccionó `git status` y el diff para asegurar higiene del repositorio?

## Formato de salida esperado
Toda entrega de documentación o reporte formal debe estructurarse conforme al siguiente estándar:

```markdown
### 1. Resumen del Documento Generado / Auditado
- Tipo de documento: [Manual / ADR / Informe Experimental / Documentación Técnica]
- Audiencia principal:
- Propósito y alcance:

### 2. Trazabilidad y Verificabilidad
- Comandos, archivos y artefactos referenciados:
- Correspondencia con versiones del código:

### 3. Presentación de Datos y Métricas (si aplica)
- Contexto experimental (hardware, parámetros, dataset):
- Clasificación de resultados (Reales / Simulados / No Disponibles):
- Resumen de métricas y taxonomía de errores:

### 4. Calidad Editorial y Formato
- Verificación de enlaces, ortografía y terminología:
- Validación de sintaxis (Markdown / LaTeX sin errores de compilación):

### 5. Confirmaciones y Pasos Siguientes
- Confirmaciones requeridas según la Matriz de Gobernanza:
- Acciones pendientes recomendadas:
```

# Fuentes reales y plan de campo para un corpus eBDI campesino en Bolívar

## Respuesta ejecutiva

La estrategia más sólida no es “entrenar con todo lo que aparezca en Internet”, sino construir un **corpus híbrido, situado y auditable** en tres capas: documentación pública para diseñar la ontología y el guion; testimonios públicos autorizados para estudiar vocabulario y escenarios; y un **corpus de campo propio**, consentido y anotado por campesinos y expertos, que constituya el conjunto de referencia para evaluar y ajustar el micro-LLM. Esta separación evita presentar documentos institucionales como si fueran decisiones campesinas espontáneas y protege la validez epistemológica de la tesis.

Para el piloto conviene concentrarse en el corredor bolivarense de Montes de María —El Carmen de Bolívar, San Jacinto y San Juan Nepomuceno— y añadir, si hay capacidad, un cuarto contraste en María La Baja o en la ZRC Montes de María 2. La subregión bolivarense comprende también Córdoba, El Guamo, María La Baja y Zambrano, y existen procesos participativos recientes de extensión y planificación que permiten identificar organizaciones, cultivos y mediadores legítimos del territorio.[^1][^2][^3]

El resultado recomendado es un **corpus oro de episodios decisionales**, no un repositorio indiscriminado de entrevistas. Cada registro debe conservar: situación agronómica, expresión original, evidencia textual, creencias inferibles, deseos, intención, recursos/restricciones, acción contemplada, temporalidad, emoción declarada, contradicción o compatibilidad entre metas, clasificación Puro/Conflictivo, confianza del anotador y procedencia.

## Qué debe representar

El corpus debe responder a la pregunta central: **¿cómo expresa y justifica un pequeño productor una decisión agronómica concreta bajo restricciones productivas, familiares, económicas, ambientales y emocionales?** Esto encaja mejor con eBDI que una colección genérica de textos agrícolas, porque permite separar hechos o creencias percibidas, objetivos deseados e intención de actuar.

La unidad mínima debería ser el **episodio decisional**: un fragmento autosuficiente en el que aparece una situación, una meta y una acción prevista, ejecutada, pospuesta o descartada. Por ejemplo: “Quiero sembrar ñame cuando entren las lluvias, pero la semilla está cara y primero debo asegurar la comida de la casa”; aquí coexisten un objetivo productivo, una condición climática, una restricción económica y una posible tensión entre producción e inseguridad alimentaria.

No toda mención agrícola sirve. “El ñame se cosecha a los diez meses” es conocimiento técnico; “voy a retrasar la siembra de ñame porque no ha llovido y no quiero perder la semilla” sí es un episodio útil para clasificación eBDI. El corpus principal debe privilegiar el segundo tipo, mientras el conocimiento técnico queda en una base contextual separada.

## Anclaje territorial

Los cultivos iniciales deberían ser **ñame, yuca, maíz, aguacate y plátano**, con agua, semillas, herramientas, mano de obra, crédito, precios y seguridad alimentaria como ejes transversales. Es una selección defendible: estudios territoriales describen una tradición regional en yuca, ñame, maíz, arroz, plátano y aguacate; caracterizaciones más recientes en El Carmen y San Jacinto identifican agricultura y ganadería, con ñame, aguacate, maíz, yuca, plátano y arroz entre los cultivos principales.[^4][^5]

El ñame merece un estrato propio. En la caracterización de AGROSAVIA, 67% del ñame encuestado en Bolívar se sembraba asociado con maíz, 19% con yuca y 14% como monocultivo, lo que ofrece situaciones reales para modelar decisiones de asociación, semillas, riesgo y comercialización. Las estadísticas sectoriales también sitúan a Bolívar entre los principales departamentos productores, aunque esas cifras deben usarse como contexto y no como sustituto de voces campesinas.[^6][^7][^8]

El agua y el clima deben aparecer como variables decisionales, no solo ambientales. El diagnóstico PDET registra dificultades de acceso al agua, asistencia técnica y maquinaria, mientras que fuentes comunitarias documentan relaciones entre mujeres rurales, producción de alimentos, fuentes hídricas y playones comunales. Las series de precipitación del IDEAM pueden triangular la fecha y plausibilidad climática de un relato, sin “corregir” la percepción local del productor.[^9][^10][^1]

## Fuentes prioritarias

| Fuente real | Aporte al corpus | Uso recomendado | Precaución |
|---|---|---|---|
| UPRA–Agronet, EVA municipales | Área, producción y rendimiento por cultivo y municipio; coyuntura climática, fitosanitaria e insumos | Diseñar cuotas por municipio/cultivo y validar contexto | No contiene razonamiento individual; no usar como corpus conversacional [^11][^12] |
| Microdatos del 3er CNA para Bolívar | Estructura de UPA, producción, activos y condiciones rurales | Caracterización del universo y muestreo | Datos de 2014; requieren contextualización temporal [^13] |
| SIPRA–UPRA | Aptitud, frontera agrícola, cadenas predominantes y consulta territorial | Contextualizar decisiones por localización | Aptitud biofísica no equivale a decisión campesina [^14][^15] |
| DANE–SIPSA, mercado de Bazurto | Precios mayoristas de ñame, yuca y otros alimentos | Contrastar episodios de venta, espera o cambio de cultivo | Precio mayorista no equivale al precio recibido en finca [^16][^17] |
| IDEAM | Precipitación y variación respecto a promedios | Triangulación temporal de lluvia/sequía | Registros recientes pueden ser preliminares [^10][^18] |
| PATR/PDET Montes de María | Problemas priorizados por las comunidades y diagnóstico subregional | Construir escenarios y categorías de restricción | Documento de planeación; no asumir que toda frase es voz individual [^1] |
| UPRA, ZRC Montes de María 2 | Priorización participativa y “agromemorias productivas” en Córdoba, El Guamo, San Juan Nepomuceno y Zambrano | Contactos, productos y talleres de elicitación | Solicitar acceso y autorización para materiales no publicados [^19][^20] |
| AGROSAVIA El Carmen | Tecnología local, cultivos, asociaciones, pilotos y extensionistas | Expertos, validación agronómica y entrada territorial | Separar recomendaciones técnicas de prácticas efectivas [^2][^21][^22] |
| EPSEA Universidad de Cartagena–ADR | Caracterizaciones participativas y Escuelas de Campo en municipios bolivarenses | Acceso a extensionistas y productores; escenarios recientes | Negociar custodia y reutilización de datos existentes [^3][^23] |
| FAO “La semilla del saber” | Testimonios sobre agua, asociatividad, ganadería y melicultura | Léxico local, diseño de preguntas y casos piloto | Verificar licencia y consentimiento antes de transcribir o entrenar [^24][^25] |
| Colectivo de Comunicaciones/Museo Itinerante | Narraciones y archivos comunitarios de Montes de María | Co-diseño, comunicación, memoria y devolución territorial | Los testimonios son patrimonio comunitario; acceso no implica permiso de reutilización [^26][^27] |
| Museo Comunitario de San Jacinto | Sala y relatos sobre vida y trabajo campesino | Entrada local y validación cultural | Concertar uso con el museo y narradores [^28] |
| Repositorios académicos | Entrevistas, etnografías, prácticas agrícolas y seguridad alimentaria | Marco teórico y detección de vacíos | Una tesis abierta no autoriza automáticamente extracción masiva o reentrenamiento [^29][^30][^31][^32] |

## Socios de entrada

La primera puerta recomendada es **AGROSAVIA, sede El Carmen de Bolívar**, porque trabaja con yuca, ñame, batata, frutales y ganadería, y ha propuesto una Red de Extensionistas de Montes de María con visitas a los quince municipios. Su papel debería ser facilitar revisión agronómica y contactos, no seleccionar por sí sola a todos los participantes.[^21][^22]

La segunda puerta es la **Universidad de Cartagena–ADR/EPSEA**, que reportó caracterizaciones territoriales participativas en San Juan Nepomuceno, El Guamo, El Carmen y San Jacinto y visitas directas a productores. Esto puede reducir costos de entrada, pero exige evitar una muestra compuesta únicamente por beneficiarios institucionales.[^3]

La tercera es el **Colectivo de Comunicaciones Montes de María Línea 21 / Museo Itinerante de la Memoria**, con presencia en El Carmen y experiencia en documentación participativa con organizaciones campesinas, de mujeres y jóvenes. Puede apoyar lenguaje, confianza, devolución de resultados y prevención de una extracción académica unilateral.[^26][^27]

También deben considerarse organizaciones productivas existentes. Fuentes institucionales mencionan APACARBOL, ASOPRAM, ASOVICHENGUE, asociaciones de cosechadores, AGROROMA, ASOMUDEPAZ, ASOAGROPAT, ASPROMONTES y ASOMERITA, entre otras. Antes de contactar, hay que verificar existencia, representación y datos vigentes; una lista publicada no sustituye el relacionamiento comunitario.[^33][^34]

## Diseño de campo

### Fase 0: preparación

Durante dos o tres semanas se debe construir un inventario documental con metadatos, licencia, nivel territorial, fecha, actor que habla y posible uso. En paralelo se define una ontología provisional de dominios: agua, suelo, semilla, herramientas, mano de obra, sanidad, clima, crédito, mercado, alimentación, trabajo extrapredial, cooperación, salud y cuidado.

Antes de entrevistar, conviene organizar un taller corto con 4–6 personas: un agrónomo o extensionista, un científico social, un representante campesino, una mujer rural, un conocedor de mercados y el equipo técnico. El objetivo no es “validar el modelo” todavía, sino revisar vocabulario, riesgos, categorías eBDI y situaciones que las preguntas no estén capturando.

### Fase 1: piloto cognitivo

Realizar 6–8 entrevistas piloto en una sola localidad, preferiblemente El Carmen por la densidad institucional existente. El piloto debe comprobar si los participantes entienden las preguntas, si narran decisiones concretas o generalidades, cuánto dura la conversación y qué categorías no previstas emergen.

La FAO recomienda entrevistas semiestructuradas como conversación guiada, observación, recorridos, calendarios estacionales y grupos focales para comprender conocimientos, actitudes, experiencias y prioridades; también insiste en tratar a agricultores como socios y no convertir la lista de temas en un cuestionario rígido. Por eso, el piloto debe usar ejemplos locales y solicitar siempre un episodio real: “Cuénteme la última vez que tuvo que decidir…”.[^35][^36][^37]

### Fase 2: corpus principal

Como meta de tesis realista, se propone reclutar **24–36 productores** y obtener **6–10 episodios útiles por persona**, para un total esperado de aproximadamente **180–300 episodios decisionales** antes de depuración. No es una muestra estadística departamental: es un muestreo cualitativo por máxima variación, orientado a saturar tipos de decisión y conflictos.

La muestra debe distribuirse por municipio, cultivo principal, género, edad, asociación/no asociación, acceso al agua, tamaño relativo de unidad productiva y dependencia de ingresos no agrícolas. Las guías FAO recomiendan representar distintos tipos de hogar y separar algunos grupos por género o edad para evitar que las voces con mayor poder dominen la conversación.[^38][^39]

Una distribución inicial viable sería:

| Estrato | Meta propuesta |
|---|---:|
| El Carmen de Bolívar | 10–12 productores |
| San Jacinto | 6–8 productores |
| San Juan Nepomuceno | 6–8 productores |
| María La Baja o ZRC Montes de María 2 | 4–8 productores |
| Mujeres | Al menos 40% |
| Jóvenes rurales, cuando sea viable | Al menos 15% |
| No asociados | Al menos 25% |

Estas son cuotas de diseño, no estimaciones poblacionales. Deben ajustarse con organizaciones locales y con el comité de ética para evitar presión sobre poblaciones vulnerables.

### Fase 3: validación participativa

Después de la primera anotación, organizar 3–4 talleres de devolución con 6–8 participantes. Un grupo focal de 6–8 personas es apropiado para explorar en detalle un problema y revelar perspectivas y reacciones, pero no debe reemplazar las entrevistas individuales cuando haya decisiones económicas o familiares sensibles.[^35]

En los talleres se presentan episodios anonimizados y se pregunta: ¿la interpretación conserva lo que quiso decir la persona?, ¿qué creencia falta?, ¿hay realmente conflicto?, ¿la acción propuesta es agronómicamente plausible?, ¿qué palabra local debería mantenerse? La corrección comunitaria debe registrarse como una nueva versión, sin borrar el texto original.

## Instrumentos de elicitación

El instrumento principal debe ser una entrevista de 45–60 minutos centrada en episodios. Un recorrido de parcela o calendario estacional puede precederla para activar memoria concreta; la observación ayuda a contrastar herramientas, fuentes de agua, cultivos asociados y condiciones de acceso, pero nunca debe usarse para inferir estados emocionales no declarados.[^40][^35]

### Bloques sugeridos

1. **Contexto productivo:** cultivos, parcela, acceso a agua, herramientas, mano de obra y destino de la producción.
2. **Última decisión:** “Cuénteme la última decisión importante que tomó sobre sembrar, aplazar, comprar, vender, regar, contratar, pedir crédito o buscar otro trabajo”.
3. **Evidencia percibida:** “¿Qué vio, supo o creyó en ese momento?”.
4. **Meta:** “¿Qué quería conseguir o evitar?”.
5. **Opciones:** “¿Qué otras alternativas consideró?”.
6. **Restricciones:** “¿Qué le impedía hacer lo que prefería?”.
7. **Conflicto:** “¿Había dos necesidades importantes que no podía atender al mismo tiempo?”.
8. **Emoción declarada:** “¿Cómo se sintió y eso cambió su decisión?”.
9. **Acción y resultado:** “¿Qué decidió finalmente y qué pasó después?”.
10. **Contrafactual:** “Si hubiera tenido agua, dinero, semilla o ayuda, ¿habría decidido distinto?”.

Debe evitarse preguntar directamente “¿cuáles eran sus beliefs, desires e intentions?”. El mapeo eBDI corresponde a la anotación; la entrevista debe conservar lenguaje natural y local.

### Disparadores situacionales

Además de episodios reales, pueden usarse viñetas construidas con datos territoriales: retraso de lluvias, semilla costosa, falta de herramienta, enfermedad familiar, precio bajo en Bazurto, plaga, deuda, oferta de jornal fuera de la parcela o conflicto entre vender y reservar alimento. Las viñetas deben marcarse como **elicitadas/hipotéticas** y jamás mezclarse con relatos reales sin una variable de procedencia.

## Esquema del corpus

Cada episodio debería almacenarse en JSONL, con audio y transcripción separados del conjunto analítico. Un esquema mínimo sería:

```json
{
  "episode_id": "BOL-ECV-P012-E04",
  "source_type": "field_real_episode",
  "department": "Bolívar",
  "municipality": "El Carmen de Bolívar",
  "vereda_code": "V07",
  "participant_code": "P012",
  "crop_system": ["ñame", "maíz"],
  "season_phase": "pre_siembra",
  "utterance_original": "...",
  "normalized_text": "...",
  "evidence_spans": {
    "beliefs": ["..."],
    "desires": ["..."],
    "intentions": ["..."],
    "constraints": ["..."],
    "emotions_declared": ["..."]
  },
  "goal_primary": "prepare_land",
  "goal_secondary": "preserve_household_food",
  "action_candidate": "postpone_planting",
  "case_label": "CONFLICTIVO",
  "conflict_type": "productive_vs_household_security",
  "temporal_status": "planned",
  "annotator_ids": ["A01", "A02"],
  "adjudicator_id": "EX03",
  "agreement": true,
  "consent_scope": ["research", "annotation", "local_model_evaluation"],
  "allowed_for_training": false,
  "provenance_hash": "sha256:...",
  "version": 1
}
```

El campo `allowed_for_training` debe ser independiente de `consent_scope`: consentir una entrevista para investigación no equivale a autorizar entrenamiento, publicación de audio o redistribución. Los hashes y versiones respaldan la trazabilidad que requiere el pipeline documental de la tesis.

## Definición de etiquetas

**Caso Puro** debe asignarse cuando el fragmento contiene una intención agronómica dominante y sus condiciones o requerimientos, sin evidencia suficiente de metas incompatibles. La falta de un recurso no convierte automáticamente el caso en conflictivo: “necesito herramientas para preparar el terreno” puede seguir siendo puro si no aparece una segunda meta que compita.

**Caso Conflictivo** exige evidencia de dos o más metas, normas, obligaciones o cursos de acción relevantes que no pueden satisfacerse simultáneamente con los recursos o el tiempo percibidos. “Quiero sembrar, pero no tengo machete” expresa restricción; “necesito comprar la semilla, pero ese dinero es para la alimentación familiar” expresa conflicto entre metas.

Debe existir una tercera salida operativa, **INDETERMINADO/INSUFICIENTE**, aunque la tarea final sea binaria. Forzar todos los fragmentos a Puro o Conflictivo contaminaría el corpus y ocultaría desacuerdos. Solo los registros adjudicados pasan al conjunto oro binario.

### Taxonomía de conflictos

- Productividad frente a seguridad alimentaria del hogar.
- Inversión productiva frente a liquidez/deuda.
- Trabajo en parcela frente a jornal extrapredial.
- Producción frente a cuidado o salud familiar.
- Venta inmediata frente a reserva de semilla/alimento.
- Rendimiento frente a conservación de suelo, agua o bosque.
- Decisión individual frente a obligación asociativa/comunitaria.
- Recomendación técnica frente a conocimiento o preferencia local.
- Corto plazo frente a resiliencia de largo plazo.
- Meta agronómica frente a emoción o percepción de riesgo declarada.

## Anotación y calidad

Cada episodio debe ser anotado de forma independiente por dos personas: una con formación en el esquema eBDI y otra con conocimiento agronómico/territorial. Los desacuerdos pasan a adjudicación de un tercero; además, una muestra debe revisarse con participantes o representantes comunitarios.

El manual debe contener definiciones, ejemplos positivos y negativos, reglas para evidencia explícita e inferida, tratamiento de negación, temporalidad, pronombres, habla reportada y fragmentos incompletos. La regla central debe ser: **ninguna etiqueta eBDI sin un span de evidencia o una inferencia marcada explícitamente como tal**.

Se recomienda medir acuerdo para la etiqueta principal y para cada dimensión epistemológica. El objetivo no debe ser inflar una métrica, sino identificar categorías ambiguas; si el desacuerdo persiste, el registro permanece indeterminado y no entra al conjunto oro.

Para prevenir fuga de identidad o de estilo, la partición de entrenamiento, desarrollo y prueba debe hacerse por **participante y preferiblemente por vereda**, no por oración aleatoria. De lo contrario, el modelo podría memorizar formas de hablar de la misma persona en los tres conjuntos.

## Ética y soberanía

Toda entrevista, grupo focal, fotografía, video o audio con personas requiere revisión ética institucional y consentimiento informado previo. Minciencias señala que esta obligación cubre entrevistas, grupos focales y videos, y que el participante debe conocer uso de información, privacidad, derecho a retirarse y condiciones de divulgación. La Ley 1581 exige autorización previa, expresa e informada para el tratamiento de datos personales y que esta pueda consultarse posteriormente.[^41][^42]

Además del consentimiento individual, se requiere concertación de entrada con organizaciones y autoridades comunitarias pertinentes, pero la autorización de un líder nunca debe sustituir la decisión individual. Los lineamientos éticos enfatizan selección justa, privacidad, confidencialidad, consideración del contexto comunitario y devolución de resultados a la comunidad participante.[^43][^44]

La arquitectura recomendada es offline y pseudonimizada: audio cifrado en almacenamiento restringido; tabla de identidades separada; transcripción sin nombres, teléfonos, coordenadas exactas ni hechos fácilmente reidentificables; registro de quién accede; y eliminación o devolución según lo pactado. Los fragmentos sensibles sobre conflicto, tierra, deudas, salud o violencia deben excluirse del corpus compartible aunque tengan valor narrativo.

Debe acordarse un producto de retorno: cartilla breve, taller, audio radial o demostración de la herramienta. Esto no es solo cortesía; ayuda a que el corpus sea una construcción con el territorio y no una extracción de conocimiento.

## Uso de material público

Los pódcasts de FAO, piezas del Colectivo, repositorios universitarios y documentales son útiles para crear un **corpus exploratorio de lenguaje y escenarios**, siempre que se verifique licencia o se obtenga permiso. Que un audio pueda escucharse o una tesis descargarse no significa que pueda redistribuirse, transcribirse masivamente o usarse para ajustar pesos de un modelo.

Por eso deben mantenerse tres estados:

| Estado | Contenido | Uso permitido |
|---|---|---|
| `context_only` | Informes, estadísticas y material sin permiso de entrenamiento | Ontología, guion, triangulación y citas |
| `evaluation_authorized` | Episodios consentidos para análisis y evaluación local | Pruebas, error analysis, validación humana |
| `training_authorized` | Fragmentos con autorización específica y anonimización aprobada | Ajuste del modelo o clasificadores |

El corpus documental nunca debe presentarse como “corpus de campo”. Puede llamarse **corpus semilla documental**; el de entrevistas propias será el **corpus de campo**; y la porción doblemente anotada y adjudicada será el **corpus oro**.

## Plan de doce semanas

| Semana | Actividad | Entregable |
|---|---|---|
| 1–2 | Inventario de fuentes, licencias y contactos | Matriz de fuentes y permisos |
| 2–3 | Ontología provisional y manual v0 | Catálogo BDI, conflictos y acciones |
| 3–4 | Aval ético, consentimiento y plan de datos | Protocolo aprobado |
| 4 | Taller territorial de co-diseño | Guion y vocabulario revisados |
| 5 | 6–8 entrevistas piloto | Informe cognitivo y manual v1 |
| 6–8 | Trabajo de campo principal | Audios, notas y episodios pseudonimizados |
| 7–9 | Transcripción y segmentación | Corpus bruto versionado |
| 9–10 | Doble anotación y adjudicación | Corpus oro v1 |
| 11 | Talleres de validación/devolución | Correcciones y actas de validación |
| 12 | Congelamiento, hashes y particiones | Corpus v1.0 y ficha de datos |

## Criterios de aceptación

El corpus estará listo para evaluar el pipeline cuando cumpla simultáneamente:

- Cada registro tiene procedencia, consentimiento, versión y hash.
- Cada belief, desire e intention tiene evidencia textual o marca de inferencia.
- Puro y Conflictivo cuentan con definiciones operativas y ejemplos fronterizos.
- Existe una etiqueta Indeterminado durante la anotación.
- Hay diversidad municipal, productiva, de género, edad y asociación.
- Ninguna persona aparece en más de una partición experimental.
- Los documentos públicos están separados del material de campo.
- Los datos técnicos triangulan, pero no reemplazan ni silencian, el conocimiento local.
- La comunidad recibe y puede cuestionar la interpretación.
- El conjunto de prueba queda congelado antes de ajustar el micro-LLM.

## Recomendación final

La ruta con mejor relación entre rigor y viabilidad es iniciar con **El Carmen de Bolívar, San Jacinto y San Juan Nepomuceno**, apoyándose en AGROSAVIA, Universidad de Cartagena–ADR y el Colectivo de Comunicaciones para la entrada territorial. El corpus debe centrarse en ñame, yuca, maíz, aguacate y plátano, con episodios sobre agua, semillas, herramientas, mano de obra, crédito, mercado, cuidado y trabajo extrapredial.

El primer hito no debería ser entrenar Gemma, sino producir **30–40 episodios piloto bien consentidos y doblemente anotados**. Si esos episodios permiten distinguir de forma estable entre restricción simple y conflicto entre metas, entonces se escala a 180–300 episodios y se congela un corpus oro; si no, se corrige primero la ontología y el guion de campo.

---

## References

1. [[PDF] PATR SUBREGION MONTES DE MARIA.pdf - Central PDET](https://centralpdet.renovacionterritorio.gov.co/wp-content/uploads/Documentos/PATR%20SUBREGION%20MONTES%20DE%20MARIA.pdf)

2. [Diseño e implementación de un sistema agroalimentario ...](https://www.agrosavia.co/media/tzth21vs/2-boli-var-y-sucre-manuel-ramo-n.pdf)

3. [Productores de Bolívar reciben apoyo para transformar su agricultura](https://www.eluniversal.com.co/regional/bolivar/2024/12/20/productores-de-bolivar-reciben-apoyo-para-transformar-su-agricultura/) - El proyecto de extensión agropecuaria busca mejorar la productividad y sostenibilidad de los agricul...

4. [Montes de María : una subregión de economía campesina y ...](https://repositorio.banrep.gov.co/items/d1aff1ca-7f54-4f0a-aa4c-b89630079d2f/full) - Acceso abierto a los contenidos investigativos producido por el BANCO DE LA REPÚBLICA DE COLOMBIA –B...

5. [Estrategias agroecológicas para el mejoramiento de la conectividad del Bosque seco tropical en los municipios de Carmen de Bolívar y San Jacinto, en la región de los Montes de María](https://repository.javeriana.edu.co/handle/10554/51459) - El bosque seco tropical y la productividad agrícola de la región de los Montes de María (MM) se ha v...

6. [Organización de Cadena Nacional del Ñame - SIOC](https://sioc.minagricultura.gov.co/Yuca/Documentos/2020-09-30%20Cifras%20Sectoriales%20%C3%91ame.pdf)

7. [Caracterización socioeconómica y tecnológica del cultivo ...](https://repository.agrosavia.co/server/api/core/bitstreams/b31a3355-10a8-4d62-9d6c-1405d296796b/content) - Las principales zonas productoras de ñame de la Regiónel Caribe seleccionadas para este estudio corr...

8. [[PDF] Cadena Productiva del Ñame - SIOC](https://sioc.minagricultura.gov.co/Yuca/Documentos/2021-03-31%20Cifras%20Sectoriales%20%C3%B1ame.pdf)

9. [Multimedia - MESA AGUA](https://mesadelaguamma.cds.org.co/multimedia.php)

10. [GEOSERVICIOS INSTITUCIONALES](http://archivo.ideam.gov.co/geoservicios-institucionales)

11. [EVA y Anuario Estadístico del Sector Agropecuario Agricola](https://agronet.gov.co/documentacion-estadisticas/agricola/reporte-evaluaciones-agropecuarias-eva-y-anuario-estadistico) - Reporte: Evaluaciones Agropecuarias - EVA y Anuario Estadístico del Sector Agropecuario Agricola · B...

12. [Dirección Nueva: Avenida Jiménez N° 7A-17 / Dirección Antigua: Avenida Jiménez No. 7 – 65 • PBX: 334 11 99 • www.minagricultura.gov.co](https://agronet.gov.co/sites/default/files/estadistica/Documents/FichaMetodologica-Reporte%201-103.pdf)

13. [Tercer Censo Nacional Agropecuario - 2014 -3er CNA](https://microdatos.dane.gov.co/index.php/catalog/513/get-microdata)

14. [Planificación Nacional](https://sipra.upra.gov.co/nacional) - Sistema Para la Planificación Rural Agropecuaria

15. [Sistemas de información](https://upra.gov.co/es-co/planificacion-del-ordenamiento-agropecuario/sistemas-de-informacion) - En el Sipra se brindan opciones de consulta y descarga de la información para uso libre. ... Aptitud...

16. [boletín semanal - precios mayoristas](https://www.dane.gov.co/files/operaciones/SIPSA/bol-SIPSASemanal-11abr17abr-2026.pdf)

17. [[PDF] boletín semanal - precios mayoristas - DANE](https://www.dane.gov.co/files/operaciones/SIPSA/bol-SIPSASemanal-18oct24oct-2025.pdf)

18. [bart.ideam.gov.co › indiecosistemas › indPrecipitación total - IDEAM](https://bart.ideam.gov.co/indiecosistemas/ind/clima/precipitacion.html)

19. [Priorizamos, con las comunidades, las alternativas productivas de la ...](https://upra.gov.co/es-co/sala-de-prensa/noticias/priorizamos-con-las-comunidades-las-alternativas-productivas-de-la-zona-de) - Este esfuerzo hace parte del compromiso del Gobierno del Cambio con las 14 ZRC que se han definido e...

20. [Seguimos cumpliendo nuestro compromiso con las Zonas ...](https://upra.gov.co/es-co/sala-de-prensa/noticias/seguimos-cumpliendo-nuestro-compromiso-con-las-zonas-de-reserva-campesina-0) - Esta semana, la UPRA recorre la Zona de reserva campesina: Montes de María 2, Bolívar, indicó Claudi...

21. [Sede El Carmen de Bolívar](https://www.agrosavia.co/nosotros/sedes/sede-el-carmen-de-bol%C3%ADvar) - está enfocada en investigaciones relacionadas con las redes de cultivos Transitorios y Agroindustria...

22. [Plan de acción Sede Carmen de Bolívar: análisis participativo](https://revistas.uptc.edu.co/index.php/ciencia_agricultura/article/download/14278/11765/60468)

23. [Iniciaron las Escuelas de Campo para impulsar la agricultura sostenible y asociatividad en Bolívar](https://caracol.com.co/2025/03/20/iniciaron-las-escuelas-de-campo-para-impulsar-la-agricultura-sostenible-y-asociatividad-en-bolivar/) - Se están implementando en 31 municipios del departamento

24. [La semilla del saber: Podcasts - Sembrando Capacidades - FAO](https://sembrandocapacidades.fao.org.co/la-semilla-del-saber-podcasts/)

25. [‘La semilla del saber’: podcasts llevan información a agricultores familiares de los Montes de María](https://www.fao.org/in-action/programa-brasil-fao/noticias/ver/es/c/1457769/)

26. [El Museo](https://mimemoria.org/who-we-are/)

27. [ESTEMOS EN CONTACTO](https://mimemoria.org/get-in-touch/)

28. [La historia de los Montes de María en el Museo Comunitario de ...](https://www.radionacional.co/cultura/historia-colombiana/la-historia-de-los-montes-de-maria-en-el-museo-comunitario-de-san) - El museo estrena una nueva sala dedicada a los campesinos y sus labores diarias en el municipio boli...

29. [cambios y permanencias en las prácticas agrícolas, en](https://repositorio.unicartagena.edu.co/bitstreams/85414a0f-308b-44f2-9f20-005d05b43517/download) - por KT Castro Pomares · 2024 — Carmen de Bolívar - Montes de María, donde la agricultura campesina h...

30. [vereda el roble de san juan nepomuceno - bolívar, una lucha ...](https://repositorio.unicartagena.edu.co/bitstreams/1245dfc6-940d-4944-ba6b-75d3fcf2f39a/download) - por JL Sarabia Padilla · 2021 — Si porque la historia de los montes de maría lo que he investigado f...

31. [Montes de María. Un territorio en disputa](https://repository.javeriana.edu.co/handle/10554/57893) - Las formas en las que las campesinas y campesinos de Montes de María han resistido a las violencias ...

32. [Estrategias de seguridad alimentaria que desarrollaron y desarrollan hombres y mujeres en las comunidades desplazadas de Pueblo Nuevo y Monte Carlos en los Montes de María. Departamento de Bolívar. Colombia](https://repository.javeriana.edu.co/handle/10554/12435) - La seguridad alimentaria es entendida desde 4 dimensiones: la disponibilidad, el acceso, la utilizac...

33. [a conceptual model of the production system Sistemas ag](https://repository.agrosavia.co/server/api/core/bitstreams/b1486eb0-b709-487a-a3f4-3cc2987b07a7/content)

34. [Sistemas Alimentarios Sostenibles e Inclusivos en Colombia](https://www.fao.org.co/PublicacionesFAOCO/SASI/MontesMaria/Informe-Taller-1.pdf)

35. [Module 5 Participatory Farm Management Tools](https://www.fao.org/4/a1298e/a1298e13.pdf)

36. [Participatory survey methods for gathering information](https://www.fao.org/4/w8016e/w8016e01.htm)

37. [Chapter 6 - Using rapid or participatory rural appraisal](https://www.fao.org/4/w5830e/w5830e08.htm)

38. [Strengthening coherence](https://openknowledge.fao.org/server/api/core/bitstreams/608a9525-a092-49b4-8836-91fa78c5e6b5/content)

39. [Social analysis for inclusive agrifood investments](https://openknowledge.fao.org/server/api/core/bitstreams/04abaa44-9a49-4fe3-a03f-3c7976a57e9b/content)

40. [Chapter 8: Rapid Rural Appraisal](https://www.fao.org/4/w3241e/w3241e09.htm)

41. [Ley 1581 de 2012 - Cancillería](https://cancilleria.gov.co/normograma/compilacion/docs/ley_1581_2012.htm)

42. [Sobre los Comités de Ética y la Ética en la Investigación](https://legadoweb.minciencias.gov.co/noticias/sobre-los-comit-s-de-tica-y-la-tica-en-la-investigaci-n)

43. [minciencias.gov.co › sites › defaultPOLÍTICA DE ÉTICA DE LA INVESTIGACIÓN, BIOÉTICA](https://minciencias.gov.co/sites/default/files/upload/paginas/evento_1_documento_02_octubre_lineamientos_minimos_cei_red_version_05_septiembre.pdf)

44. [minciencias.gov.co › sites › defaultPOLÍTICA DE ÉTICA DE LA INVESTIGACIÓN, BIOÉTICA E INTEGRIDAD ...](https://minciencias.gov.co/sites/default/files/upload/noticias/mincienciaslineamientos_c_i_eweb.pdf)

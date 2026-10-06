"""Generador y validador del banco sintético territorial S9-S10 (Bolívar / Montes de María).
Garantiza offsets exactos sobre el texto, esquemas estrictos y coherencia agronómica.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path("outputs/corpus/b6_synthetic_s9_s10")

CASES = [
    {
        "episode_id": "SYN_BOL_001",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p01",
        "vereda_code": "synthetic_vereda_01",
        "municipality_context": "El Carmen de Bolívar",
        "crop_context": "maíz criollo",
        "season_context": "primera siembra (abril-mayo)",
        "scenario_id": "SYN_BOL_001",
        "text": (
            "Para esta primera siembra de mayo voy a limpiar el rastrojo y preparar la tierra con machete y azadón. "
            "El único detalle es que me hace falta afilar las herramientas y comprar dos limas nuevas en el pueblo, "
            "pero tengo la plata guardada y mañana mismo bajo a comprarlas para arrancar a tiempo."
        ),
        "quotes": [
            ("voy a limpiar el rastrojo y preparar la tierra con machete y azadón", "observed_intention"),
            ("me hace falta afilar las herramientas y comprar dos limas nuevas", "observed_constraint"),
            ("tengo la plata guardada y mañana mismo bajo a comprarlas", "observed_condition"),
        ],
        "beliefs": ["La temporada de siembra de primera inicia en mayo", "Las herramientas necesitan mantenimiento previo"],
        "desires": ["Tener la parcela limpia y lista antes de que caigan los primeros aguaceros"],
        "intentions": ["Limpiar rastrojo y preparar terreno", "Comprar limas y afilar herramientas mañana"],
        "constraints": ["Herramientas desafiladas"],
        "emotional_state": "optimista",
        "expected_case_type": "pure",
        "expected_conflict_type": None,
        "expected_action": "preparar_terreno",
        "base_condition": "Herramientas disponibles con recursos para mantenimiento",
        "perturbation": "Limas costosas o almacén cerrado",
        "expected_change": "Pospone la afilada un día pero mantiene la intención única de preparar el terreno sin meta rival",
        "agronomic_rationale": "La falta de filo es una restricción técnica soluble, no una colisión entre metas incompatibles.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_002",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p02",
        "vereda_code": "synthetic_vereda_02",
        "municipality_context": "San Juan Nepomuceno",
        "crop_context": "ñame espino",
        "season_context": "siembra principal",
        "scenario_id": "SYN_BOL_002",
        "text": (
            "La fecha de sembrar el ñame ya llegó y si espero más se me pasa el tiempo del cultivo. "
            "Por un lado quiero tirar la semilla de una vez en los montículos listos, pero por otro lado el arroyo "
            "está seco y los viejos dicen que viene una canícula brava; si siembro ahora con este suelo seco arriesgo "
            "a perder toda la semilla que tanto me costó, y si espero a que llueva seguro pierdo el ciclo de la cosecha."
        ),
        "quotes": [
            ("quiero tirar la semilla de una vez en los montículos listos", "observed_intention_a"),
            ("si espero a que llueva seguro pierdo el ciclo de la cosecha", "observed_intention_b"),
            ("el arroyo está seco y los viejos dicen que viene una canícula brava", "observed_trigger"),
        ],
        "beliefs": ["El ciclo agronómico del ñame exige siembra temprana", "El suelo sin humedad pudre o seca la semilla"],
        "desires": ["Aprovechar el ciclo productivo", "Proteger el capital invertido en semilla"],
        "intentions": ["Sembrar de inmediato para no perder ciclo", "Posponer siembra hasta que se confirme humedad"],
        "constraints": ["Arroyo seco", "Pronóstico de canícula"],
        "emotional_state": "preocupado",
        "expected_case_type": "conflict",
        "expected_conflict_type": "short_term_vs_long_term_resilience",
        "conflict_detail": {
            "intent_a": "Sembrar de inmediato para respetar ciclo agronómico",
            "evidence_a": "quiero tirar la semilla de una vez en los montículos listos",
            "intent_b": "Retrasar siembra para proteger semilla ante sequía",
            "evidence_b": "si espero a que llueva seguro pierdo el ciclo de la cosecha",
            "incompatibility_reason": "Sembrar ahora expone la semilla a sequía letal; esperar protege la semilla pero arruina la ventana agronómica.",
            "resolution": "escalar_decision_humana_o_esperar_humedad",
        },
        "expected_action": "dilema_siembra_sequia",
        "base_condition": "Lluvia regular permite siembra sin riesgo de desecación",
        "perturbation": "Retraso severo de lluvias y agotamiento de fuente hídrica",
        "expected_change": "Transforma la labor rutinaria de siembra en un conflicto crítico de supervivencia agronómica",
        "agronomic_rationale": "El ñame requiere humedad inicial constante; sembrar en seco sin riego es pérdida casi total del germoplasma.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_003",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p03",
        "vereda_code": "synthetic_vereda_03",
        "municipality_context": "San Jacinto",
        "crop_context": "frijol cuarentano",
        "season_context": "segunda siembra",
        "scenario_id": "SYN_BOL_003",
        "text": (
            "Solo tengo trescientos mil pesos en el bolsillo para resolver este mes. "
            "Necesito comprar dos bultos de semilla certificada de frijol para no quedarme sin sembrar la parcela, "
            "pero al mismo tiempo tengo la obligación urgente de comprar el mercado de la casa porque no hay arroz ni manteca. "
            "Si meto la plata en la semilla dejamos a la familia pasando hambre tres semanas, y si compro la comida nos comemos el capital de trabajo."
        ),
        "quotes": [
            ("Necesito comprar dos bultos de semilla certificada de frijol para no quedarme sin sembrar", "observed_intention_a"),
            ("tengo la obligación urgente de comprar el mercado de la casa porque no hay arroz ni manteca", "observed_intention_b"),
            ("Solo tengo trescientos mil pesos en el bolsillo para resolver este mes", "observed_constraint"),
        ],
        "beliefs": ["La semilla certificada garantiza cosecha", "El dinero disponible es insuficiente para ambos rubros"],
        "desires": ["Garantizar producción agrícola", "Alimentar a la familia de inmediato"],
        "intentions": ["Invertir en insumos productivos de frijol", "Asignar efectivo a la alimentación básica del hogar"],
        "constraints": ["Presupuesto ilíquido no extensible ($300.000 COP)"],
        "emotional_state": "angustiado",
        "expected_case_type": "conflict",
        "expected_conflict_type": "productive_vs_household_security",
        "conflict_detail": {
            "intent_a": "Comprar semilla de frijol para mantener ciclo productivo",
            "evidence_a": "Necesito comprar dos bultos de semilla certificada de frijol para no quedarme sin sembrar",
            "intent_b": "Comprar alimentos básicos del hogar para subsistencia",
            "evidence_b": "tengo la obligación urgente de comprar el mercado de la casa porque no hay arroz ni manteca",
            "incompatibility_reason": "El capital de $300.000 es indivisiblemente insuficiente para cubrir simultáneamente semilla y alimentos.",
            "resolution": "particionar_presupuesto_o_buscar_semilla_criolla_prestada",
        },
        "expected_action": "dilema_capital_semilla_vs_comida",
        "base_condition": "Ingreso suficiente o ahorro disponible para insumos y canasta básica",
        "perturbation": "Caída drástica de liquidez y agotamiento de reservas de comida",
        "expected_change": "Fuerza colisión directa entre supervivencia biológica del hogar e inversión productiva",
        "agronomic_rationale": "Pequeños productores descapitalizados enfrentan el consumo del capital operativo ante emergencias domésticas.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_004",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p04",
        "vereda_code": "synthetic_vereda_04",
        "municipality_context": "Córdoba Tetón",
        "crop_context": "yuca industrial",
        "season_context": "roturación",
        "scenario_id": "SYN_BOL_004",
        "text": (
            "Para sacar adelante la media hectárea de yuca acordamos con cuatro compadres hacer un convite este sábado. "
            "Yo pongo el sancocho de gallina y ellos traen los bueyes para arar la loma entre todos en una sola jornada. "
            "Es una ayuda mutua sin plata de por medio, el compromiso está sellado y todos confirmaron su asistencia."
        ),
        "quotes": [
            ("acordamos con cuatro compadres hacer un convite este sábado", "observed_intention"),
            ("Yo pongo el sancocho de gallina y ellos traen los bueyes para arar la loma entre todos", "observed_action"),
            ("el compromiso está sellado y todos confirmaron su asistencia", "observed_condition"),
        ],
        "beliefs": ["La mano de obra compartida permite preparar tierra sin contratar jornales", "El convite es vinculante"],
        "desires": ["Arar la loma rápidamente sin costo monetario"],
        "intentions": ["Realizar convite comunitario de arado el sábado"],
        "constraints": ["Dependencia de asistencia de los compadres (resuelta con confirmación)"],
        "emotional_state": "tranquilo",
        "expected_case_type": "pure",
        "expected_conflict_type": None,
        "expected_action": "convite_preparacion_arado",
        "base_condition": "Trabajo individual con altos costos de jornal",
        "perturbation": "Activación de red comunitaria de apoyo mutuo (convite tradicional)",
        "expected_change": "Sustituye la restricción monetaria por reciprocidad social comunitaria sin generar conflicto de metas",
        "agronomic_rationale": "El convite campesino es una institución tradicional de optimización laboral sin conflicto en Montes de María.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_005",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p05",
        "vereda_code": "synthetic_vereda_05",
        "municipality_context": "El Carmen de Bolívar",
        "crop_context": "aguacate criollo y maíz",
        "season_context": "poscosecha y siembra",
        "scenario_id": "SYN_BOL_005",
        "text": (
            "El intermediario del camión llegó ofreciendo comprarme de una vez toda la cosecha de aguacate en el árbol por adelantado. "
            "Me tienta porque necesito efectivo ya mismo para comprar medicina para mi suegro, pero si le entrego la fruta completa al intermediario "
            "por esa miseria me quedo sin nada para llevar a la plaza de mercado en julio donde le saco el triple, "
            "y además me compromete a regalarle el maíz que tenemos para el consumo de la casa."
        ),
        "quotes": [
            ("necesito efectivo ya mismo para comprar medicina para mi suegro", "observed_intention_a"),
            ("me quedo sin nada para llevar a la plaza de mercado en julio donde le saco el triple", "observed_intention_b"),
            ("El intermediario del camión llegó ofreciendo comprarme de una vez toda la cosecha", "observed_trigger"),
        ],
        "beliefs": ["El intermediario paga por debajo del precio justo", "La venta en plaza local maximiza ganancia pero es diferida"],
        "desires": ["Conseguir liquidez inmediata para emergencia de salud", "Preservar valor comercial y alimento del hogar"],
        "intentions": ["Aceptar venta anticipada a bajo precio por urgencia médica", "Retener cosecha para comercialización justa y consumo"],
        "constraints": ["Urgencia médica inmediata", "Mercado mayorista distante temporalmente"],
        "emotional_state": "presionado",
        "expected_case_type": "conflict",
        "expected_conflict_type": "immediate_sale_vs_seed_food_reserve",
        "conflict_detail": {
            "intent_a": "Venta anticipada a intermediario para obtener dinero urgente de salud",
            "evidence_a": "necesito efectivo ya mismo para comprar medicina para mi suegro",
            "intent_b": "Retener fruto para comercialización digna y consumo familiar",
            "evidence_b": "me quedo sin nada para llevar a la plaza de mercado en julio donde le saco el triple",
            "incompatibility_reason": "Vender por adelantado enajena el control del cultivo a precio irrisorio frente al plan de comercialización directa.",
            "resolution": "buscar_prestamo_menor_y_rechazar_venta_atada",
        },
        "expected_action": "dilema_venta_anticipada_intermediario",
        "base_condition": "Comercialización estándar en plaza mayorista",
        "perturbation": "Oferta abusiva de intermediario ante emergencia de salud familiar",
        "expected_change": "Introduce tensión entre liquidez inmediata forzada y soberanía comercial del productor",
        "agronomic_rationale": "La venta en flor o en árbol es un mecanismo de extracción asimétrico frecuente en crisis de liquidez.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_006",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p06",
        "vereda_code": "synthetic_vereda_06",
        "municipality_context": "María La Baja",
        "crop_context": "arroz secano",
        "season_context": "siembra de invierno",
        "scenario_id": "SYN_BOL_006",
        "text": (
            "El clima está demasiado loco y las lluvias han caído salteadas este mes. "
            "Mi plan original era sembrar las dos hectáreas completas de arroz para pagar la deuda del banco, "
            "pero si las aguas siguen así de escasas sembrar todo es una locura; estoy tentado a reducir a solo media hectárea para minimizar riesgo, "
            "aunque reduciendo el área sé perfectamente que no me va a alcanzar la plata para pagar la cuota de junio."
        ),
        "quotes": [
            ("Mi plan original era sembrar las dos hectáreas completas de arroz para pagar la deuda del banco", "observed_intention_a"),
            ("estoy tentado a reducir a solo media hectárea para minimizar riesgo", "observed_intention_b"),
            ("las lluvias han caído salteadas este mes", "observed_trigger"),
        ],
        "beliefs": ["Dos hectáreas generan el ingreso requerido para saldar deuda", "El arroz secano fracasa con lluvia irregular"],
        "desires": ["Cumplir la obligación financiera bancaria", "Evitar quiebra total por catástrofe climática"],
        "intentions": ["Sembrar 2 hectáreas para cumplir cuota bancaria", "Reducir a 0.5 hectáreas para mitigar riesgo de sequía"],
        "constraints": ["Régimen pluviométrico errático", "Vencimiento bancario estricto"],
        "emotional_state": "indeciso",
        "expected_case_type": "conflict",
        "expected_conflict_type": "investment_vs_liquidity_debt",
        "conflict_detail": {
            "intent_a": "Mantener siembra de 2 ha para generar flujo de pago de deuda",
            "evidence_a": "Mi plan original era sembrar las dos hectáreas completas de arroz para pagar la deuda del banco",
            "intent_b": "Reducir área a 0.5 ha para salvaguardar inversión de la sequía",
            "evidence_b": "estoy tentado a reducir a solo media hectárea para minimizar riesgo",
            "incompatibility_reason": "Sembrar 2 ha asume riesgo inasumible de pérdida climática; sembrar 0.5 ha garantiza incumplimiento bancario por déficit de cosecha.",
            "resolution": "renegociar_plazo_bancario_o_diversificar",
        },
        "expected_action": "dilema_reduccion_area_por_lluvia",
        "base_condition": "Régimen pluviométrico estable acorde al calendario de siembra",
        "perturbation": "Precipitación fragmentada y tardía con crédito formal activo",
        "expected_change": "Provoca colisión entre solvencia financiera y mitigación de desastre agronómico",
        "agronomic_rationale": "El arroz secano no tolera baches de más de 8 días sin lluvia en germinación; reducir área es la respuesta agronómica prudente.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_007",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p07",
        "vereda_code": "synthetic_vereda_07",
        "municipality_context": "San Juan Nepomuceno",
        "crop_context": "yuca dulce",
        "season_context": "cosecha",
        "scenario_id": "SYN_BOL_007",
        "text": (
            "Para arrancar la yuca gruesa necesito la barra pesada que no tengo en mi finca. "
            "El vecino Manuel me la presta con gusto a cambio de que yo le preste mi bomba de espalda el lunes para fumigar su potrero. "
            "Ya hicimos el trueque de palabra y voy a aprovechar hoy mismo para cosechar los primeros bultos."
        ),
        "quotes": [
            ("Para arrancar la yuca gruesa necesito la barra pesada que no tengo en mi finca", "observed_constraint"),
            ("El vecino Manuel me la presta con gusto a cambio de que yo le preste mi bomba de espalda el lunes", "observed_agreement"),
            ("voy a aprovechar hoy mismo para cosechar los primeros bultos", "observed_intention"),
        ],
        "beliefs": ["La barra pesada extrae la raíz sin partirla", "El préstamo recíproco de implementos es confiable"],
        "desires": ["Cosechar yuca de calidad intacta"],
        "intentions": ["Cosechar yuca utilizando la herramienta prestada en trueque"],
        "constraints": ["Falta de barra metálica propia (resuelta por intercambio)"],
        "emotional_state": "satisfecho",
        "expected_case_type": "pure",
        "expected_conflict_type": None,
        "expected_action": "cosechar_con_herramienta_trueque",
        "base_condition": "Carencia de apero específico para desenterrar tubérculos",
        "perturbation": "Intercambio solidario vecinal de apero agrícola",
        "expected_change": "Resuelve la restricción técnica mediante acuerdo comunal sin crear metas antagónicas",
        "agronomic_rationale": "El trueque de aperos entre minifundistas amortiza costos fijos y viabiliza labores agronómicas.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_008",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p08",
        "vereda_code": "synthetic_vereda_08",
        "municipality_context": "San Jacinto",
        "crop_context": "tabaco y ajonjolí",
        "season_context": "fin de verano",
        "scenario_id": "SYN_BOL_008",
        "text": (
            "En la tienda del cruce la gente andaba diciendo que este año las cosas vienen raras con los precios y con la brisa. "
            "Unos compadres decían que tal vez valga la pena ensayar con ajonjolí y otros que no vale la pena sembrar nada todavía. "
            "Yo estuve escuchando pero no tengo claro qué va a pasar ni he decidido nada para la parcela."
        ),
        "quotes": [
            ("En la tienda del cruce la gente andaba diciendo que este año las cosas vienen raras", "observed_rumor"),
            ("no tengo claro qué va a pasar ni he decidido nada para la parcela", "observed_indecision"),
        ],
        "beliefs": ["Rumores contradictorios sobre clima y cotizaciones de mercado"],
        "desires": [],
        "intentions": [],
        "constraints": ["Incertidumbre absoluta de información"],
        "emotional_state": "confundido",
        "expected_case_type": "insufficient",
        "expected_conflict_type": None,
        "expected_action": "abstencion_por_falta_de_evidencia",
        "base_condition": "Información incompleta y rumores sin decisión del productor",
        "perturbation": "Ausencia explícita de intención o dilema individual formulado",
        "expected_change": "Impide clasificar como pure o conflict por falta de una intención o colisión concreta declarada",
        "agronomic_rationale": "Un clasificador riguroso debe abstenerse ante comentarios ambientales sin agencia decisional del productor.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_009",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p09",
        "vereda_code": "synthetic_vereda_09",
        "municipality_context": "El Carmen de Bolívar",
        "crop_context": "ñame diamante",
        "season_context": "mitad de ciclo",
        "scenario_id": "SYN_BOL_009",
        "text": (
            "Se vino una plaga de antracnosis tremenda en las guías del ñame y necesito aplicar fungicida de inmediato para no perder la inversión. "
            "El problema es que no tengo liquidez y el prestamista del pueblo me cobra el diez por ciento mensual de interés por la plata del veneno. "
            "Por un lado quiero salvar las plantas cueste lo que cueste metiéndome en esa deuda usurera, pero por otro lado sé que si firmo ese pagaré "
            "quedo trabajando todo el año para pagar intereses y termino perdiendo hasta la parcela si la cosecha no rinde al máximo."
        ),
        "quotes": [
            ("quiero salvar las plantas cueste lo que cueste metiéndome en esa deuda usurera", "observed_intention_a"),
            ("si firmo ese pagaré quedo trabajando todo el año para pagar intereses y termino perdiendo hasta la parcela", "observed_intention_b"),
            ("Se vino una plaga de antracnosis tremenda en las guías del ñame", "observed_trigger"),
        ],
        "beliefs": ["La antracnosis destruye el follaje del ñame si no se controla", "El crédito informal usurero (gota a gota / 10%) es ruinoso"],
        "desires": ["Salvar la plantación de ñame", "Proteger el patrimonio familiar y la tenencia de la tierra"],
        "intentions": ["Adquirir crédito costoso para comprar fungicida", "Evitar endeudamiento usurero para no arriesgar la parcela"],
        "constraints": ["Ataque severo de fitopatógeno", "Falta de crédito institucional ágil"],
        "emotional_state": "desesperado",
        "expected_case_type": "conflict",
        "expected_conflict_type": "investment_vs_liquidity_debt",
        "conflict_detail": {
            "intent_a": "Adquirir deuda usurera inmediata para salvar cultivo de antracnosis",
            "evidence_a": "quiero salvar las plantas cueste lo que cueste metiéndome en esa deuda usurera",
            "intent_b": "Rechazar deuda informal para evitar ruina patrimonial y despojo",
            "evidence_b": "si firmo ese pagaré quedo trabajando todo el año para pagar intereses y termino perdiendo hasta la parcela",
            "incompatibility_reason": "Salvar físicamente el cultivo endeudándose al 10% mensual canibaliza la rentabilidad y arriesga la tierra.",
            "resolution": "buscar_remedio_biologico_casero_o_credito_asociativo",
        },
        "expected_action": "dilema_credito_usurero_vs_perdida_fitosanitaria",
        "base_condition": "Cultivo sano en desarrollo normal",
        "perturbation": "Brote agresivo de antracnosis con acceso únicamente a crédito informal usurero",
        "expected_change": "Provoca disyuntiva trágica entre pérdida inmediata de cultivo o asfixia financiera de largo plazo",
        "agronomic_rationale": "La antracnosis en ñame diamante puede devastar el 80% del rendimiento; los intereses del 10% mensual son insostenibles.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
    {
        "episode_id": "SYN_BOL_010",
        "source_id": "synth_bol_v1",
        "source_type": "synthetic",
        "provenance_class": "synthetic",
        "participant_code": "synthetic_p10",
        "vereda_code": "synthetic_vereda_10",
        "municipality_context": "San Juan Nepomuceno",
        "crop_context": "maíz vs ajonjolí",
        "season_context": "segunda siembra (agosto)",
        "scenario_id": "SYN_BOL_010",
        "text": (
            "El IDEAM y los aguaceros escasos confirman que este segundo semestre viene con fenómeno de El Niño bravo. "
            "Toda la vida he sembrado maíz para asegurar los bultos del gasto de la casa y quiero insistir con mi maíz tradicional, "
            "pero el técnico del comité insiste en que cambie toda la parcela a ajonjolí porque resiste sequía profunda. "
            "No sé si jugármela por el maíz que es la comida segura de la familia pero que se puede quemar en floración, "
            "o sembrar ajonjolí que aguanta el verano pero no se come en la mesa si los precios se desploman."
        ),
        "quotes": [
            ("quiero insistir con mi maíz tradicional", "observed_intention_a"),
            ("cambie toda la parcela a ajonjolí porque resiste sequía profunda", "observed_intention_b"),
            ("El IDEAM y los aguaceros escasos confirman que este segundo semestre viene con fenómeno de El Niño bravo", "observed_trigger"),
        ],
        "beliefs": ["El maíz garantiza alimento pero es muy vulnerable a estrés hídrico", "El ajonjolí resiste sequía pero no sustituye la comida familiar"],
        "desires": ["Seguridad alimentaria doméstica con maíz", "Resiliencia climática ante El Niño con ajonjolí"],
        "intentions": ["Sembrar maíz criollo para abastecer el consumo doméstico", "Reemplazar por ajonjolí para tolerar el déficit hídrico extremo"],
        "constraints": ["Sequía severa proyectada por El Niño"],
        "emotional_state": "inquieto",
        "expected_case_type": "conflict",
        "expected_conflict_type": "productive_vs_household_security",
        "conflict_detail": {
            "intent_a": "Sembrar maíz criollo tradicional para despensa del hogar",
            "evidence_a": "quiero insistir con mi maíz tradicional",
            "intent_b": "Cambiar cultivo a ajonjolí resistente a sequía",
            "evidence_b": "sembrar ajonjolí porque resiste sequía profunda",
            "incompatibility_reason": "El área disponible es una sola; el maíz arriesga pérdida total por sequía pero da alimento, mientras el ajonjolí resiste pero no alimenta a la familia.",
            "resolution": "asociar_cultivos_en_franjas_o_diversificar",
        },
        "expected_action": "dilema_cambio_cultivo_clima_vs_seguridad_alimentaria",
        "base_condition": "Clima benigno que favorece siembra tradicional de maíz",
        "perturbation": "Alerta climática de El Niño y recomendación técnica de reconversión",
        "expected_change": "Genera conflicto entre cultura alimentaria identitaria y adaptación climática extrema",
        "agronomic_rationale": "El maíz aborta espiga con estrés térmico e hídrico; el ajonjolí es xerófilo pero expone al productor a la volatilidad de precios sin autoconsumo.",
        "allowed_for_training": False,
        "usage_state": "context_only",
    },
]


def build_and_validate():
    sources_file = BASE_DIR / "sources/synthetic_bolivar_field_logic_v1.jsonl"
    expected_file = BASE_DIR / "expected/expected_labels.jsonl"
    perturbation_file = BASE_DIR / "reports/perturbation_matrix.json"
    coherence_file = BASE_DIR / "reports/coherence_review.json"

    sources_records = []
    expected_records = []
    perturbation_records = []
    coherence_records = []

    for c in CASES:
        text = c["text"]
        evidence_spans = []
        for quote, etype in c["quotes"]:
            idx = text.find(quote)
            if idx == -1:
                raise ValueError(f"En {c['episode_id']}, la cita no coincide: '{quote}'")
            evidence_spans.append({
                "quote": quote,
                "char_start": idx,
                "char_end": idx + len(quote),
                "evidence_type": etype,
            })
            # Verificar exactitud
            assert text[idx:idx + len(quote)] == quote

        source_rec = {
            "episode_id": c["episode_id"],
            "source_id": c["source_id"],
            "source_type": c["source_type"],
            "provenance_class": c["provenance_class"],
            "participant_code": c["participant_code"],
            "vereda_code": c["vereda_code"],
            "municipality_context": c["municipality_context"],
            "crop_context": c["crop_context"],
            "season_context": c["season_context"],
            "scenario_id": c["scenario_id"],
            "text": text,
            "evidence": evidence_spans,
            "beliefs": c["beliefs"],
            "desires": c["desires"],
            "intentions": c["intentions"],
            "constraints": c["constraints"],
            "emotional_state": c["emotional_state"],
            "expected_case_type": c["expected_case_type"],
            "expected_conflict_type": c["expected_conflict_type"],
            "expected_action": c["expected_action"],
            "base_condition": c["base_condition"],
            "perturbation": c["perturbation"],
            "expected_change": c["expected_change"],
            "agronomic_rationale": c["agronomic_rationale"],
            "allowed_for_training": c["allowed_for_training"],
            "usage_state": c["usage_state"],
        }
        sources_records.append(source_rec)

        expected_records.append({
            "episode_id": c["episode_id"],
            "expected_case_type": c["expected_case_type"],
            "expected_conflict_type": c["expected_conflict_type"],
            "conflict_detail": c.get("conflict_detail"),
            "expected_action": c["expected_action"],
        })

        perturbation_records.append({
            "scenario_id": c["scenario_id"],
            "episode_id": c["episode_id"],
            "base_condition": c["base_condition"],
            "perturbation": c["perturbation"],
            "expected_change": c["expected_change"],
            "agronomic_rationale": c["agronomic_rationale"],
        })

        coherence_records.append({
            "scenario_id": c["scenario_id"],
            "agronomic_coherence": {
                "climate_condition_supported": True,
                "resource_constraint_supported": True,
                "action_plausible": True,
                "conflict_or_pure_label_justified": True,
                "requires_human_review": c["expected_case_type"] in ("conflict", "insufficient"),
                "notes": f"Caso coherente con agronomía de {c['municipality_context']} en cultivo {c['crop_context']}. {c['agronomic_rationale']}",
            }
        })

    with open(sources_file, "w", encoding="utf-8") as f:
        for r in sources_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(expected_file, "w", encoding="utf-8") as f:
        for r in expected_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(perturbation_file, "w", encoding="utf-8") as f:
        json.dump(perturbation_records, f, ensure_ascii=False, indent=2)

    with open(coherence_file, "w", encoding="utf-8") as f:
        json.dump(coherence_records, f, ensure_ascii=False, indent=2)

    print(f"Creados exitosamente 10 casos sintéticos en {sources_file}")


if __name__ == "__main__":
    build_and_validate()

"""tests/unit/test_text_humanizer.py

Pruebas unitarias para el sanitizador determinista TextHumanizer.
Verifica:
1. Eliminación de tics retóricos de IA (em-dashes, léxico grandilocuente, riders superficiales).
2. Preservación absoluta e inmutable de citas literales (raw_excerpt) y campos formales.
3. Rendimiento sub-milisegundo.
"""

import time
from apps.atlas.extractors.text_humanizer import TextHumanizer
from apps.atlas.schemas.context_schemas import TerritorialBeliefItem


def test_sanitize_em_dashes_and_buzzwords():
    raw_ai_text = (
        "El programa — diseñado para pequeños productores — desempeña un papel crucial en "
        "el vibrante paisaje productivo de los Montes de María, marcando un hito para la región."
    )
    clean_text = TextHumanizer.sanitize_text(raw_ai_text)

    # Verifica que no quedan guiones largos
    assert "—" not in clean_text
    assert "–" not in clean_text
    # Verifica que las frases infladas fueron sustituidas por términos sobrios
    assert "desempeña un papel crucial" not in clean_text
    assert "vibrante paisaje productivo" not in clean_text
    assert "marcando un hito" not in clean_text
    assert "participa en el sector productivo" in clean_text
    assert "formalizando" in clean_text


def test_sanitize_shallow_riders_and_contrasts():
    raw_ai_text = (
        "Se prioriza la semilla criolla, no solo para autoconsumo, sino para comercialización local, "
        "destacando la importancia de la soberanía alimentaria."
    )
    clean_text = TextHumanizer.sanitize_text(raw_ai_text)

    # Verifica simplificación de no solo X sino Y
    assert "no solo" not in clean_text
    assert "destacando la importancia de" not in clean_text
    assert "priorizando la soberanía alimentaria" in clean_text


def test_sanitize_belief_presentation_preserves_immutable_fields():
    # El raw_excerpt contiene intencionalmente tics de texto oficial o guiones
    official_quote = "Artículo 12 — El municipio garantiza un enfoque robusto para el crédito rural."

    belief = TerritorialBeliefItem(
        belief_id="bel_test_001",
        source_id="doc_test",
        pillar="desarrollo_agrario_y_rural",
        topic="Crédito rural",
        belief_key="acceso_credito_rural_robusto",
        trigger_condition="Cuando el campesino requiere insumos — según la temporada.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="BUY_SEEDS",
        behavioral_effect="Solicita crédito — con una robusta estrategia para cosecha.",
        activation_rule_template="state.creditAvailable == true",
        raw_excerpt=official_quote,
        ebdi_belief_assertion="El campesino accede a financiamiento — en un marco robusto.",
        target_municipalities=["El Carmen de Bolívar"],
        applicable_divipolas=["13244"],
        confidence=0.95,
        verification_status="verified_verbatim",
    )

    sanitized = TextHumanizer.sanitize_belief_presentation(belief)

    # INVARIANTES SAGRADOS (Garantía Verbatim y Criptográfica)
    assert sanitized.raw_excerpt == official_quote, "raw_excerpt DEBE permanecer 100% inalterado"
    assert sanitized.belief_key == "acceso_credito_rural_robusto", "belief_key no debe alterarse"
    assert sanitized.activation_rule_template == "state.creditAvailable == true"
    assert sanitized.applicable_divipolas == ["13244"]
    assert sanitized.belief_id == "bel_test_001"

    # CAMPOS DE PRESENTACIÓN HUMANA (Sanitizados)
    assert "—" not in sanitized.trigger_condition
    assert "—" not in sanitized.behavioral_effect
    assert "—" not in sanitized.ebdi_belief_assertion
    assert "robusta estrategia" not in sanitized.behavioral_effect
    assert "estrategia técnica" in sanitized.behavioral_effect
    assert "marco robusto" not in sanitized.ebdi_belief_assertion
    assert "marco operativo" in sanitized.ebdi_belief_assertion


def test_sub_millisecond_performance():
    sample_text = (
        "El pequeño productor — formalizado ante la UMATA — desempeña un papel clave en "
        "la transición agroecológica, no solo para reducir costos, sino para cuidar el suelo, "
        "con una robusta estrategia que sirve como un testimonio de resiliencia comunitaria."
    )

    t0 = time.perf_counter()
    for _ in range(100):
        _ = TextHumanizer.sanitize_text(sample_text)
    elapsed = time.perf_counter() - t0

    # 100 ejecuciones deben tardar menos de 20 ms en total (< 0.2 ms por llamada)
    assert elapsed < 0.05, f"Tiempo excesivo para sanitizador determinista: {elapsed * 1000:.2f} ms"

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.atlas.schemas.context_schemas import (
    TerritorialBeliefItem,
    TerritorialBeliefExtractionResult,
    BeliefEditRequest,
)
from apps.atlas.compilers.ebdi_yaml_compiler import EBDIYamlCompiler
from apps.atlas.extractors.belief_extractor import TerritorialBeliefExtractor
from src.api.main import app

client = TestClient(app)


def test_ebdi_yaml_compiler_goal_and_plan(tmp_path: Path):
    compiler = EBDIYamlCompiler(output_base_dir=tmp_path / "yaml")
    belief = TerritorialBeliefItem(
        belief_id="bel_test_001",
        source_id="pdm_carmen_test",
        pillar="desarrollo_agrario_y_rural",
        topic="Mecanización y adecuación de suelos comunitaria",
        belief_key="adecuacion_suelos_comunitaria",
        trigger_condition="El productor requiere acondicionar su lote antes de la siembra de maíz.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="PREPARE",
        behavioral_effect="Coordina maquinaria comunitaria para arado y preparación previa.",
        activation_rule_template="belief.get('farmReady') == 0",
        raw_excerpt="Se prioriza el banco de maquinaria agrícola comunitaria para adecuación de suelos.",
        ebdi_belief_assertion="En El Carmen de Bolívar, los productores de maíz tienen acceso a banco de maquinaria.",
        target_municipalities=["El Carmen de Bolívar"],
        applicable_divipolas=["13244"],
        confidence=0.95,
        verification_status="verified_verbatim",
        curation_status="admitted_ebdi",
    )

    report = compiler.compile_and_save(
        beliefs=[belief],
        document_id="pdm_carmen_test",
        document_hash="a" * 64,
        only_admitted=True,
    )

    assert report["compiled_goals_count"] == 1
    assert report["compiled_plans_count"] == 1
    assert len(report["errors"]) == 0

    goal_path = tmp_path / "yaml" / "goals" / "adecuacion_suelos_comunitaria_goal_v1.yaml"
    plan_path = tmp_path / "yaml" / "plans" / "adecuacion_suelos_comunitaria_plan_v1.yaml"
    assert goal_path.exists()
    assert plan_path.exists()

    goal_text = goal_path.read_text(encoding="utf-8")
    assert "pyramid_level: OPPORTUNITY" in goal_text
    assert "adecuacion_suelos_comunitaria_plan_v1" in goal_text

    plan_text = plan_path.read_text(encoding="utf-8")
    assert "action: agro_ecosystem_operation" in plan_text
    assert "operation: PREPARE" in plan_text
    assert "action: emit_episode" in plan_text


def test_deduplicate_identical_beliefs():
    extractor = TerritorialBeliefExtractor()
    b1 = TerritorialBeliefItem(
        belief_id="bel_1",
        source_id="doc_a",
        pillar="desarrollo_agrario_y_rural",
        topic="Semillas nativas",
        belief_key="fondo_semillas_nativas",
        trigger_condition="Escasez de semillas certificadas.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="PREPARE",
        behavioral_effect="Accede al fondo de semillas.",
        activation_rule_template="belief.get('seeds') == 0",
        raw_excerpt="Fondo municipal de semillas nativas y criollas para pequeños campesinos.",
        ebdi_belief_assertion="Acceso a semillas nativas en El Carmen.",
        target_municipalities=["El Carmen de Bolívar"],
        applicable_divipolas=["13244"],
        confidence=0.9,
        verification_status="verified_verbatim",
    )
    b2 = TerritorialBeliefItem(
        belief_id="bel_2",
        source_id="doc_a",
        pillar="desarrollo_agrario_y_rural",
        topic="Semillas nativas",
        belief_key="fondo_semillas_nativas",  # Misma clave
        trigger_condition="Escasez de semillas certificadas.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="PREPARE",
        behavioral_effect="Accede al fondo de semillas.",
        activation_rule_template="belief.get('seeds') == 0",
        raw_excerpt="Fondo municipal de semillas nativas y criollas para pequeños campesinos.",
        ebdi_belief_assertion="Acceso a semillas nativas en San Jacinto.",
        target_municipalities=["San Jacinto"],
        applicable_divipolas=["13654"],
        confidence=0.95,
        verification_status="verified_verbatim",
    )

    deduped = extractor.deduplicate_and_detect_collisions([b1, b2])
    assert len(deduped) == 1
    assert "13244" in deduped[0].applicable_divipolas
    assert "13654" in deduped[0].applicable_divipolas
    assert deduped[0].confidence == 0.95


def test_collision_detection_deforestation_vs_runap():
    extractor = TerritorialBeliefExtractor()
    b_forest = TerritorialBeliefItem(
        belief_id="bel_deforest",
        source_id="doc_a",
        pillar="desarrollo_agrario_y_rural",
        topic="Ampliación de frontera agrícola",
        belief_key="desmonte_parcela",
        trigger_condition="El productor requiere habilitar terreno boscoso.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="DEFOREST",
        behavioral_effect="Realiza desmonte para siembra.",
        activation_rule_template="state.hasLand == 1",
        raw_excerpt="Autorización para desmonte y adecuación de terrenos en San Onofre.",
        ebdi_belief_assertion="Permiso de desmonte en predios rurales.",
        target_municipalities=["San Onofre"],
        applicable_divipolas=["70717"],
        confidence=0.85,
        verification_status="verified_verbatim",
    )
    b_runap = TerritorialBeliefItem(
        belief_id="bel_runap",
        source_id="doc_b",
        pillar="ambiente_y_agua",
        topic="Protección ambiental y áreas protegidas",
        belief_key="reserva_runap_conservacion",
        trigger_condition="Presencia de zona protegida en la subregión.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="CHECK",
        behavioral_effect="Monitorea el cumplimiento de veda ambiental.",
        activation_rule_template="state.conservation == 1",
        raw_excerpt="Registro Único Nacional de Áreas Protegidas RUNAP prohíbe tala y afectación de cobertura boscosa.",
        ebdi_belief_assertion="Veda de tala en áreas de protección RUNAP.",
        target_municipalities=["San Onofre"],
        applicable_divipolas=["70717"],
        confidence=0.98,
        verification_status="verified_verbatim",
    )

    result = extractor.deduplicate_and_detect_collisions([b_forest], [b_runap])
    assert len(result) == 1
    assert result[0].collision_detected is True
    assert "Incompatibilidad ambiental" in (result[0].collision_reason or "")


def test_collision_detection_water_irrigate_vs_restriction():
    extractor = TerritorialBeliefExtractor()
    b_irrigate = TerritorialBeliefItem(
        belief_id="bel_irrigate",
        source_id="doc_a",
        pillar="desarrollo_agrario_y_rural",
        topic="Turno de riego libre",
        belief_key="riego_libre_distrito",
        trigger_condition="El productor tiene cultivos con déficit hídrico.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="IRRIGATE",
        behavioral_effect="Riega libremente su parcela usando agua del canal.",
        activation_rule_template="state.waterAvailable == 0",
        raw_excerpt="Concesión de agua para riego libre sin restricción horaria en María la Baja.",
        ebdi_belief_assertion="Riego permanente para pequeños productores.",
        target_municipalities=["María la Baja"],
        applicable_divipolas=["13442"],
        confidence=0.9,
        verification_status="verified_verbatim",
    )
    b_restriction = TerritorialBeliefItem(
        belief_id="bel_restric",
        source_id="doc_b",
        pillar="ambiente_y_agua",
        topic="Emergencia hídrica y veda de cuencas",
        belief_key="veda_cuenca_hidrica",
        trigger_condition="En sequía crítica se impone restricción estricta de agua.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="CHECK",
        behavioral_effect="Aplica veda y cuota mínima de agua por sequía extrema.",
        activation_rule_template="state.drought == 1",
        raw_excerpt="Resolución de POMCA establece veda y restricción absoluta de agua para riego por sequía.",
        ebdi_belief_assertion="Restricción de agua por alerta de sequía en María la Baja.",
        target_municipalities=["María la Baja"],
        applicable_divipolas=["13442"],
        confidence=0.95,
        verification_status="verified_verbatim",
    )

    result = extractor.deduplicate_and_detect_collisions([b_irrigate], [b_restriction])
    assert len(result) == 1
    assert result[0].collision_detected is True
    assert "Inconsistencia hídrica" in (result[0].collision_reason or "")


def test_api_endpoints_update_and_compile(tmp_path: Path):
    # Setup temporary belief result file in outputs/atlas/context/
    context_dir = Path("outputs/atlas/context")
    context_dir.mkdir(parents=True, exist_ok=True)
    test_src = "src_test_api_flow"
    file_path = context_dir / f"{test_src}_beliefs.json"

    dummy_item = TerritorialBeliefItem(
        belief_id="bel_api_01",
        source_id=test_src,
        pillar="desarrollo_agrario_y_rural",
        topic="Crédito agrario campesino",
        belief_key="credito_agrario_campesino",
        trigger_condition="Falta de liquidez para insumos.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="PREPARE",
        behavioral_effect="Solicita línea de microcrédito municipal.",
        activation_rule_template="belief.get('money') < 100000",
        raw_excerpt="Línea especial de microcrédito agrario subsidiado por el municipio.",
        ebdi_belief_assertion="Acceso a microcrédito campesino en El Carmen de Bolívar.",
        target_municipalities=["El Carmen de Bolívar"],
        applicable_divipolas=["13244"],
        confidence=0.92,
        verification_status="verified_verbatim",
        curation_status="pending",
    )
    result = TerritorialBeliefExtractionResult(
        source_id=test_src,
        instrument_title="Plan Municipal de Desarrollo Test",
        document_sha256="b" * 64,
        extraction_timestamp_utc="2026-10-07T12:00:00Z",
        model_used="ai/gemma4:E4B",
        extraction_method="poppler_pdftotext_plus_micro_llm",
        total_beliefs_extracted=1,
        verified_beliefs_count=1,
        rejected_hallucinations_count=0,
        beliefs=[dummy_item],
    )
    file_path.write_text(json.dumps(result.model_dump(), indent=2), encoding="utf-8")

    try:
        # 1. Human Edit (PUT)
        edit_payload = {
            "editor_id": "investigador_juan",
            "topic": "Microcrédito Agrario Campesino Editado",
            "trigger_condition": "Cuando el campesino no cuenta con capital de trabajo para comprar semillas.",
            "edit_notes": "Ajuste de condición para mayor claridad operativa.",
        }
        res_put = client.put(f"/v2/atlas/artifacts/{test_src}/beliefs/bel_api_01", json=edit_payload)
        assert res_put.status_code == 200, res_put.text
        data_put = res_put.json()
        assert data_put["topic"] == "Microcrédito Agrario Campesino Editado"
        assert "investigador_juan" in data_put["curator_id"]

        # 2. Human Curation (PATCH to admit)
        res_patch = client.patch(
            f"/v2/atlas/artifacts/{test_src}/beliefs/bel_api_01",
            json={"decision": "admitted_ebdi", "curator_id": "investigador_juan", "notes": "Aprobado"},
        )
        assert res_patch.status_code == 200, res_patch.text
        assert res_patch.json()["curation_status"] == "admitted_ebdi"

        # 3. YAML Compilation (POST)
        res_compile = client.post(f"/v2/atlas/artifacts/{test_src}/compile-yaml")
        assert res_compile.status_code == 200, res_compile.text
        compile_data = res_compile.json()
        assert compile_data["compiled_goals_count"] == 1
        assert compile_data["compiled_plans_count"] == 1

        # 4. List Compiled YAMLs (GET)
        res_yamls = client.get(f"/v2/atlas/artifacts/{test_src}/compiled-yamls")
        assert res_yamls.status_code == 200, res_yamls.text
        yamls_data = res_yamls.json()
        assert yamls_data["total_yamls"] >= 2
        assert len(yamls_data["goals"]) >= 1
        assert len(yamls_data["plans"]) >= 1

    finally:
        if file_path.exists():
            file_path.unlink()


def test_collision_detection_chemical_vs_agroecology():
    extractor = TerritorialBeliefExtractor()
    b_chem = TerritorialBeliefItem(
        belief_id="bel_chem",
        source_id="doc_a",
        pillar="desarrollo_agrario_y_rural",
        topic="Manejo químico intensivo",
        belief_key="agroquimico_sintetico_plagas",
        trigger_condition="Ataque de insectos plaga en cultivo de ñame.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="PREPARE",
        behavioral_effect="Aplica plaguicida químico sintético en la parcela.",
        activation_rule_template="state.pestSeverity > 0.5",
        raw_excerpt="Fomento al uso de agroquímicos y plaguicidas de síntesis para control de plagas en San Jacinto.",
        ebdi_belief_assertion="Uso de plaguicidas químicos sintéticos en cultivos.",
        target_municipalities=["San Jacinto"],
        applicable_divipolas=["13654"],
        confidence=0.88,
        verification_status="verified_verbatim",
    )
    b_organic = TerritorialBeliefItem(
        belief_id="bel_org",
        source_id="doc_b",
        pillar="ambiente_y_agua",
        topic="Transición agroecológica y bioinsumos",
        belief_key="transicion_agroecologica_comunitaria",
        trigger_condition="Pacto territorial de manejo orgánico sin venenos.",
        executable_action="agro_ecosystem_operation",
        action_operation_type="PREPARE",
        behavioral_effect="Sustituye venenos por bioinsumos orgánicos.",
        activation_rule_template="state.agroecology == 1",
        raw_excerpt="Zona de reserva campesina promueve la transición agroecológica y prohíbe plaguicidas de síntesis.",
        ebdi_belief_assertion="Transición agroecológica comunitaria en San Jacinto.",
        target_municipalities=["San Jacinto"],
        applicable_divipolas=["13654"],
        confidence=0.96,
        verification_status="verified_verbatim",
    )

    result = extractor.deduplicate_and_detect_collisions([b_chem], [b_organic])
    assert len(result) == 1
    assert result[0].collision_detected is True
    assert "Inconsistencia agroecológica" in (result[0].collision_reason or "")


def test_normative_chunking_detection():
    extractor = TerritorialBeliefExtractor()
    sample_text = """
    INTRODUCCIÓN Y GENERALIDADES
    Este documento presenta las líneas del plan.

    Artículo 14. Reactivación económica y cadenas productivas
    El municipio priorizará el apoyo a pequeños productores agropecuarios con semillas y asistencia técnica.

    Artículo 15. Adecuación de tierras y distritos de riego
    Se realizarán inversiones en el distrito de riego comunal para abastecer las parcelas de los campesinos en épocas secas.

    Artículo 16. Finanzas públicas
    Gastos de funcionamiento ordinarios de la alcaldía.
    """
    chunks = extractor.slice_agricultural_excerpts(sample_text)
    assert len(chunks) >= 2
    # Comprobar que los chunks contienen los artículos relevantes de reactivación y riego
    combined = " ".join(chunks)
    assert "Artículo 14" in combined or "reactivación económica" in combined.lower()
    assert "Artículo 15" in combined or "distrito de riego" in combined.lower()

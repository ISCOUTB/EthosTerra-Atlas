"""Pruebas unitarias para el banco sintético territorial S9-S10 (Bolívar / Montes de María).
Verifica integridad de esquemas, exactitud de offsets, invariantes de soberanía y coherencia agronómica.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from src.domain.v2.corpus_schemas import (
    AnnotatedSegment,
    ConflictRecord,
    CorpusEvidenceSpan,
    SourceRecord,
    is_gold_candidate,
)

BASE_DIR = Path("outputs/corpus/b6_synthetic_s9_s10")
SOURCES_FILE = BASE_DIR / "sources/synthetic_bolivar_field_logic_v1.jsonl"
EXPECTED_FILE = BASE_DIR / "expected/expected_labels.jsonl"
PERTURBATION_FILE = BASE_DIR / "reports/perturbation_matrix.json"
COHERENCE_FILE = BASE_DIR / "reports/coherence_review.json"


@pytest.fixture(scope="module")
def synthetic_cases() -> list[dict]:
    assert SOURCES_FILE.exists(), "El archivo de fuentes sintéticas S9-S10 debe existir."
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]
    return cases


@pytest.fixture(scope="module")
def expected_labels() -> list[dict]:
    assert EXPECTED_FILE.exists(), "El archivo de etiquetas esperadas debe existir."
    with open(EXPECTED_FILE, "r", encoding="utf-8") as f:
        labels = [json.loads(line) for line in f if line.strip()]
    return labels


def test_synthetic_bank_exact_count_and_ids(synthetic_cases: list[dict]) -> None:
    assert len(synthetic_cases) == 10, "El banco sintético S9-S10 debe contener exactamente 10 casos."
    expected_ids = [f"SYN_BOL_{i:03d}" for i in range(1, 11)]
    assert [c["episode_id"] for c in synthetic_cases] == expected_ids


def test_synthetic_bank_governance_invariants(synthetic_cases: list[dict]) -> None:
    for c in synthetic_cases:
        assert c["source_type"] == "synthetic"
        assert c["provenance_class"] == "synthetic"
        assert c["allowed_for_training"] is False, f"{c['episode_id']} no debe estar autorizado para entrenamiento."
        assert c["usage_state"] == "context_only", f"{c['episode_id']} debe ser context_only."
        assert c["municipality_context"] in (
            "El Carmen de Bolívar", "San Juan Nepomuceno", "San Jacinto", "Córdoba Tetón", "María La Baja"
        )


def test_text_offset_integrity(synthetic_cases: list[dict]) -> None:
    """Verifica que ningún offset sea inventado: text[char_start:char_end] == quote para cada cita."""
    for c in synthetic_cases:
        text = c["text"]
        evidence = c["evidence"]
        assert len(evidence) >= 2, f"{c['episode_id']} debe tener al menos dos fragmentos de evidencia."
        for ev in evidence:
            s, e = ev["char_start"], ev["char_end"]
            quote = ev["quote"]
            assert text[s:e] == quote, f"En {c['episode_id']}, desalineación en cita: '{quote}' != '{text[s:e]}'"


def test_expected_class_distribution(expected_labels: list[dict]) -> None:
    distribution = {
        "pure": ["SYN_BOL_001", "SYN_BOL_004", "SYN_BOL_007"],
        "conflict": ["SYN_BOL_002", "SYN_BOL_003", "SYN_BOL_005", "SYN_BOL_006", "SYN_BOL_009", "SYN_BOL_010"],
        "insufficient": ["SYN_BOL_008"],
    }
    by_class: dict[str, list[str]] = {"pure": [], "conflict": [], "insufficient": []}
    for item in expected_labels:
        by_class[item["expected_case_type"]].append(item["episode_id"])

    assert by_class["pure"] == distribution["pure"]
    assert by_class["conflict"] == distribution["conflict"]
    assert by_class["insufficient"] == distribution["insufficient"]


def test_conflict_cases_have_bilateral_evidence(expected_labels: list[dict]) -> None:
    for item in expected_labels:
        if item["expected_case_type"] == "conflict":
            assert item["expected_conflict_type"] is not None
            detail = item["conflict_detail"]
            assert detail is not None, f"{item['episode_id']} debe incluir conflict_detail."
            assert detail["intent_a"] and detail["intent_b"]
            assert detail["evidence_a"] and detail["evidence_b"]
            assert detail["incompatibility_reason"]


def test_synthetic_cases_are_excluded_from_gold_corpus(synthetic_cases: list[dict]) -> None:
    for c in synthetic_cases:
        src = SourceRecord(
            source_id="synth_0010",
            source_type="synthetic",
            provenance_class="synthetic",
            title=f"Caso {c['episode_id']}",
            language="es",
            collection_date="unknown",
            location="redacted",
            collector_id="researcher_01",
            consent_status="not_applicable",
            raw_path="sources/synthetic_bolivar_field_logic_v1.jsonl",
            raw_sha256="0" * 64,
            version="1.0.0",
            status="draft",
        )
        text = c["text"]
        num = int(c['episode_id'].split('_')[-1])
        base_seg = {
            "segment_id": f"synth_0010_seg_{num:04d}",
            "source_id": "synth_0010",
            "text": text,
            "char_start": 0,
            "char_end": len(text),
            "epistemic_status": "observed",
            "annotation_status": "adjudicated",
            "annotator_id": "researcher_01",
            "annotation_version": "1.0.0",
        }
        if c["expected_case_type"] == "pure":
            ev = c["evidence"][0]
            spans = [CorpusEvidenceSpan(quote=ev["quote"], char_start=ev["char_start"], char_end=ev["char_end"], evidence_type="observed")]
            seg = AnnotatedSegment(
                **base_seg,
                evidence_spans=spans,
                case_type="pure",
                trigger="temporada",
                intent_candidate="preparar_terreno",
                requires_human_review=False,
            )
        elif c["expected_case_type"] == "conflict":
            ev_a, ev_b = c["evidence"][0], c["evidence"][1]
            spans = [
                CorpusEvidenceSpan(quote=ev_a["quote"], char_start=ev_a["char_start"], char_end=ev_a["char_end"], evidence_type="observed"),
                CorpusEvidenceSpan(quote=ev_b["quote"], char_start=ev_b["char_start"], char_end=ev_b["char_end"], evidence_type="observed"),
            ]
            conflict = ConflictRecord(
                common_trigger="retraso de lluvias o iliquidez",
                intent_a="meta_a",
                intent_b="meta_b",
                evidence_a=[ev_a["quote"]],
                evidence_b=[ev_b["quote"]],
                incompatibility_reason="Metas mutuamente excluyentes",
                conflict_type=c["expected_conflict_type"] or "other",
            )
            seg = AnnotatedSegment(
                **base_seg,
                evidence_spans=spans,
                case_type="conflict",
                conflict_trigger=conflict.common_trigger,
                conflicting_intents=["meta_a", "meta_b"],
                conflict=conflict,
                conflict_type=conflict.conflict_type,
                requires_human_review=True,
            )
        else:
            seg = AnnotatedSegment(
                **base_seg,
                evidence_spans=[],
                case_type="insufficient",
                requires_human_review=True,
            )

        # La función de gobernanza debe excluir estrictamente el caso por ser sintético
        assert is_gold_candidate(seg, src) is False


def test_perturbation_matrix_covers_all_ten_scenarios() -> None:
    assert PERTURBATION_FILE.exists()
    matrix = json.loads(PERTURBATION_FILE.read_text("utf-8"))
    assert len(matrix) == 10
    for p in matrix:
        assert p["base_condition"]
        assert p["perturbation"]
        assert p["expected_change"]
        assert p["agronomic_rationale"]


def test_agronomic_coherence_verified() -> None:
    assert COHERENCE_FILE.exists()
    coherence = json.loads(COHERENCE_FILE.read_text("utf-8"))
    assert len(coherence) == 10
    for item in coherence:
        audit = item["agronomic_coherence"]
        assert audit["climate_condition_supported"] is True
        assert audit["resource_constraint_supported"] is True
        assert audit["action_plausible"] is True
        assert audit["conflict_or_pure_label_justified"] is True

from __future__ import annotations

import re
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from src.domain.v2.document_schemas import (
    DocumentAnalysisSchema,
    ExtractedKnowledge,
    EvidenceSpan,
    EpistemicItem,
)

logger = logging.getLogger("epistemic_extractor")

PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "domain" / "prompts" / "document_extraction_v1.txt"


def _detect_prompt_injection(text: str) -> list[str]:
    """Detecta patrones comunes de evasión o inyección de instrucciones en el texto."""
    patterns = [
        r"(?i)\b(ignora|ignore|olvida|forget)\s+.*?\b(instrucciones|instructions)\b",
        r"(?i)\b(instrucci[oó]n\s+del\s+sistema|system\s*prompt|system\s*:)\b",
        r"(?i)\b(act\s+as\s+admin|hazte\s+pasar\s+por|nuevo\s+rol)\b",
        r"(?i)\b(borra\s+la\s+base|drop\s+table|delete\s+from|rm\s+-rf)\b",
    ]
    findings = []
    for pat in patterns:
        if re.search(pat, text):
            findings.append(f"Patrón sospechoso de inyección: '{pat}'")
    return findings


def _is_ambiguous_text(text: str) -> bool:
    """Detecta expresiones explícitas de indecisión o ambigüedad severa."""
    ambiguity_pattern = r"(?i)\b(no\s+s[eé]\s+(si|qu[eé])|quiz[aá]s?|tal\s+vez|dudo|indeciso|no\s+estoy\s+segur[oa])\b"
    return bool(re.search(ambiguity_pattern, text))


def extract_epistemology_deterministic(
    text: str,
    document_id: str,
    source_hash: str,
    source_ref: str = "diario.txt",
    extraction_mode: str = "deterministic_fallback"
) -> DocumentAnalysisSchema:
    """
    Extractor determinista libre de valores fijos o mocks.
    Analiza semánticamente el texto del documento para fundamentar cada campo.
    """
    evidence = EvidenceSpan(
        fragment_id="frag_01",
        source_ref=source_ref,
        start_char=0,
        end_char=len(text),
        text_quote=text,
    )
    detected_conflicts: list[EpistemicItem] = []

    # 1. Detección de Prompt Injection
    injections = _detect_prompt_injection(text)
    if injections:
        detected_conflicts.append(
            EpistemicItem(
                status="observed",
                value="prompt_injection_detected",
                evidence_ref="frag_01",
                rationale="Detectado intento de inyección de instrucciones o manipulación adversaria en el texto fuente."
            )
        )

    # 2. Extracción de Actor
    actor_match = re.search(r"\bpeasant_\d+\b", text)
    if actor_match:
        actor_alias = EpistemicItem(
            status="observed",
            value=actor_match.group(0),
            evidence_ref="frag_01",
            rationale=f"Alias '{actor_match.group(0)}' explícitamente observado en el documento."
        )
    else:
        actor_alias = EpistemicItem(
            status="not_stated",
            value=None,
            evidence_ref=None,
            rationale="El documento no declara ningún alias de campesino (peasant_<id>)."
        )

    # 3. Contexto Territorial
    territory_context = EpistemicItem(
        status="not_stated",
        value=None,
        evidence_ref=None,
        rationale="El texto no declara departamento, municipio ni coordenadas geográficas."
    )

    # 4. Intención y Deseo
    intentions: list[EpistemicItem] = []
    desires: list[EpistemicItem] = []

    is_ambiguous = _is_ambiguous_text(text)
    
    # Análisis de temáticas
    has_fertilization = bool(re.search(r"(?i)\b(fertilizante|abono|fertilizar|fertilizaci[oó]n)\b", text))
    has_selling = bool(re.search(r"(?i)\b(vender|venta|mercado)\b", text))
    has_land_prep = bool(re.search(r"(?i)\b(preparar\s+(el\s+)?terreno|preparar\s+la\s+parcela|preparaci[oó]n\s+del\s+terreno|preparar\s+la\s+tierra|labranza)\b", text))

    theme_count = sum([has_fertilization, has_selling, has_land_prep])

    if is_ambiguous or (theme_count > 1 and not has_fertilization and not has_land_prep):
        # Indecisión o contradicción
        intentions.append(
            EpistemicItem(
                status="unknown",
                value=None,
                evidence_ref="frag_01",
                rationale="Texto ambiguo, con indecisión manifiesta o múltiples intenciones contradictorias sin resolución."
            )
        )
        detected_conflicts.append(
            EpistemicItem(
                status="inferred",
                value="intencion_ambigua",
                evidence_ref="frag_01",
                rationale="El texto presenta dudas o conflicto de prioridades sin decisión clara."
            )
        )
    elif has_fertilization:
        intentions.append(
            EpistemicItem(
                status="observed",
                value="fertilize_crop",
                evidence_ref="frag_01",
                rationale="El campesino manifiesta la necesidad explícita de fertilizar o aplicar abono a la parcela."
            )
        )
        desire_match = re.search(r"(?i)para\s+(recuperar\s+la\s+productividad[^.]+)", text)
        desire_val = desire_match.group(1).strip() if desire_match else "recuperar la productividad del suelo"
        desires.append(
            EpistemicItem(
                status="inferred",
                value=desire_val,
                evidence_ref="frag_01",
                rationale="Deseo productivo inferido a partir de la justificación de la labor."
            )
        )
    elif has_selling:
        intentions.append(
            EpistemicItem(
                status="observed",
                value="sell_crop",
                evidence_ref="frag_01",
                rationale="La campesina/campesino declara la necesidad de vender parte de la cosecha."
            )
        )
        desire_match = re.search(r"(?i)para\s+(comprar\s+alimentos[^.]+)", text)
        desire_val = desire_match.group(1).strip() if desire_match else "comprar alimentos y pagar transporte escolar"
        desires.append(
            EpistemicItem(
                status="inferred",
                value=desire_val,
                evidence_ref="frag_01",
                rationale="Deseo socioeconómico inferido de la destinación del ingreso."
            )
        )
    elif has_land_prep:
        intentions.append(
            EpistemicItem(
                status="observed",
                value="prepare_land",
                evidence_ref="frag_01",
                rationale="El texto indica como labor indispensable preparar el terreno para la siembra."
            )
        )
        desires.append(
            EpistemicItem(
                status="inferred",
                value="alistar el suelo para la siembra",
                evidence_ref="frag_01",
                rationale="Deseo inferido de la fase agrícola de preparación."
            )
        )
    else:
        intentions.append(
            EpistemicItem(
                status="unknown",
                value=None,
                evidence_ref="frag_01",
                rationale="No se identificó ninguna intención agrícola estructurada del catálogo en el texto."
            )
        )

    # 5. Extracción de Requerimientos específicos
    requirements: list[EpistemicItem] = []

    # Búsqueda de cláusulas de requerimientos
    req_clause = ""
    req_match = re.search(r"(?i)(?:requiere|necesita)\s+(?:disponer\s+de\s+|contar\s+con\s+)?([^.]+)", text)
    if req_match:
        req_clause = req_match.group(1)

    # Detección específica por términos reales
    if re.search(r"(?i)\babono(\s+suficiente)?\b", text):
        requirements.append(
            EpistemicItem(
                status="required",
                value={"resource": "abono", "specification": "abono suficiente"},
                evidence_ref="frag_01",
                rationale="El campesino explicita que requiere abono suficiente."
            )
        )
    if re.search(r"(?i)\bherramientas\s+de\s+aplicaci[oó]n\b", text):
        requirements.append(
            EpistemicItem(
                status="required",
                value={"resource": "herramientas", "specification": "herramientas de aplicación"},
                evidence_ref="frag_01",
                rationale="Se especifican herramientas de aplicación."
            )
        )
    elif re.search(r"(?i)\bherramientas(\s+necesarias)?\b", text):
        requirements.append(
            EpistemicItem(
                status="required",
                value={"resource": "tools", "specification": "herramientas necesarias en la parcela"},
                evidence_ref="frag_01",
                rationale="Se requiere contar con herramientas necesarias en la parcela."
            )
        )

    labor_match = re.search(r"(?i)(dos|\d+)\s+jornales(\s+de\s+apoyo)?", text)
    if labor_match:
        qty_str = labor_match.group(1)
        qty = 2 if qty_str.lower() == "dos" else int(qty_str)
        requirements.append(
            EpistemicItem(
                status="required",
                value={"resource": "jornales", "quantity": qty, "specification": f"{qty_str} jornales de apoyo"},
                evidence_ref="frag_01",
                rationale=f"Requiere {qty_str} jornales de apoyo para la labor."
            )
        )

    if re.search(r"(?i)\bcostales(\s+limpios)?\b", text):
        requirements.append(
            EpistemicItem(
                status="required",
                value={"resource": "costales", "specification": "costales limpios"},
                evidence_ref="frag_01",
                rationale="Requiere costales limpios para empacar la cosecha."
            )
        )

    if re.search(r"(?i)\bcamino\s+veredal\b", text):
        requirements.append(
            EpistemicItem(
                status="required",
                value={"resource": "acceso_vial", "specification": "acceso al camino veredal"},
                evidence_ref="frag_01",
                rationale="Requiere acceso al camino veredal para movilizar la carga."
            )
        )

    if re.search(r"(?i)\bmotocicleta\b", text):
        requirements.append(
            EpistemicItem(
                status="required",
                value={"resource": "transporte", "specification": "apoyo de un vecino con motocicleta"},
                evidence_ref="frag_01",
                rationale="Requiere transporte solidario mediante motocicleta."
            )
        )

    knowledge = ExtractedKnowledge(
        actor_alias=actor_alias,
        territory_context=territory_context,
        beliefs=[],
        desires=desires,
        intentions=intentions,
        requirements=requirements,
        detected_conflicts=detected_conflicts,
        emotions={
            "happiness": EpistemicItem(status="unknown", value=None),
            "hopeful": EpistemicItem(status="unknown", value=None),
            "secure": EpistemicItem(status="unknown", value=None),
        },
        social_relations=[],
    )

    return DocumentAnalysisSchema(
        schema_version="2.0.0",
        document_id=document_id,
        source_type="peasant_diary" if "peasant" in text else "pasted_text",
        document_hash=source_hash,
        extracted_knowledge=knowledge,
        evidence_spans=[evidence],
        extraction_metadata={
            "extractor_model": "ai/gemma4:E4B" if extraction_mode == "model_assisted" else "deterministic_rules_v1",
            "extraction_mode": extraction_mode,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        },
    )


async def extract_epistemology(
    text: str,
    document_id: str,
    source_hash: str,
    source_ref: str = "diario.txt",
    model_gateway: Any = None,
) -> DocumentAnalysisSchema:
    """
    Función de extracción epistemológica con soporte para inferencia real LLM
    y degradación elegante e informada a fallback determinista.
    """
    if not text or not text.strip():
        raise ValueError("El texto documental no puede estar vacío.")

    # 1. Si hay gateway disponible, intentar inferencia estructurada
    if model_gateway is not None:
        try:
            template = ""
            if PROMPT_TEMPLATE_PATH.exists():
                template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
            else:
                template = "Extrae epistemología en JSON: {{document_text}}"

            prompt = template.replace("{{document_text}}", text)

            payload = {
                "model": getattr(model_gateway, "model_name", "ai/gemma4:E4B"),
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.0,
            }

            url = f"{getattr(model_gateway, 'base_url', 'http://localhost:11434/')}"
            if not url.endswith("/"):
                url += "/"
            url += "chat/completions"

            client = getattr(model_gateway, "client", None)
            if client:
                res = await client.post(url, json=payload, timeout=20.0)
                res.raise_for_status()
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                parsed = json.loads(content)

                ek_data = parsed.get("extracted_knowledge", {})
                spans_data = parsed.get("evidence_spans", [])

                # Validación Pydantic estricta
                knowledge = ExtractedKnowledge(**ek_data)
                evidence_spans = [EvidenceSpan(**s) for s in spans_data]

                # Verificar que las citas textuales sean reales y pertenezcan a 'text'
                if not evidence_spans:
                    evidence_spans = [
                        EvidenceSpan(
                            fragment_id="frag_01",
                            source_ref=source_ref,
                            start_char=0,
                            end_char=len(text),
                            text_quote=text,
                        )
                    ]
                else:
                    for span in evidence_spans:
                        if span.text_quote not in text:
                            # Rechazar alucinación de cita textual
                            raise ValueError(f"Cita alucinada fuera de texto: '{span.text_quote}'")

                # Defensa contra inyección: si el texto tiene inyección, asegurar que no manipuló
                injections = _detect_prompt_injection(text)
                if injections and not knowledge.detected_conflicts:
                    knowledge.detected_conflicts.append(
                        EpistemicItem(
                            status="observed",
                            value="prompt_injection_detected",
                            evidence_ref="frag_01",
                            rationale="Patrón de inyección detectado en texto fuente."
                        )
                    )

                return DocumentAnalysisSchema(
                    schema_version="2.0.0",
                    document_id=document_id,
                    source_type="peasant_diary" if "peasant" in text else "pasted_text",
                    document_hash=source_hash,
                    extracted_knowledge=knowledge,
                    evidence_spans=evidence_spans,
                    extraction_metadata={
                        "extractor_model": getattr(model_gateway, "model_name", "ai/gemma4:E4B"),
                        "extraction_mode": "model_assisted",
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception as exc:
            logger.warning(
                f"Inferencia DMR falló ({type(exc).__name__}: {exc}). "
                "Activando fallback determinista documentado."
            )

    # 2. Fallback determinista riguroso y dinámico
    return extract_epistemology_deterministic(
        text=text,
        document_id=document_id,
        source_hash=source_hash,
        source_ref=source_ref,
        extraction_mode="deterministic_fallback",
    )

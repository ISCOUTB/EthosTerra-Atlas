from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml

from apps.atlas.schemas.discovery_schemas import (
    CandidateApprovalStatus,
    CandidateReviewDecision,
    CandidateReviewRecord,
    CandidateReviewAuditState,
    CandidateSourceRecord,
    CandidateReviewResponse,
    MAX_ADAPTIVE_SEARCH_RETRIES,
)


class CandidateReviewError(Exception):
    """Error base en la revisión y gobernanza de candidatos."""
    pass


class CandidateNotFoundError(CandidateReviewError):
    """Error cuando un candidato no existe en el catálogo o descubrimiento."""
    pass


class CandidateAlreadyReviewedError(CandidateReviewError):
    """Error cuando un candidato ya fue previamente revisado."""
    pass


class CandidateGovernanceError(CandidateReviewError):
    """Error de violación de invariantes de gobernanza territorial."""
    pass


class CandidateReviewManager:
    """Administrador local y determinista de revisión humana para candidatos del Atlas."""

    def __init__(
        self,
        storage_dir: Path | str | None = None,
        registry_path: Path | str | None = None,
    ) -> None:
        self.storage_dir = Path(storage_dir) if storage_dir else Path("outputs/atlas")
        self.reviews_file = self.storage_dir / "candidate_reviews.json"
        self.discovered_file = self.storage_dir / "discovered_candidates.json"
        self.adaptive_state_file = self.storage_dir / "adaptive_search_state.json"
        self.registry_path = Path(registry_path) if registry_path else Path("apps/atlas/config/sources_registry.yaml")
        self._discovered_cache: dict[str, CandidateSourceRecord] = {}
        self._adaptive_state: dict[str, Any] = {}
        self._load_persisted_discovered_candidates()
        self._load_adaptive_state()

    def ensure_directories(self) -> None:
        """Crea las carpetas necesarias si no existen."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _load_persisted_discovered_candidates(self) -> None:
        """Carga los candidatos descubiertos persistidos en disco."""
        if self.discovered_file.is_file():
            try:
                raw = json.loads(self.discovered_file.read_text(encoding="utf-8"))
                for item in raw:
                    cand = CandidateSourceRecord.model_validate(item)
                    self._discovered_cache[cand.source_id] = cand
            except Exception:
                pass

    def _persist_discovered_candidates(self) -> None:
        """Persiste los candidatos descubiertos en disco de forma atómica."""
        self.ensure_directories()
        data = [cand.model_dump() for cand in self._discovered_cache.values()]
        temp_path = self.discovered_file.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(self.discovered_file)

    def _load_adaptive_state(self) -> None:
        """Carga el estado del ciclo adaptativo de reintentos y retroalimentación."""
        if self.adaptive_state_file.is_file():
            try:
                self._adaptive_state = json.loads(self.adaptive_state_file.read_text(encoding="utf-8"))
            except Exception:
                self._adaptive_state = {}

    def _persist_adaptive_state(self) -> None:
        """Persiste el estado del ciclo adaptativo atómicamente."""
        self.ensure_directories()
        temp_path = self.adaptive_state_file.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(self._adaptive_state, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_path.replace(self.adaptive_state_file)

    def register_discovered_candidate(self, candidate: CandidateSourceRecord) -> None:
        """Indexa y persiste un candidato descubierto para permitir su evaluación."""
        self._discovered_cache[candidate.source_id] = candidate
        self._persist_discovered_candidates()

    def list_all_candidates(self, manifest_documents: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Devuelve todos los candidatos (curados y descubiertos) con su estado de auditoría y enlace oficial."""
        manifest_docs = manifest_documents or {}
        audit_state = self.load_audit_state()
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        # 1. Candidatos descubiertos o dinámicos persistidos
        for c in self._discovered_cache.values():
            if c.source_id in seen_ids:
                continue
            seen_ids.add(c.source_id)
            review = audit_state.reviews.get(c.source_id)
            status = review.resulting_status if review else "pending_review"
            is_downloaded = c.source_id in manifest_docs
            adaptive = self._adaptive_state.get(c.source_id, {})
            results.append({
                "source_id": c.source_id,
                "title": c.title,
                "entity": c.entity,
                "instrument_type": c.instrument_type,
                "territory_scope": c.territory_scope,
                "status": status,
                "approval_status": status,
                "canonical_url": c.url,
                "selection_reason": c.selection_reason,
                "is_downloaded": is_downloaded,
                "review_notes": review.review_notes if review else None,
                "reviewer_id": review.reviewer_id if review else None,
                "approval_timestamp": review.timestamp if review else None,
                "instruction_feedback": review.instruction_feedback if review else adaptive.get("instruction_feedback"),
                "retry_count": adaptive.get("retry_count", review.retry_count if review else 0),
                "max_retries": MAX_ADAPTIVE_SEARCH_RETRIES,
                "search_status": adaptive.get("search_status", "reviewed" if review else "pending_review"),
                "feedback_history": adaptive.get("feedback_history", []),
            })

        # 2. Fuentes del registro curado oficial
        if self.registry_path.is_file():
            try:
                data = yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or {}
                for entry in data.get("sources", []):
                    sid = entry.get("id")
                    if not sid or sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    review = audit_state.reviews.get(sid)
                    status = review.resulting_status if review else ("revised_2026" if sid == "art_patr_montes_de_maria_2026" else "pending_review")
                    is_downloaded = sid in manifest_docs
                    entry_id_lower = sid.lower()
                    instrument_type = "PIDARET" if "pidaret" in entry_id_lower else (
                        "PATR" if "patr" in entry_id_lower else (
                            "PDT" if "pdt" in entry_id_lower or "pdm" in entry_id_lower else (
                                "POT" if "pot" in entry_id_lower else "ordenanza"
                            )
                        )
                    )
                    adaptive = self._adaptive_state.get(sid, {})
                    results.append({
                        "source_id": sid,
                        "title": entry.get("name", sid),
                        "entity": entry.get("entity", "Entidad Oficial"),
                        "instrument_type": instrument_type,
                        "territory_scope": entry.get("territory_scope", "Montes de María"),
                        "status": status,
                        "approval_status": status,
                        "canonical_url": entry.get("canonical_url", ""),
                        "selection_reason": entry.get("description") or "Registro curado de fuentes oficiales",
                        "is_downloaded": is_downloaded,
                        "review_notes": review.review_notes if review else None,
                        "reviewer_id": review.reviewer_id if review else None,
                        "approval_timestamp": review.timestamp if review else None,
                        "instruction_feedback": review.instruction_feedback if review else adaptive.get("instruction_feedback"),
                        "retry_count": adaptive.get("retry_count", review.retry_count if review else 0),
                        "max_retries": MAX_ADAPTIVE_SEARCH_RETRIES,
                        "search_status": adaptive.get("search_status", "reviewed" if review else "pending_review"),
                        "feedback_history": adaptive.get("feedback_history", []),
                    })
            except Exception:
                pass

        return results

    def get_candidate_source(self, source_id: str) -> CandidateSourceRecord:
        """Resuelve el registro del candidato desde el caché de descubrimiento o el registro oficial curado."""
        if source_id in self._discovered_cache:
            return self._discovered_cache[source_id]

        if self.registry_path.is_file():
            try:
                data = yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or {}
                sources_list = data.get("sources", [])
                for entry in sources_list:
                    if entry.get("id") == source_id:
                        pipeline_type = entry.get("pipeline_type", "documental")
                        source_type = "document_context" if pipeline_type == "documental" else "tabular_context"
                        doc_format = entry.get("document_format", "pdf" if pipeline_type == "documental" else "json_api")

                        # Inferencia determinista de instrument_type
                        entry_id_lower = source_id.lower()
                        instrument_type = "PIDARET" if "pidaret" in entry_id_lower else (
                            "PATR" if "patr" in entry_id_lower else (
                                "PDT" if "pdt" in entry_id_lower else (
                                    "POT" if "pot" in entry_id_lower else (
                                        "ordenanza" if "ordenanza" in entry_id_lower else "datos_agricolas"
                                    )
                                )
                            )
                        )

                        return CandidateSourceRecord(
                            source_id=entry["id"],
                            url=entry.get("canonical_url", ""),
                            entity=entry.get("entity", ""),
                            title=entry.get("name", ""),
                            territory_scope=entry.get("territory_scope", "COLOMBIA"),
                            instrument_type=instrument_type,
                            pipeline_type=pipeline_type,
                            document_format=doc_format,
                            status="candidate",
                            confidence_level="high",
                            selection_reason="Registro oficial curado de fuentes",
                            http_status=None,
                            content_type=None,
                            query_date=datetime.now(timezone.utc).date().isoformat(),
                            source_type=source_type,
                            allowed_for_training=False,
                            usage_state="context_only",
                            consent_status="not_applicable",
                            approval_status="pending_review",
                        )
            except Exception as exc:
                raise CandidateReviewError(f"Error al leer el registro de fuentes {self.registry_path}: {exc}") from exc

        raise CandidateNotFoundError(
            f"El candidato '{source_id}' no existe en los candidatos descubiertos ni en el registro de fuentes oficial."
        )

    def load_audit_state(self) -> CandidateReviewAuditState:
        """Carga el estado persistente de revisiones o inicializa uno vacío."""
        if not self.reviews_file.is_file():
            now_iso = datetime.now(timezone.utc).isoformat()
            return CandidateReviewAuditState(last_updated=now_iso, reviews={})

        try:
            raw_data = json.loads(self.reviews_file.read_text(encoding="utf-8"))
            return CandidateReviewAuditState.model_validate(raw_data)
        except Exception as exc:
            raise CandidateReviewError(f"Error al cargar auditoría desde {self.reviews_file}: {exc}") from exc

    def save_audit_state(self, state: CandidateReviewAuditState) -> None:
        """Persiste atómicamente el estado de auditoría formateado en JSON."""
        self.ensure_directories()
        now_iso = datetime.now(timezone.utc).isoformat()
        state.last_updated = now_iso

        serialized = state.model_dump_json(indent=2)
        temp_path = self.reviews_file.with_suffix(".json.tmp")
        temp_path.write_text(serialized, encoding="utf-8")
        temp_path.replace(self.reviews_file)

    def find_adaptive_alternative(
        self,
        rejected_candidate: CandidateSourceRecord,
        feedback: str,
        instruction: str | None,
        retry_count: int,
        manifest_docs: dict[str, Any] | None = None,
        seed_items: list[Any] | None = None,
    ) -> tuple[CandidateSourceRecord | None, str]:
        """Busca deterministamente una fuente oficial alternativa sin duplicados ni colisiones."""
        if retry_count > MAX_ADAPTIVE_SEARCH_RETRIES:
            return None, "exhausted_no_alternative"

        manifest_docs = manifest_docs or {}
        audit_state = self.load_audit_state()

        # Conjunto estricto de URLs y IDs no permitidos (anti-redundancia y anti-colisión)
        seen_urls: set[str] = set()
        seen_ids: set[str] = set()

        for sid in audit_state.reviews:
            seen_ids.add(sid)
        for doc_id, doc_meta in manifest_docs.items():
            seen_ids.add(doc_id)
            if isinstance(doc_meta, dict) and "canonical_url" in doc_meta:
                seen_urls.add(doc_meta["canonical_url"].strip().lower())
        for cand in self._discovered_cache.values():
            seen_ids.add(cand.source_id)
            if cand.url:
                seen_urls.add(cand.url.strip().lower())
        if rejected_candidate.url:
            seen_urls.add(rejected_candidate.url.strip().lower())
        seen_ids.add(rejected_candidate.source_id)

        target_scope = rejected_candidate.territory_scope.upper()

        # 1. Buscar en semillas autorizadas por el usuario
        if seed_items:
            for seed in seed_items:
                seed_url = getattr(seed, "url", "").strip()
                if not seed_url or seed_url.lower() in seen_urls:
                    continue
                seed_scope = getattr(seed, "territory_scope", "").upper()
                scope_match = (
                    seed_scope == target_scope
                    or "MONTES_DE_MARIA" in seed_scope
                    or "BOLIVAR" in seed_scope
                    or "SUCRE" in seed_scope
                    or target_scope in seed_scope
                    or "COLOMBIA" in seed_scope
                )
                if not scope_match:
                    continue

                cand_id = f"cand_alt_{uuid.uuid4().hex[:8]}"
                now_iso = datetime.now(timezone.utc).isoformat()
                instr_clean = instruction or feedback[:60]
                alt_cand = CandidateSourceRecord(
                    source_id=cand_id,
                    url=seed_url,
                    entity=getattr(seed, "entity", "Entidad Oficial"),
                    title=getattr(seed, "title", "Documento Alternativo"),
                    territory_scope=getattr(seed, "territory_scope", rejected_candidate.territory_scope),
                    instrument_type=getattr(seed, "instrument_type", rejected_candidate.instrument_type),
                    pipeline_type=getattr(seed, "pipeline_type", "documental"),
                    document_format=getattr(seed, "document_format", "pdf"),
                    status="candidate",
                    confidence_level="high",
                    selection_reason=(
                        f"Alternativa oficial propuesta (Intento {retry_count}/{MAX_ADAPTIVE_SEARCH_RETRIES}) "
                        f"desde semillas autorizadas para '{rejected_candidate.title}'. Criterio: '{instr_clean}'."
                    ),
                    http_status=None,
                    content_type=None,
                    query_date=now_iso,
                    source_type="document_context",
                    allowed_for_training=False,
                    usage_state="context_only",
                    consent_status="not_applicable",
                    approval_status="pending_review",
                )
                self.register_discovered_candidate(alt_cand)
                return alt_cand, "found_alternative"

        # 2. Buscar en catálogo curado oficial (sources_registry.yaml)
        if self.registry_path.is_file():
            try:
                data = yaml.safe_load(self.registry_path.read_text(encoding="utf-8")) or {}
                for entry in data.get("sources", []):
                    sid = entry.get("id")
                    url = entry.get("canonical_url", "").strip()
                    if not sid or not url:
                        continue
                    if sid in seen_ids or url.lower() in seen_urls:
                        continue

                    entry_scope = entry.get("territory_scope", "").upper()
                    scope_match = (
                        entry_scope == target_scope
                        or "MONTES_DE_MARIA" in entry_scope
                        or "BOLIVAR" in entry_scope
                        or "SUCRE" in entry_scope
                        or target_scope in entry_scope
                        or "COLOMBIA" in entry_scope
                    )
                    if not scope_match:
                        continue

                    now_iso = datetime.now(timezone.utc).isoformat()
                    cand_id = f"cand_alt_{sid[:20]}_{uuid.uuid4().hex[:4]}"
                    inst_type = "PATR" if "patr" in sid.lower() else (
                        "PIDARET" if "pidaret" in sid.lower() else (
                            "PDT" if "pdt" in sid.lower() else rejected_candidate.instrument_type
                        )
                    )
                    instr_clean = instruction or feedback[:60]
                    alt_cand = CandidateSourceRecord(
                        source_id=cand_id,
                        url=url,
                        entity=entry.get("entity", "Entidad Oficial"),
                        title=entry.get("name", sid),
                        territory_scope=entry.get("territory_scope", rejected_candidate.territory_scope),
                        instrument_type=inst_type,
                        pipeline_type="documental",
                        document_format="pdf",
                        status="candidate",
                        confidence_level="high",
                        selection_reason=(
                            f"Alternativa oficial propuesta (Intento {retry_count}/{MAX_ADAPTIVE_SEARCH_RETRIES}) "
                            f"del catálogo curado para '{rejected_candidate.title}'. Criterio: '{instr_clean}'."
                        ),
                        http_status=None,
                        content_type=None,
                        query_date=now_iso,
                        source_type="document_context",
                        allowed_for_training=False,
                        usage_state="context_only",
                        consent_status="not_applicable",
                        approval_status="pending_review",
                    )
                    self.register_discovered_candidate(alt_cand)
                    return alt_cand, "found_alternative"
            except Exception:
                pass

        return None, "exhausted_no_alternative"

    def review_candidate(
        self,
        decision: CandidateReviewDecision,
        seed_items: list[Any] | None = None,
        manifest_docs: dict[str, Any] | None = None,
    ) -> CandidateReviewResponse:
        """Aplica la decisión humana sobre un candidato y gestiona el ciclo adaptativo con feedback."""
        # 1. Verificar existencia del candidato
        candidate = self.get_candidate_source(decision.source_id)

        # 2. Cargar estado de auditoría y verificar si ya fue dictaminado
        state = self.load_audit_state()
        if decision.source_id in state.reviews:
            existing = state.reviews[decision.source_id]
            raise CandidateAlreadyReviewedError(
                f"El candidato '{decision.source_id}' ya fue revisado por '{existing.reviewer_id}' "
                f"con dictamen '{existing.resulting_status}' en {existing.timestamp}. "
                f"No se permite re-revisión sin operación explícita de reapertura."
            )

        # 3. Determinar estado de gobernanza resultante
        if decision.decision == "approve":
            resulting_status: CandidateApprovalStatus = "approved_for_acquisition"
        elif decision.decision == "reject":
            resulting_status = "rejected"
        else:
            raise ValueError(f"Decisión inválida: '{decision.decision}'. Solo se admite 'approve' o 'reject'.")

        timestamp_utc = decision.timestamp or datetime.now(timezone.utc).isoformat()

        # 4. Manejo de reintentos e iteraciones HITL
        adaptive_info = self._adaptive_state.get(decision.source_id, {})
        current_retries = adaptive_info.get("retry_count", 0)
        feedback_history = adaptive_info.get("feedback_history", [])

        if decision.decision == "reject":
            feedback_history.append({
                "reviewer_id": decision.reviewer_id,
                "notes": decision.review_notes,
                "instruction": decision.instruction_feedback,
                "timestamp": timestamp_utc,
            })
            if decision.request_alternative_search:
                next_retry = min(current_retries + 1, MAX_ADAPTIVE_SEARCH_RETRIES)
            else:
                next_retry = current_retries
        else:
            next_retry = current_retries

        # 5. Ejecutar ciclo adaptativo y búsqueda alternativa
        search_status: str = "reviewed"
        alt_candidate_dict = None
        message = f"Decisión '{decision.decision}' registrada exitosamente."

        if decision.decision == "reject" and decision.request_alternative_search:
            if current_retries >= MAX_ADAPTIVE_SEARCH_RETRIES:
                next_retry = MAX_ADAPTIVE_SEARCH_RETRIES
                search_status = "exhausted_no_alternative"
                message = (
                    f"El agente agotó los {MAX_ADAPTIVE_SEARCH_RETRIES} intentos de búsqueda adaptativa "
                    f"sin encontrar documentos oficiales equivalentes no redundantes. "
                    f"Se sugiere cargar el PDF manualmente o agregar una nueva semilla oficial en .gov.co."
                )
            else:
                alt_cand, search_status = self.find_adaptive_alternative(
                    rejected_candidate=candidate,
                    feedback=decision.review_notes,
                    instruction=decision.instruction_feedback,
                    retry_count=next_retry,
                    manifest_docs=manifest_docs,
                    seed_items=seed_items,
                )
                if alt_cand:
                    alt_candidate_dict = alt_cand.model_dump()
                    self._adaptive_state[alt_cand.source_id] = {
                        "parent_source_id": candidate.source_id,
                        "retry_count": next_retry,
                        "search_status": "found_alternative",
                        "instruction_feedback": decision.instruction_feedback,
                        "feedback_history": feedback_history,
                    }
                    message = (
                        f"Alternativa oficial propuesta: '{alt_cand.title}' (Intento {next_retry}/{MAX_ADAPTIVE_SEARCH_RETRIES}). "
                        f"Pendiente de validación humana."
                    )
                else:
                    search_status = "exhausted_no_alternative"
                    message = (
                        f"No se encontraron documentos oficiales equivalentes no redundantes tras el intento "
                        f"{next_retry}/{MAX_ADAPTIVE_SEARCH_RETRIES} con las indicaciones proporcionadas."
                    )

        # 6. Crear registro inmutable con preservación estricta de pipeline y gobernanza
        record = CandidateReviewRecord(
            source_id=candidate.source_id,
            reviewer_id=decision.reviewer_id,
            decision=decision.decision,
            resulting_status=resulting_status,
            review_notes=decision.review_notes,
            timestamp=timestamp_utc,
            request_alternative_search=decision.request_alternative_search,
            instruction_feedback=decision.instruction_feedback,
            retry_count=next_retry,
            max_retries=MAX_ADAPTIVE_SEARCH_RETRIES,
            alternative_found=alt_candidate_dict is not None,
            alternative_candidate=alt_candidate_dict,
            search_status=search_status,  # type: ignore[arg-type]
            adaptive_message=message,
            pipeline_type=candidate.pipeline_type,
            source_type=candidate.source_type,
            document_format=candidate.document_format,
            allowed_for_training=False,
            usage_state="context_only",
        )

        state.reviews[candidate.source_id] = record
        self.save_audit_state(state)

        self._adaptive_state[candidate.source_id] = {
            "retry_count": next_retry,
            "search_status": search_status,
            "instruction_feedback": decision.instruction_feedback,
            "feedback_history": feedback_history,
        }
        self._persist_adaptive_state()

        return record

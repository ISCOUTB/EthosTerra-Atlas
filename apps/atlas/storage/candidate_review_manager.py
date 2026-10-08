from __future__ import annotations

import json
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
        self.registry_path = Path(registry_path) if registry_path else Path("apps/atlas/config/sources_registry.yaml")
        self._discovered_cache: dict[str, CandidateSourceRecord] = {}

    def ensure_directories(self) -> None:
        """Crea las carpetas necesarias si no existen."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def register_discovered_candidate(self, candidate: CandidateSourceRecord) -> None:
        """Indexa un candidato descubierto en memoria para permitir su evaluación inmediata."""
        self._discovered_cache[candidate.source_id] = candidate

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

    def review_candidate(self, decision: CandidateReviewDecision) -> CandidateReviewRecord:
        """Aplica la decisión humana sobre un candidato y persiste la auditoría."""
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

        # 4. Crear registro inmutable con preservación estricta de pipeline y gobernanza
        record = CandidateReviewRecord(
            source_id=candidate.source_id,
            reviewer_id=decision.reviewer_id,
            decision=decision.decision,
            resulting_status=resulting_status,
            review_notes=decision.review_notes,
            timestamp=timestamp_utc,
            pipeline_type=candidate.pipeline_type,
            source_type=candidate.source_type,
            document_format=candidate.document_format,
            allowed_for_training=False,
            usage_state="context_only",
        )

        # 5. Persistir atómicamente en el registro de auditoría
        state.reviews[candidate.source_id] = record
        self.save_audit_state(state)

        return record

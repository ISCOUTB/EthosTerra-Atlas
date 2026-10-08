from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from apps.atlas.schemas.discovery_schemas import (
    AuthorizedSeedCreate,
    AuthorizedSeedItem,
    CandidateSourceRecord,
)
from apps.atlas.storage.candidate_review_manager import CandidateReviewManager


class SeedManager:
    """Administrador soberano de enlaces y semillas oficiales autorizados para rastreo."""

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        self.storage_dir = Path(storage_dir) if storage_dir else Path("outputs/atlas")
        self.seeds_file = self.storage_dir / "authorized_seeds.json"
        self.ensure_default_seeds()

    def ensure_directories(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def ensure_default_seeds(self) -> None:
        """Inicializa semillas por defecto institucionales de Montes de María si el archivo no existe."""
        if not self.seeds_file.is_file():
            self.ensure_directories()
            now_iso = datetime.now(timezone.utc).isoformat()
            default_seeds = [
                AuthorizedSeedItem(
                    seed_id="seed_art_montes_de_maria_patr",
                    url="https://www.renovacionterritorio.gov.co/descargar.php?idFile=22158",
                    entity="Agencia de Renovación del Territorio (ART)",
                    title="PATR Subregión Montes de María",
                    territory_scope="PDET_01_MONTES_DE_MARIA",
                    instrument_type="PATR",
                    pipeline_type="documental",
                    document_format="pdf",
                    added_by="sistema_atlas_soberano",
                    added_at=now_iso,
                    is_active=True,
                ),
                AuthorizedSeedItem(
                    seed_id="seed_art_patr_2026_revision",
                    url="https://www.renovacionterritorio.gov.co/sites/default/files/2026-08/patr-montes-de-maria.pdf",
                    entity="Agencia de Renovación del Territorio (ART)",
                    title="PATR Revisado y Actualizado 2026 (Montes de María)",
                    territory_scope="PDET_01_MONTES_DE_MARIA",
                    instrument_type="PATR",
                    pipeline_type="documental",
                    document_format="pdf",
                    added_by="sistema_atlas_soberano",
                    added_at=now_iso,
                    is_active=True,
                ),
                AuthorizedSeedItem(
                    seed_id="seed_adr_pidaret_bolivar",
                    url="https://www.adr.gov.co/wp-content/uploads/2022/03/PIDARET-DE-BOLIVAR.pdf",
                    entity="Agencia de Desarrollo Rural (ADR)",
                    title="PIDARET Departamento de Bolívar",
                    territory_scope="DEP_13_BOLIVAR",
                    instrument_type="PIDARET",
                    pipeline_type="documental",
                    document_format="pdf",
                    added_by="sistema_atlas_soberano",
                    added_at=now_iso,
                    is_active=True,
                ),
            ]
            self.save_seeds(default_seeds)

    def load_seeds(self) -> list[AuthorizedSeedItem]:
        """Carga las semillas autorizadas registradas en el almacenamiento."""
        if not self.seeds_file.is_file():
            return []
        try:
            raw = json.loads(self.seeds_file.read_text(encoding="utf-8"))
            return [AuthorizedSeedItem.model_validate(item) for item in raw]
        except Exception:
            return []

    def save_seeds(self, seeds: list[AuthorizedSeedItem]) -> None:
        """Persiste las semillas autorizadas de manera atómica."""
        self.ensure_directories()
        serialized = json.dumps([s.model_dump() for s in seeds], indent=2, ensure_ascii=False)
        temp_path = self.seeds_file.with_suffix(".json.tmp")
        temp_path.write_text(serialized, encoding="utf-8")
        temp_path.replace(self.seeds_file)

    def add_seed(self, seed_in: AuthorizedSeedCreate) -> AuthorizedSeedItem:
        """Registra una nueva semilla autorizada por el usuario."""
        seeds = self.load_seeds()
        norm_url = seed_in.url.strip()

        # Evitar duplicados por URL idéntica
        for existing in seeds:
            if existing.url.strip().lower() == norm_url.lower():
                existing.is_active = True
                self.save_seeds(seeds)
                return existing

        now_iso = datetime.now(timezone.utc).isoformat()
        clean_name = urlparse(norm_url).path.split("/")[-1].replace(".pdf", "").replace("-", "_").lower()
        if not clean_name or len(clean_name) < 3:
            clean_name = "semilla"
        seed_id = f"seed_{clean_name[:24]}_{uuid.uuid4().hex[:6]}"

        item = AuthorizedSeedItem(
            seed_id=seed_id,
            url=norm_url,
            entity=seed_in.entity,
            title=seed_in.title,
            territory_scope=seed_in.territory_scope,
            instrument_type=seed_in.instrument_type,
            pipeline_type=seed_in.pipeline_type,
            document_format=seed_in.document_format,
            added_by=seed_in.added_by,
            added_at=now_iso,
            is_active=True,
        )
        seeds.append(item)
        self.save_seeds(seeds)
        return item

    def delete_seed(self, seed_id: str) -> bool:
        """Elimina una semilla autorizada por su ID."""
        seeds = self.load_seeds()
        orig_len = len(seeds)
        seeds = [s for s in seeds if s.seed_id != seed_id]
        if len(seeds) < orig_len:
            self.save_seeds(seeds)
            return True
        return False

    def scan_authorized_seeds(self, review_manager: CandidateReviewManager) -> list[dict]:
        """Rastrea las semillas autorizadas y propone candidatos para validación humana (cero auto-aprobación)."""
        seeds = self.load_seeds()
        discovered_candidates = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for seed in seeds:
            if not seed.is_active:
                continue

            # Inferencia de source_id derivado de la URL o título
            parsed_path = urlparse(seed.url).path
            base_filename = parsed_path.split("/")[-1].replace(".pdf", "").replace("-", "_").lower()
            if not base_filename or len(base_filename) < 3:
                base_filename = seed.seed_id

            candidate_id = f"cand_{base_filename[:36]}"

            # Registro del candidato descubierto con estado estrictamente pending_review
            candidate_record = CandidateSourceRecord(
                source_id=candidate_id,
                url=seed.url,
                entity=seed.entity,
                title=seed.title,
                territory_scope=seed.territory_scope,
                instrument_type=seed.instrument_type,
                pipeline_type=seed.pipeline_type,
                document_format=seed.document_format,
                status="candidate",
                confidence_level="high",
                selection_reason=f"Descubierto mediante semilla autorizada por usuario ({seed.added_by})",
                http_status=None,
                content_type=None,
                query_date=now_iso,
                source_type="document_context" if seed.pipeline_type == "documental" else "tabular_context",
                allowed_for_training=False,
                usage_state="context_only",
                consent_status="not_applicable",
                approval_status="pending_review",
            )

            review_manager.register_discovered_candidate(candidate_record)
            discovered_candidates.append(candidate_record.model_dump())

        return discovered_candidates

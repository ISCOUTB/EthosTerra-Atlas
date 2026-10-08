from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import httpx

from apps.atlas.web.schemas import (
    WebDiscoveryQuery,
    CandidateProvenanceRecord,
)
from apps.atlas.web.security import (
    validate_url_security,
    validate_pdf_magic_bytes,
    SecurityValidationError,
)
from apps.atlas.web.politeness import (
    build_transparent_user_agent,
    RobotsTxtManager,
    HostRateLimiter,
    CircuitBreaker,
    CrawlBudgetTracker,
    RobotsDisallowedError,
    CircuitBreakerOpenError,
)
from apps.atlas.web.adapters import (
    BaseDiscoveryAdapter,
    SocrataCatalogAdapter,
    DcatAdapter,
    SitemapAdapter,
    FeedAdapter,
    NativeSearchAdapter,
    FocusedHtmlCrawler,
    PlaywrightFallbackAdapter,
)
from apps.atlas.storage.manifest_manager import ManifestManager
from apps.atlas.schemas.document_schemas import DocumentMetadataRecord

MAX_DOCUMENT_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
CHUNK_SIZE = 65536  # 64 KB


class AutonomousWebCollectorError(Exception):
    """Error base del recolector web autónomo."""
    pass


class AutonomousWebCollector:
    """Orquestador de la cascada de descubrimiento y adquisición web respetuosa."""

    def __init__(
        self,
        base_dir: Path | str | None = None,
        user_agent: str | None = None,
        client: httpx.Client | None = None,
        adapters: list[BaseDiscoveryAdapter] | None = None,
    ) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path("outputs/atlas")
        self.sources_dir = self.base_dir / "sources"
        self.user_agent = user_agent if user_agent is not None else build_transparent_user_agent()
        self.manifest_manager = ManifestManager(base_dir=self.base_dir)

        self.robots_mgr = RobotsTxtManager(user_agent=self.user_agent)
        self.rate_limiter = HostRateLimiter(base_delay=1.5)
        self.circuit_breaker = CircuitBreaker(max_failures=3, cooldown_seconds=60.0)
        self.budget_tracker = CrawlBudgetTracker()

        self.client = client or httpx.Client(
            headers={"User-Agent": self.user_agent},
            follow_redirects=False,  # Manejo manual de redirecciones para verificar cada salto
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )

        self.adapters = adapters or [
            SocrataCatalogAdapter(),
            DcatAdapter(),
            SitemapAdapter(),
            FeedAdapter(),
            NativeSearchAdapter(),
            FocusedHtmlCrawler(),
            PlaywrightFallbackAdapter(),
        ]

    def ensure_directories(self) -> None:
        self.sources_dir.mkdir(parents=True, exist_ok=True)

    def discover_candidates(self, query: WebDiscoveryQuery) -> list[CandidateProvenanceRecord]:
        """Ejecuta la cascada secuencial de descubrimiento respetando límites y cortesía."""
        all_candidates: list[CandidateProvenanceRecord] = []
        seen_urls: set[str] = set()

        for adapter in self.adapters:
            if not self.budget_tracker.can_request():
                break

            try:
                adapter_candidates = adapter.discover(
                    query=query,
                    client=self.client,
                    robots_mgr=self.robots_mgr,
                    rate_limiter=self.rate_limiter,
                    budget=self.budget_tracker,
                )

                for cand in adapter_candidates:
                    if cand.url not in seen_urls:
                        seen_urls.add(cand.url)
                        # Validar autoridad institucional
                        try:
                            validate_url_security(cand.url, resolve_dns=False)
                            if cand.status == "discovered":
                                cand.status = "authority_verified"
                            all_candidates.append(cand)
                        except SecurityValidationError as exc:
                            self.budget_tracker.record_discard(cand.url, f"security_rejected: {exc}")

                # Si ya se encontraron candidatos suficientes para cumplir la meta de adquisición
                if len(all_candidates) >= query.max_documents_to_acquire:
                    break

            except Exception as exc:
                self.budget_tracker.record_discard(adapter.name, f"adapter_failure: {exc}")

        return all_candidates

    def acquire_document(
        self,
        candidate: CandidateProvenanceRecord,
        expected_sha256: str | None = None,
    ) -> CandidateProvenanceRecord:
        """Adquiere un documento oficial por streaming, validando cabeceras, firma mágica y SHA-256."""
        self.ensure_directories()
        candidate.status = "queued_for_acquisition"

        url = candidate.url
        max_redirects = 5
        redirect_count = 0

        # Resolución segura de redirecciones y streaming
        hasher = hashlib.sha256()
        byte_size = 0
        etag: str | None = None
        last_modified: str | None = None
        final_url = url

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            current_url = url
            while redirect_count < max_redirects:
                # Validar seguridad y allowlist en cada salto
                validate_url_security(current_url, resolve_dns=True)
                host = urlparse(current_url).netloc

                # Validar circuit breaker y robots.txt
                self.circuit_breaker.check_host(host)
                if not self.robots_mgr.can_fetch(current_url, client=self.client):
                    raise RobotsDisallowedError(f"Rastreo prohibido por robots.txt para {current_url}")

                self.rate_limiter.wait_for_turn(host)

                # Petición GET streaming
                with self.client.stream("GET", current_url, headers={"User-Agent": self.user_agent}) as resp:
                    if resp.status_code in (301, 302, 303, 307, 308):
                        redirect_count += 1
                        loc = resp.headers.get("location")
                        if not loc:
                            raise AutonomousWebCollectorError("Redirección HTTP sin cabecera Location.")
                        from urllib.parse import urljoin
                        current_url = urljoin(current_url, loc)
                        continue

                    if resp.status_code >= 400:
                        self.circuit_breaker.record_failure(host)
                        raise AutonomousWebCollectorError(f"Servidor respondió con HTTP {resp.status_code} para {current_url}")

                    self.circuit_breaker.record_success(host)
                    final_url = str(resp.url)
                    candidate.http_status = resp.status_code
                    candidate.content_type = resp.headers.get("content-type", "")
                    etag = resp.headers.get("etag")
                    last_modified = resp.headers.get("last-modified")

                    content_type_lower = candidate.content_type.lower()
                    if "text/html" in content_type_lower:
                        raise AutonomousWebCollectorError(f"Respuesta no documental (HTML detectado: {candidate.content_type})")

                    first_chunk = True
                    with open(tmp_path, "wb") as f_out:
                        for chunk in resp.iter_bytes(chunk_size=CHUNK_SIZE):
                            if not chunk:
                                continue

                            # Validar firma mágica en el primer bloque (%PDF-)
                            if first_chunk:
                                if not validate_pdf_magic_bytes(chunk):
                                    raise AutonomousWebCollectorError(
                                        "Firma mágica inválida: El archivo no inicia con %PDF-."
                                    )
                                first_chunk = False

                            byte_size += len(chunk)
                            if byte_size > MAX_DOCUMENT_SIZE_BYTES:
                                raise AutonomousWebCollectorError(
                                    f"Tamaño excede el límite de 100 MB ({byte_size} bytes)."
                                )

                            hasher.update(chunk)
                            f_out.write(chunk)

                    break  # Stream finalizado con éxito

            actual_sha256 = hasher.hexdigest()

            # Validación de hash esperado si se suministró
            if expected_sha256 and actual_sha256 != expected_sha256:
                raise AutonomousWebCollectorError(
                    f"Discrepancia de SHA-256: esperado {expected_sha256}, real {actual_sha256}."
                )

            # Transición a acquired_unreviewed y luego a integrity_verified
            candidate.status = "acquired_unreviewed"
            candidate.sha256 = actual_sha256
            candidate.byte_size = byte_size
            candidate.final_url = final_url
            candidate.etag = etag
            candidate.last_modified = last_modified

            # Mover atómicamente a cuarentena direccionada por SHA-256
            target_rel_path = f"sources/{actual_sha256}.pdf"
            target_abs_path = self.base_dir / target_rel_path
            shutil.move(str(tmp_path), str(target_abs_path))

            candidate.status = "integrity_verified"
            candidate.content_path = target_rel_path

            now_iso = datetime.now(timezone.utc).isoformat()
            candidate.timestamp_utc = now_iso

            # Priorización de versión vigente (2026 - Resolución 000841 de 2026) vs versión histórica (2019)
            is_2026_version = any(
                k in candidate.title.lower() or k in final_url.lower()
                for k in ("2026", "000841", "actualizado", "revision", "resolucion_000841")
            )
            if candidate.instrument_type == "PATR" and not is_2026_version:
                candidate.is_superseded = True
                candidate.status = "pending_context_review"
                notes_text = (
                    f"Descubierto mediante {candidate.discovery_adapter}. "
                    "Versión histórica (2018-2019). "
                    "Registrado como superseded_candidate en estado pending_context_review a la espera de revisión contextual."
                )
            else:
                candidate.is_superseded = False
                candidate.status = "pending_context_review"
                notes_text = f"Descubierto mediante {candidate.discovery_adapter}. Espera revisión contextual."

            # Actualizar manifiesto
            doc_record = DocumentMetadataRecord(
                source_id=candidate.source_id,
                entity=candidate.entity,
                title=candidate.title,
                level="departamental" if "DEP_" in candidate.territory_scope else "subregional_pdet",
                territory_scope=candidate.territory_scope,
                pipeline_type="documental",
                document_format="pdf",
                canonical_url=final_url,
                download_date=now_iso,
                sha256=actual_sha256,
                byte_size=byte_size,
                content_path=target_rel_path,
                source_type="document_context",
                provenance_class="official_government",
                consent_status="not_applicable",
                allowed_for_training=False,
                usage_state="context_only",
                approval_status="pending_context_review",
                status="pending_context_review",
                instrument_type=candidate.instrument_type,
                approval_notes=notes_text,
            )

            manifest = self.manifest_manager.load_manifest()
            self.manifest_manager.register_document(manifest, doc_record, verify_content=True)
            self.manifest_manager.save_manifest(manifest)

            return candidate

        except Exception as exc:
            if tmp_path.exists():
                tmp_path.unlink()
            candidate.status = "rejected"
            candidate.discard_reason = str(exc)
            raise

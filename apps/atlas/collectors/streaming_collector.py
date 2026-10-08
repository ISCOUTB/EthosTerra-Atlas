from __future__ import annotations

import hashlib
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import httpx

from apps.atlas.collectors.policy_verifier import PolicyVerifier, PolicyVerificationError
from apps.atlas.schemas.document_schemas import (
    DocumentMetadataRecord,
    VerificationPolicyResult,
)
from apps.atlas.storage.manifest_manager import ManifestManager

DEFAULT_USER_AGENT = "AtlasTerritorial-Collector/1.0 (Universidad; Investigacion Posgrado Montes de Maria)"
CHUNK_SIZE = 65536  # 64 KB
MAX_DOCUMENT_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


class StreamingCollectorError(Exception):
    """Error durante la descarga o recolección por streaming."""
    pass


class StreamingSizeExceededError(StreamingCollectorError):
    """Error cuando el tamaño del documento excede el límite permitido de 100 MB."""
    pass


class StreamingDocumentCollector:
    """Recolector documental por streaming con hashing en vuelo y verificación de políticas."""

    def __init__(
        self,
        verifier: PolicyVerifier,
        manifest_manager: ManifestManager,
        client: httpx.Client | None = None,
    ) -> None:
        self.verifier = verifier
        self.manifest_manager = manifest_manager
        self.client = client or httpx.Client(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            follow_redirects=True,
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0),
        )

    def collect_source_from_stream(
        self,
        source_id: str,
        stream_reader: BinaryIO,
        download_date_iso: str | None = None,
        expected_sha256: str | None = None,
    ) -> tuple[DocumentMetadataRecord, VerificationPolicyResult]:
        """Procesa y almacena un flujo binario (útil para pruebas offline y pipelines desacoplados)."""
        if source_id not in self.verifier.registered_sources:
            raise PolicyVerificationError(f"Fuente no registrada: {source_id}")

        source_info = self.verifier.registered_sources[source_id]
        self.manifest_manager.ensure_directories()

        # Escribir en archivo temporal calculando SHA-256
        hasher = hashlib.sha256()
        byte_size = 0

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            with open(tmp_path, "wb") as f_out:
                while chunk := stream_reader.read(CHUNK_SIZE):
                    byte_size += len(chunk)
                    if byte_size > MAX_DOCUMENT_SIZE_BYTES:
                        raise StreamingSizeExceededError(
                            f"El documento excede el límite máximo de 100 MB ({byte_size} bytes leídos)."
                        )
                    hasher.update(chunk)
                    f_out.write(chunk)

            actual_sha256 = hasher.hexdigest()

            # Validación de hash esperado si está definido
            effective_expected_hash = expected_sha256 or getattr(source_info, "sha256", None)
            if effective_expected_hash and actual_sha256 != effective_expected_hash:
                raise StreamingCollectorError(
                    f"Discrepancia criptográfica de SHA-256 para {source_id}: "
                    f"esperado {effective_expected_hash}, obtenido {actual_sha256}"
                )

            ext = source_info.document_format
            if ext == "json_api":
                ext = "json"

            target_rel_path = f"sources/{actual_sha256}.{ext}"
            target_abs_path = self.manifest_manager.base_dir / target_rel_path

            # Mover archivo a destino direccionado por contenido atómicamente
            shutil.move(str(tmp_path), str(target_abs_path))
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        now_iso = download_date_iso or datetime.now(timezone.utc).isoformat()

        record = DocumentMetadataRecord(
            source_id=source_id,
            entity=source_info.entity,
            title=source_info.name,
            level=source_info.level,
            territory_scope=source_info.territory_scope,
            pipeline_type=source_info.pipeline_type,
            document_format=source_info.document_format,
            canonical_url=source_info.canonical_url,
            download_date=now_iso,
            sha256=actual_sha256,
            byte_size=byte_size,
            content_path=target_rel_path,
            source_type="document_context",
            provenance_class="official_government",
            consent_status="not_applicable",
            allowed_for_training=False,
            usage_state="context_only",
            approval_status="pending_review",
            approval_notes="",
            approval_timestamp=None,
            reviewer_id=None,
        )

        policy_result = self.verifier.verify_document_policy(record, expected_sha256=expected_sha256)

        # Actualizar manifiesto
        manifest = self.manifest_manager.load_manifest()
        self.manifest_manager.register_document(manifest, record, verify_content=True)
        self.manifest_manager.save_manifest(manifest)

        return record, policy_result

    def collect_source(
        self,
        source_id: str,
        custom_url: str | None = None,
        expected_sha256: str | None = None,
    ) -> tuple[DocumentMetadataRecord, VerificationPolicyResult]:
        """Descarga por streaming desde la URL oficial, calculando SHA-256 en vuelo."""
        if source_id not in self.verifier.registered_sources:
            raise PolicyVerificationError(f"Fuente no registrada: {source_id}")

        source_info = self.verifier.registered_sources[source_id]
        url = custom_url or source_info.canonical_url

        try:
            with self.client.stream("GET", url) as response:
                if response.status_code >= 400:
                    raise StreamingCollectorError(
                        f"El servidor oficial respondió con código de error {response.status_code} para {url}"
                    )

                ct = response.headers.get("content-type", "").lower()
                if source_info.pipeline_type == "documental" and "application/pdf" not in ct:
                    raise StreamingCollectorError(
                        f"Content-Type inválido '{ct}' para fuente documental {source_id}. Se requiere 'application/pdf'."
                    )

                cl_header = response.headers.get("content-length")
                if cl_header and cl_header.isdigit() and int(cl_header) > MAX_DOCUMENT_SIZE_BYTES:
                    raise StreamingSizeExceededError(
                        f"Content-Length reportado ({cl_header} bytes) excede el límite de 100 MB."
                    )

                # Delegar streaming a través del iterador de bytes de respuesta
                class ResponseStreamAdapter:
                    def __init__(self, resp):
                        self.iterator = resp.iter_bytes(chunk_size=CHUNK_SIZE)

                    def read(self, _size=-1):
                        try:
                            return next(self.iterator)
                        except StopIteration:
                            return b""

                adapter = ResponseStreamAdapter(response)
                return self.collect_source_from_stream(
                    source_id=source_id,
                    stream_reader=adapter,
                    expected_sha256=expected_sha256,
                )
        except (StreamingSizeExceededError, StreamingCollectorError, PolicyVerificationError):
            raise
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise StreamingCollectorError(f"Error de red al conectar con {url}: {exc}") from exc
        except Exception as exc:
            raise StreamingCollectorError(f"Fallo en recolección por streaming de {source_id} desde {url}: {exc}") from exc

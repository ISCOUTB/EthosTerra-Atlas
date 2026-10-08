from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from apps.atlas.schemas.document_schemas import (
    AtlasManifestState,
    DocumentMetadataRecord,
)
from apps.atlas.storage.hashing import compute_file_sha256


class ManifestManagerError(Exception):
    """Error base en la gestión del manifiesto del Atlas."""
    pass


class ManifestIntegrityError(ManifestManagerError):
    """Error lanzado cuando un archivo en almacenamiento no coincide con su hash registrado."""
    pass


class ManifestManager:
    """Administrador local del manifiesto y almacenamiento direccionado por contenido."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path("outputs/atlas")
        self.sources_dir = self.base_dir / "sources"
        self.manifest_path = self.base_dir / "registry_state.json"

    def ensure_directories(self) -> None:
        """Crea las carpetas necesarias si no existen."""
        self.sources_dir.mkdir(parents=True, exist_ok=True)

    def load_manifest(self) -> AtlasManifestState:
        """Carga el estado del manifiesto desde disco o retorna uno nuevo vacío."""
        if not self.manifest_path.is_file():
            now_iso = datetime.now(timezone.utc).isoformat()
            return AtlasManifestState(last_updated=now_iso, documents={})

        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return AtlasManifestState.model_validate(data)
        except Exception as e:
            raise ManifestManagerError(f"Error al cargar manifiesto desde {self.manifest_path}: {e}") from e

    def save_manifest(self, manifest: AtlasManifestState) -> None:
        """Persiste el estado del manifiesto serializado en JSON formateado."""
        self.ensure_directories()
        now_iso = datetime.now(timezone.utc).isoformat()
        manifest.last_updated = now_iso

        serialized = manifest.model_dump_json(indent=2)
        temp_path = self.manifest_path.with_suffix(".json.tmp")
        temp_path.write_text(serialized, encoding="utf-8")
        temp_path.replace(self.manifest_path)

    def register_document(
        self,
        manifest: AtlasManifestState,
        record: DocumentMetadataRecord,
        verify_content: bool = True,
    ) -> AtlasManifestState:
        """Registra o actualiza un documento en el manifiesto verificando invariantes."""
        if verify_content:
            target_file = self.base_dir / record.content_path
            if not target_file.is_file():
                raise FileNotFoundError(f"El archivo físico no existe en la ruta declarada: {target_file}")
            actual_hash = compute_file_sha256(target_file)
            if actual_hash != record.sha256:
                raise ManifestIntegrityError(
                    f"Discrepancia de integridad para {record.source_id}: "
                    f"registrado {record.sha256}, real {actual_hash}"
                )

        manifest.documents[record.source_id] = record
        return manifest

    def approve_document(
        self,
        manifest: AtlasManifestState,
        source_id: str,
        reviewer_id: str,
        notes: str = "",
    ) -> AtlasManifestState:
        """Puerta de aprobación humana: valida y promueve un documento para su uso en contexto eBDI."""
        if source_id not in manifest.documents:
            raise ManifestManagerError(f"Documento {source_id} no encontrado en el manifiesto.")

        doc = manifest.documents[source_id]
        now_iso = datetime.now(timezone.utc).isoformat()

        # Validar integridad del archivo antes de aprobar
        target_file = self.base_dir / doc.content_path
        if not target_file.is_file():
            raise FileNotFoundError(f"Archivo físico ausente al intentar aprobar: {target_file}")

        current_hash = compute_file_sha256(target_file)
        if current_hash != doc.sha256:
            raise ManifestIntegrityError(
                f"Bloqueo de seguridad: El archivo fue alterado antes de la aprobación humana. "
                f"Esperado: {doc.sha256}, Actual: {current_hash}"
            )

        updated_dict = doc.model_dump()
        updated_dict["approval_status"] = "approved"
        updated_dict["approval_notes"] = notes
        updated_dict["approval_timestamp"] = now_iso
        updated_dict["reviewer_id"] = reviewer_id

        manifest.documents[source_id] = DocumentMetadataRecord.model_validate(updated_dict)
        return manifest

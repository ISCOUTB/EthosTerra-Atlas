from __future__ import annotations

from pathlib import Path
import yaml

from apps.atlas.schemas.document_schemas import (
    DocumentMetadataRecord,
    SourceRegistryEntry,
    VerificationPolicyResult,
)


class PolicyVerificationError(Exception):
    """Error en la verificación de políticas territoriales e institucionales."""
    pass


class PolicyVerifier:
    """Validador estricto de políticas, fuentes oficiales y soberanía de datos."""

    def __init__(self, registry_path: Path | str | None = None) -> None:
        if registry_path:
            self.registry_path = Path(registry_path)
        else:
            self.registry_path = Path("apps/atlas/config/sources_registry.yaml")
        self._registry: dict[str, SourceRegistryEntry] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Carga y valida el archivo YAML curado contra los esquemas Pydantic V2."""
        if not self.registry_path.is_file():
            raise FileNotFoundError(f"Registro de fuentes no encontrado en: {self.registry_path}")

        raw_yaml = yaml.safe_load(self.registry_path.read_text(encoding="utf-8"))
        if not isinstance(raw_yaml, dict) or "sources" not in raw_yaml:
            raise PolicyVerificationError(f"Estructura inválida en registro de fuentes: {self.registry_path}")

        for entry_raw in raw_yaml.get("sources", []):
            entry = SourceRegistryEntry.model_validate(entry_raw)
            self._registry[entry.id] = entry

    @property
    def registered_sources(self) -> dict[str, SourceRegistryEntry]:
        """Diccionario de fuentes oficiales registradas indexadas por su ID."""
        return self._registry

    def verify_document_policy(
        self,
        record: DocumentMetadataRecord,
        expected_sha256: str | None = None,
    ) -> VerificationPolicyResult:
        """Verifica deterministamente que un documento cumpla con todas las reglas de gobernanza."""
        violations: list[str] = []

        # 1. Verificación de fuente oficial registrada
        is_official = record.source_id in self._registry
        if not is_official:
            violations.append(f"La fuente '{record.source_id}' no está registrada en el catálogo oficial curado.")

        # 2. Verificación criptográfica de SHA-256
        sha256_verified = True
        if expected_sha256 is not None and record.sha256.lower() != expected_sha256.lower():
            sha256_verified = False
            violations.append(
                f"Discrepancia en SHA-256: calculado '{record.sha256}', esperado '{expected_sha256}'."
            )

        # 3. Verificación de Invariantes de Gobernanza
        governance_verified = True
        if record.source_type != "document_context":
            governance_verified = False
            violations.append(
                f"Violación de gobernanza: source_type debe ser estrictamente 'document_context', encontrado '{record.source_type}'."
            )

        if record.allowed_for_training is not False:
            governance_verified = False
            violations.append("Violación crítica: allowed_for_training DEBE ser False para documentos de política.")

        if record.usage_state != "context_only":
            governance_verified = False
            violations.append(
                f"Violación de gobernanza: usage_state debe ser estrictamente 'context_only', encontrado '{record.usage_state}'."
            )

        if record.consent_status != "not_applicable":
            governance_verified = False
            violations.append(
                f"Violación de gobernanza: consent_status debe ser 'not_applicable' para documentos públicos, encontrado '{record.consent_status}'."
            )

        # 4. Verificación de coherencia territorial si está registrada
        territory_matches = True
        if is_official:
            reg_entry = self._registry[record.source_id]
            if record.territory_scope != reg_entry.territory_scope:
                territory_matches = False
                violations.append(
                    f"Discrepancia de ámbito territorial: registro '{reg_entry.territory_scope}', documento '{record.territory_scope}'."
                )

        is_valid = is_official and sha256_verified and governance_verified and territory_matches and len(violations) == 0

        return VerificationPolicyResult(
            source_id=record.source_id,
            is_official=is_official,
            sha256_verified=sha256_verified,
            governance_verified=governance_verified,
            territory_matches=territory_matches,
            is_valid=is_valid,
            violations=violations,
        )

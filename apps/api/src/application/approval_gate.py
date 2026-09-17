from __future__ import annotations

from src.domain.v2.operational_schemas import OperationalDocumentSchema
from src.application.canonical_hasher import compute_canonical_hash


class YAMLGenerationBlocked(Exception):
    """Excepción lanzada cuando una condición de control o seguridad bloquea la generación."""
    pass


def assert_yaml_generation_allowed(document: OperationalDocumentSchema) -> None:
    current_hash = compute_canonical_hash(document)

    # 1. Estado Principal
    if document.status != "Aprobado":
        raise YAMLGenerationBlocked(
            f"El documento se encuentra en estado '{document.status}'. Solo documentos con estado 'Aprobado' pueden generar YAML."
        )

    # 2. Revisión Humana
    if document.review_status == "rejected":
        raise YAMLGenerationBlocked("La revisión humana fue rechazada por el investigador.")

    if document.review_status == "pending":
        raise YAMLGenerationBlocked("El documento tiene una revisión humana pendiente.")

    if document.review_status != "approved":
        raise YAMLGenerationBlocked(
            f"Estado de revisión inválido: '{document.review_status}'. Se requiere 'approved'."
        )

    # 3. Metadatos de aprobación
    if document.approval_metadata is None:
        raise YAMLGenerationBlocked("Faltan metadatos de aprobación humana.")

    # 4. Integridad Criptográfica del Hash
    if document.approval_metadata.approved_json_hash != current_hash:
        raise YAMLGenerationBlocked(
            f"Violación de integridad: El JSON fue modificado tras la aprobación. "
            f"Hash firmado: {document.approval_metadata.approved_json_hash}, Hash actual: {current_hash}."
        )

    # 5. Errores bloqueantes
    if document.validation_status.has_blocking_errors:
        raise YAMLGenerationBlocked(
            f"El documento tiene errores bloqueantes: {document.validation_status.blocking_errors}"
        )

    # 6. Trazabilidad de fuentes y evidencias
    if not document.source_refs:
        raise YAMLGenerationBlocked("Falta trazabilidad: se requiere al menos una referencia de fuente (source_refs).")

    if not document.evidence_spans:
        raise YAMLGenerationBlocked("Falta trazabilidad: se requiere al menos una evidencia textual (evidence_spans).")

    # 7. Resolución de Caso Conflictivo
    if document.tipo_caso == "conflicto" and not document.selected_alternative:
        raise YAMLGenerationBlocked("No se ha seleccionado una alternativa para el Caso Conflictivo.")

    # 8. Compatibilidad de Artefactos con EthosTerra
    for artifact in document.artifacts:
        if artifact.support_status == "not_supported":
            raise YAMLGenerationBlocked(
                f"El artefacto '{artifact.artifact_id}' está catalogado como 'not_supported'."
            )
        if artifact.requires_simulator_extension:
            raise YAMLGenerationBlocked(
                f"El artefacto '{artifact.artifact_id}' requiere extensión previa del simulador."
            )

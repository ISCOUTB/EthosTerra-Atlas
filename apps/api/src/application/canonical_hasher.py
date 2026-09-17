from __future__ import annotations

import hashlib
import json
from typing import Any
from src.domain.v2.operational_schemas import OperationalDocumentSchema


CANONICAL_HASH_FIELDS = (
    "experiment_id",
    "document_id",
    "schema_version",
    "tipo_caso",
    "source_refs",
    "evidence_spans",
    "extracted_knowledge",
    "artifacts",
    "alternatives",
    "selected_alternative",
    "validation_status",
)


def extract_canonical_payload(doc: OperationalDocumentSchema) -> dict[str, Any]:
    """Extrae estrictamente los 11 campos obligatorios para el hash canónico."""
    raw = doc.model_dump(mode="json")
    canonical = {field: raw.get(field) for field in CANONICAL_HASH_FIELDS}
    return canonical


def serialize_canonical_payload(payload: dict[str, Any]) -> str:
    """Serializa el payload en una representación JSON normalizada y determinista."""
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":")
    )


def compute_canonical_hash(doc: OperationalDocumentSchema) -> str:
    """Calcula el hash criptográfico SHA-256 sobre el payload canónico serializado."""
    payload = extract_canonical_payload(doc)
    canonical_str = serialize_canonical_payload(payload)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

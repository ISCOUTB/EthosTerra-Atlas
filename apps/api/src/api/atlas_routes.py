from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import base64
import hashlib
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
import yaml

from apps.atlas.geo.territory_resolver import TerritoryResolver, MONTES_DE_MARIA_MUNICIPALITIES
from apps.atlas.schemas.territory_schemas import TerritoryHierarchy
from apps.atlas.agents.discovery_agent import DocumentDiscoveryAgent, DiscoveryAgentError
from apps.atlas.schemas.discovery_schemas import (
    DiscoveryQuery,
    DiscoveryResult,
    CandidateReviewDecision,
    CandidateReviewRecord,
    CandidateReviewResponse,
    AcquisitionRequest,
    AcquisitionResult,
    AuthorizedSeedCreate,
    AuthorizedSeedItem,
)
from apps.atlas.storage.candidate_review_manager import (
    CandidateReviewManager,
    CandidateNotFoundError,
    CandidateAlreadyReviewedError,
    CandidateGovernanceError,
)
from apps.atlas.schemas.document_schemas import (
    DocumentMetadataRecord,
    ReviewEventRecord,
    SourceRegistryEntry,
)
from apps.atlas.storage.manifest_manager import ManifestManager
from apps.atlas.storage.seed_manager import SeedManager
from apps.atlas.collectors.policy_verifier import PolicyVerifier, PolicyVerificationError
from apps.atlas.collectors.streaming_collector import (
    StreamingDocumentCollector,
    StreamingCollectorError,
    StreamingSizeExceededError,
)
from apps.atlas.storage.hashing import compute_file_sha256
from apps.atlas.schemas.context_schemas import (
    TerritorialBeliefItem,
    TerritorialBeliefExtractionResult,
    PilotAggregatedBeliefs,
    BeliefCurationRequest,
    BeliefEditRequest,
)
from apps.atlas.collectors.ocr_processor import (
    LocalOCRProcessor,
    OCRError,
)
from apps.atlas.extractors.belief_extractor import (
    TerritorialBeliefExtractor,
    BeliefExtractionError,
    ArtifactNotApprovedError,
)
from apps.atlas.compilers.ebdi_yaml_compiler import EBDIYamlCompiler, CompilationError

atlas_router = APIRouter(prefix="/v2/atlas", tags=["Atlas de Política Territorial (AT-1)"])
resolver = TerritoryResolver()
discovery_agent = DocumentDiscoveryAgent(resolver=resolver)
review_manager = CandidateReviewManager()
seed_manager = SeedManager()
manifest_manager = ManifestManager()
policy_verifier = PolicyVerifier()
streaming_collector = StreamingDocumentCollector(verifier=policy_verifier, manifest_manager=manifest_manager)
ocr_processor = LocalOCRProcessor()
belief_extractor = TerritorialBeliefExtractor(
    manifest_manager=manifest_manager,
    resolver=resolver,
)
yaml_compiler = EBDIYamlCompiler()

GEOJSON_PATH = Path("apps/atlas/geo/dane_mgn_montes_de_maria.geojson")
REGISTRY_PATH = Path("apps/atlas/config/sources_registry.yaml")


@atlas_router.get("/territories", summary="Listar territorios de Montes de María")
def list_territories():
    pilots = set(resolver.list_montes_de_maria_pilots())
    results = []
    for code, item in MONTES_DE_MARIA_MUNICIPALITIES.items():
        results.append({
            "divipola": code,
            "name": item["name"],
            "department_code": item["department_code"],
            "department_name": item["department_name"],
            "is_pilot": code in pilots,
            "is_pdet": item.get("is_pdet", False),
            "pdet_subregion": item.get("pdet_name"),
        })
    return {"territories": results, "pilots_count": len(pilots)}


@atlas_router.get("/territories/{divipola}", response_model=TerritoryHierarchy, summary="Resolver jerarquía territorial e instrumentos")
def resolve_territory(divipola: str):
    try:
        return resolver.resolve_by_divipola(divipola)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@atlas_router.get("/geojson", summary="Obtener polígonos DANE MGN para renderizado en mapa")
def get_dane_geojson():
    if not GEOJSON_PATH.exists():
        raise HTTPException(status_code=500, detail="Archivo GeoJSON DANE no encontrado en el servidor.")
    return json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))


@atlas_router.get("/sources", summary="Consultar registro de fuentes oficiales")
def get_sources_registry():
    if not REGISTRY_PATH.exists():
        raise HTTPException(status_code=500, detail="Registro de fuentes YAML no encontrado.")
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


@atlas_router.post(
    "/discover",
    response_model=DiscoveryResult,
    summary="Descubrir fuentes oficiales de política y datos para un territorio",
)
def discover_sources(query: DiscoveryQuery) -> DiscoveryResult:
    """Descubre de forma determinista y offline las fuentes oficiales aplicables a un territorio."""
    try:
        hierarchy = resolver.resolve_by_divipola(query.divipola)

        # Validación estricta de coherencia territorial
        dep_clean_query = query.department.strip().lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
        dep_clean_real = hierarchy.department_name.strip().lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
        if dep_clean_query != dep_clean_real:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Incompatibilidad territorial: El código DIVIPOLA '{query.divipola}' corresponde a "
                    f"'{hierarchy.department_name}', no a '{query.department}'."
                ),
            )

        return discovery_agent.discover_sources(query)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DiscoveryAgentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@atlas_router.post(
    "/candidates/review",
    response_model=CandidateReviewResponse,
    summary="Registrar decisión humana (aprobación para adquisición o rechazo con retroalimentación) de un candidato",
)
def review_candidate(decision: CandidateReviewDecision) -> CandidateReviewResponse:
    """Registra y audita la decisión de un investigador sobre un candidato descubierto con soporte adaptativo."""
    try:
        seeds = seed_manager.load_seeds()
        manifest = manifest_manager.load_manifest()
        return review_manager.review_candidate(
            decision,
            seed_items=seeds,
            manifest_docs=manifest.documents,
        )
    except CandidateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except CandidateAlreadyReviewedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (CandidateGovernanceError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@atlas_router.post(
    "/acquire",
    response_model=AcquisitionResult,
    summary="Adquirir bajo demanda un documento previamente aprobado para adquisición",
)
def acquire_document(request: AcquisitionRequest) -> AcquisitionResult:
    """Descarga por streaming un candidato aprobado y registra su metadato en el manifiesto."""
    # 1. Verificar existencia del candidato
    try:
        candidate = review_manager.get_candidate_source(request.source_id)
    except CandidateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # 2. Verificar estado de revisión humana
    audit_state = review_manager.load_audit_state()
    if request.source_id not in audit_state.reviews:
        raise HTTPException(
            status_code=409,
            detail=(
                f"El candidato '{request.source_id}' se encuentra en estado 'pending_review'. "
                f"Solo se permite la adquisición de candidatos con estado 'approved_for_acquisition'."
            ),
        )

    review_record = audit_state.reviews[request.source_id]
    if review_record.resulting_status != "approved_for_acquisition":
        raise HTTPException(
            status_code=409,
            detail=(
                f"El candidato '{request.source_id}' tiene estado '{review_record.resulting_status}'. "
                f"Solo se permite la adquisición de candidatos con estado 'approved_for_acquisition'."
            ),
        )

    # 3. Validar compatibilidad de pipeline
    if candidate.pipeline_type != "documental":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tipo de pipeline incompatible: '{candidate.pipeline_type}'. "
                f"El endpoint de adquisición documental solo admite fuentes con pipeline 'documental'."
            ),
        )

    # 4. Verificar idempotencia e integridad local
    manifest = manifest_manager.load_manifest()
    if request.source_id in manifest.documents:
        existing_doc = manifest.documents[request.source_id]
        target_file = manifest_manager.base_dir / existing_doc.content_path
        if not target_file.is_file():
            raise HTTPException(
                status_code=409,
                detail=(
                    f"El documento '{request.source_id}' está registrado en el manifiesto pero su archivo "
                    f"físico no existe en disco. No se permite re-descarga automática."
                ),
            )
        current_hash = compute_file_sha256(target_file)
        if current_hash != existing_doc.sha256:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"El archivo local para '{request.source_id}' existe pero su hash está alterado "
                    f"({current_hash} != {existing_doc.sha256}). No se permite re-descarga automática."
                ),
            )

        return AcquisitionResult(
            source_id=existing_doc.source_id,
            requester_id=request.requester_id,
            status="already_present",
            download_timestamp=existing_doc.download_date,
            canonical_url=existing_doc.canonical_url,
            sha256=existing_doc.sha256,
            byte_size=existing_doc.byte_size,
            content_path=existing_doc.content_path,
            content_type="application/pdf",
            pipeline_type="documental",
            source_type="document_context",
            document_format="pdf",
            allowed_for_training=False,
            usage_state="context_only",
            approval_status="pending_review",
        )

    # 5. Adquirir documento mediante StreamingDocumentCollector
    if candidate.source_id not in policy_verifier.registered_sources:
        policy_verifier._registry[candidate.source_id] = SourceRegistryEntry(
            id=candidate.source_id,
            entity=candidate.entity,
            name=candidate.title,
            level="municipal" if candidate.instrument_type in ["PDM", "PDT"] else ("subregional_pdet" if candidate.instrument_type == "PATR" else "departamental"),
            territory_scope=candidate.territory_scope,
            pipeline_type=candidate.pipeline_type,
            document_format=candidate.document_format,
            adoption_norm="Norma Oficial Registrada",
            validity_start_year=2024,
            status="vigente",
            canonical_url=candidate.url,
            access_type="descarga_directa",
            rate_limit="10_req_per_minute",
            license="Gobierno de Colombia - Acceso Público y Consulta",
        )

    try:
        record, _ = streaming_collector.collect_source(
            source_id=request.source_id,
        )
        return AcquisitionResult(
            source_id=record.source_id,
            requester_id=request.requester_id,
            status="acquired_new",
            download_timestamp=record.download_date,
            canonical_url=record.canonical_url,
            sha256=record.sha256,
            byte_size=record.byte_size,
            content_path=record.content_path,
            content_type="application/pdf",
            pipeline_type="documental",
            source_type="document_context",
            document_format="pdf",
            allowed_for_training=False,
            usage_state="context_only",
            approval_status="pending_review",
        )
    except StreamingSizeExceededError as exc:
        raise HTTPException(status_code=413, detail=str(exc))
    except (StreamingCollectorError, PolicyVerificationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))


class ContextReviewDecision(BaseModel):
    """Contrato Pydantic V2 estricto para la revisión contextual humana de artefactos en cuarentena."""
    model_config = ConfigDict(extra="forbid", strict=True)

    source_id: str = Field(..., min_length=3, max_length=120)
    reviewer_id: str = Field(..., min_length=3, max_length=64)
    decision: Literal["approved_for_context", "rejected", "pending_context_review"]
    review_notes: str = Field(..., min_length=3, max_length=2000)


@atlas_router.get(
    "/artifacts/quarantine",
    summary="Listar artefactos documentales en cuarentena y candidatos registrados",
)
def get_quarantine_artifacts():
    """Expone los artefactos descargados en cuarentena y los candidatos registrados para revisión contextual humana."""
    manifest = manifest_manager.load_manifest()
    docs = list(manifest.documents.values())

    all_cands = review_manager.list_all_candidates(manifest.documents)
    unacquired_candidates = [c for c in all_cands if not c.get("is_downloaded")]

    return {
        "documents": [d.model_dump() for d in docs],
        "registered_candidates": unacquired_candidates,
        "count": len(docs),
    }


class DirectUploadRequest(BaseModel):
    """Contrato estricto para carga manual de documentos PDF vía Base64/JSON."""
    model_config = ConfigDict(extra="forbid", strict=True)

    filename: str = Field(..., min_length=3, max_length=120)
    file_base64: str = Field(..., min_length=10)
    source_id: str | None = Field(default=None, max_length=100)
    title: str | None = Field(default=None, max_length=200)
    entity: str = Field(default="Entidad Territorial / Carga Manual", max_length=120)
    territory_scope: str = Field(default="Montes de María", max_length=100)
    instrument_type: str = Field(default="PDM", max_length=50)
    reviewer_id: str = Field(default="investigador_ebdi_01", max_length=64)


@atlas_router.post(
    "/artifacts/upload",
    response_model=DocumentMetadataRecord,
    summary="Cargar manualmente un documento PDF al almacenamiento soberano de cuarentena",
)
def upload_artifact(payload: DirectUploadRequest):
    """Permite al investigador subir directamente un documento PDF en Base64 al almacenamiento de cuarentena."""
    filename = payload.filename
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos en formato PDF (.pdf).")

    # Limpiar prefijo data URI si viene de FileReader.readAsDataURL
    raw_b64 = payload.file_base64
    if "," in raw_b64:
        raw_b64 = raw_b64.split(",", 1)[1]

    try:
        content = base64.b64decode(raw_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Contenido Base64 inválido: {exc}")

    if len(content) < 4 or not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="El archivo proporcionado no es un PDF válido (falta firma binaria '%PDF-').",
        )

    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo excede el límite máximo de 100 MB.")

    sha256 = hashlib.sha256(content).hexdigest()

    if not payload.source_id:
        clean_name = filename.replace(".pdf", "").replace("-", "_").replace(" ", "_").lower()
        clean_name = re.sub(r"[^a-z0-9_]", "", clean_name)
        effective_source_id = f"manual_{clean_name[:32]}"
    else:
        effective_source_id = re.sub(r"[^a-zA-Z0-9_-]", "_", payload.source_id.strip()).lower()

    manifest_manager.ensure_directories()
    dest_path = manifest_manager.sources_dir / f"{sha256}.pdf"
    dest_path.write_bytes(content)

    now_iso = datetime.now(timezone.utc).isoformat()
    rev_event = ReviewEventRecord(
        event_id=f"rev_{uuid.uuid4().hex[:12]}",
        timestamp_utc=now_iso,
        reviewer_id=payload.reviewer_id,
        reviewer_auth_mode="declarado_sin_autenticacion",
        decision="approved_for_context",
        review_notes="Documento PDF cargado y aprobado manualmente por el investigador.",
        previous_status=None,
        event_type="human_decision",
        is_valid_human_approval=True,
    )

    doc_record = DocumentMetadataRecord(
        source_id=effective_source_id,
        entity=payload.entity,
        title=payload.title or filename.replace(".pdf", "").replace("_", " ").title(),
        level="municipal",
        territory_scope=payload.territory_scope,
        pipeline_type="documental",
        document_format="pdf",
        canonical_url=f"local_upload://{filename}",
        download_date=now_iso,
        sha256=sha256,
        byte_size=len(content),
        content_path=f"sources/{sha256}.pdf",
        source_type="document_context",
        provenance_class="official_government",
        consent_status="not_applicable",
        allowed_for_training=False,
        usage_state="context_only",
        approval_status="approved_for_context",
        status="approved_for_context",
        instrument_type=payload.instrument_type,
        approval_notes="Cargado directamente por el investigador local desde archivo físico.",
        approval_timestamp=now_iso,
        reviewer_id=payload.reviewer_id,
        reviewer_auth_mode="declarado_sin_autenticacion",
        review_events=[rev_event],
    )

    manifest = manifest_manager.load_manifest()
    manifest.documents[effective_source_id] = doc_record
    manifest_manager.save_manifest(manifest)

    # Habilitar en validador de políticas para extracción
    policy_verifier._registry[effective_source_id] = SourceRegistryEntry(
        id=effective_source_id,
        entity=payload.entity,
        name=doc_record.title,
        level="municipal",
        territory_scope=payload.territory_scope,
        pipeline_type="documental",
        document_format="pdf",
        adoption_norm="Carga Manual Soberana",
        validity_start_year=2024,
        status="vigente",
        canonical_url=doc_record.canonical_url,
        access_type="descarga_directa",
        rate_limit="local_unlimited",
        license="Gobierno de Colombia - Acceso Público y Consulta",
    )

    return doc_record


@atlas_router.get(
    "/candidates",
    summary="Listar todos los candidatos oficiales y descubiertos con estado de revisión humana",
)
def list_candidates():
    """Devuelve la lista unificada de candidatos oficiales e institucionales con enlaces de inspección."""
    manifest = manifest_manager.load_manifest()
    cands = review_manager.list_all_candidates(manifest.documents)
    return {
        "candidates": cands,
        "count": len(cands),
    }


@atlas_router.get(
    "/seeds",
    summary="Listar enlaces y repositorios semilla autorizados para rastreo",
)
def list_seeds():
    """Devuelve las semillas autorizadas por el usuario."""
    seeds = seed_manager.load_seeds()
    return {
        "seeds": [s.model_dump() for s in seeds],
        "count": len(seeds),
    }


@atlas_router.post(
    "/seeds",
    response_model=AuthorizedSeedItem,
    summary="Registrar un enlace o repositorio semilla autorizado para rastreo",
)
def add_seed(seed_in: AuthorizedSeedCreate):
    """Registra una nueva semilla autorizada para búsqueda."""
    return seed_manager.add_seed(seed_in)


@atlas_router.delete(
    "/seeds/{seed_id}",
    summary="Eliminar una semilla autorizada",
)
def delete_seed(seed_id: str):
    """Elimina una semilla por ID."""
    deleted = seed_manager.delete_seed(seed_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Semilla '{seed_id}' no encontrada.")
    return {"status": "deleted", "seed_id": seed_id}


@atlas_router.post(
    "/seeds/scan",
    summary="Escanear semillas autorizadas proponiendo candidatos para validación humana",
)
def scan_seeds():
    """Rastrea las semillas activas y registra candidatos en pending_review para validación humana."""
    discovered = seed_manager.scan_authorized_seeds(review_manager)
    return {
        "status": "completed",
        "discovered_candidates": discovered,
        "count": len(discovered),
    }


@atlas_router.post(
    "/artifacts/context-review",
    response_model=DocumentMetadataRecord,
    summary="Registrar decisión humana contextual sobre artefacto en cuarentena",
)
def review_context_artifact(decision: ContextReviewDecision) -> DocumentMetadataRecord:
    """Registra la decisión humana (approved_for_context, rejected, pending_context_review) sin alterar campos inmutables."""
    if decision.source_id == "art_patr_montes_de_maria_2026":
        raise HTTPException(
            status_code=400,
            detail=(
                "La Opción A (art_patr_montes_de_maria_2026) se encuentra registrada únicamente como candidato "
                "no descargado y no puede ser promovida a approved_for_context sin adquisición previa autorizada."
            ),
        )

    manifest = manifest_manager.load_manifest()
    if decision.source_id not in manifest.documents:
        raise HTTPException(
            status_code=404,
            detail=f"Documento con source_id '{decision.source_id}' no encontrado en el manifiesto de cuarentena.",
        )

    doc = manifest.documents[decision.source_id]

    # Invariantes no alterables (verificación estricta)
    orig_sha256 = doc.sha256
    orig_content_path = doc.content_path
    orig_canonical_url = doc.canonical_url
    orig_download_date = doc.download_date
    orig_provenance_class = doc.provenance_class
    orig_source_type = doc.source_type
    orig_allowed_for_training = doc.allowed_for_training
    orig_usage_state = doc.usage_state

    # Generar evento append-only y capturar estado previo
    now_iso = datetime.now(timezone.utc).isoformat()
    event_id = f"rev_{uuid.uuid4().hex[:12]}"
    previous_status = doc.status or doc.approval_status

    review_event = ReviewEventRecord(
        event_id=event_id,
        timestamp_utc=now_iso,
        reviewer_id=decision.reviewer_id,
        reviewer_auth_mode="declarado_sin_autenticacion",
        decision=decision.decision,
        review_notes=decision.review_notes,
        previous_status=previous_status,
        event_type="human_decision",
        is_valid_human_approval=True,
    )

    doc_dict = doc.model_dump()
    doc_dict["status"] = decision.decision
    doc_dict["approval_status"] = decision.decision
    doc_dict["reviewer_id"] = decision.reviewer_id
    doc_dict["reviewer_auth_mode"] = "declarado_sin_autenticacion"
    doc_dict["approval_timestamp"] = now_iso

    # Append-only estricto a la lista de eventos históricos (nunca sobrescribir review_events)
    events_list = list(doc.review_events) if doc.review_events else []
    events_list.append(review_event)
    doc_dict["review_events"] = [e.model_dump() for e in events_list]

    # approval_notes contiene únicamente la nota vigente o resumen actual (no el historial acumulado)
    doc_dict["approval_notes"] = decision.review_notes.strip()

    # Revalidar preservación estricta de campos inmutables
    assert doc_dict["sha256"] == orig_sha256
    assert doc_dict["content_path"] == orig_content_path
    assert doc_dict["canonical_url"] == orig_canonical_url
    assert doc_dict["download_date"] == orig_download_date
    assert doc_dict["provenance_class"] == orig_provenance_class
    assert doc_dict["source_type"] == orig_source_type
    assert doc_dict["allowed_for_training"] == orig_allowed_for_training
    assert doc_dict["usage_state"] == orig_usage_state

    updated_record = DocumentMetadataRecord.model_validate(doc_dict)
    manifest.documents[decision.source_id] = updated_record
    manifest_manager.save_manifest(manifest)

    return updated_record


@atlas_router.get(
    "/artifacts/{source_id}/content",
    summary="Servir contenido binario local de un artefacto en cuarentena",
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Archivo PDF servido de forma soberana"},
        400: {"description": "Petición inválida o riesgo de Directory Traversal"},
        404: {"description": "Artefacto no encontrado en el manifiesto o archivo físico ausente"},
        409: {"description": "Discrepancia de integridad criptográfica SHA-256"},
    },
)
def get_artifact_content(source_id: str):
    """Sirve de forma local y soberana el archivo PDF almacenado en outputs/atlas/sources/."""
    # 1. Protección contra Directory Traversal
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido (prohibido traversal).")

    # 2. Cargar manifiesto y verificar existencia
    manifest = manifest_manager.load_manifest()
    if source_id not in manifest.documents:
        raise HTTPException(
            status_code=404,
            detail=f"Artefacto '{source_id}' no registrado en el manifiesto local.",
        )

    doc = manifest.documents[source_id]

    # 3. Validar ruta física canónica
    file_path = (manifest_manager.base_dir / doc.content_path).resolve()
    base_sources_dir = (manifest_manager.base_dir / "sources").resolve()

    if not str(file_path).startswith(str(base_sources_dir)):
        raise HTTPException(status_code=400, detail="Violación de confinamiento de almacenamiento.")

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"El archivo físico no existe en almacenamiento local para '{source_id}'.",
        )

    # 4. Verificación de integridad criptográfica
    actual_hash = compute_file_sha256(file_path)
    if actual_hash != doc.sha256:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Bloqueo de seguridad: El archivo local ha sido alterado. "
                f"Esperado {doc.sha256}, actual {actual_hash}."
            ),
        )

    # 5. Servir archivo con cabeceras defensivas para inspección en navegador
    filename = f"{doc.source_id}.pdf"
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="inline",
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Artifact-SHA256": doc.sha256,
            "X-Artifact-Source-ID": doc.source_id,
            "X-Artifact-Status": doc.status or doc.approval_status or "pending_context_review",
        },
    )


@atlas_router.get(
    "/pilots/cascades",
    summary="Listar jerarquía e instrumentos de los 5 municipios piloto de Montes de María",
)
def get_pilots_cascades():
    """Devuelve la resolución territorial y cascada de políticas de los 5 casos piloto."""
    pilot_codes = resolver.list_montes_de_maria_pilots()
    pilots_data = []
    manifest = manifest_manager.load_manifest()

    for code in pilot_codes:
        hierarchy = resolver.resolve_by_divipola(code)
        # Identificar documentos disponibles en cuarentena para este ámbito
        available_docs = [
            d.source_id
            for d in manifest.documents.values()
            if d.territory_scope in (hierarchy.municipality_name, hierarchy.pdet_subregion_name, f"DEP_{hierarchy.department_code}_{hierarchy.department_name.upper()}", "nacional")
            or (d.level == "departamental" and d.territory_scope == f"DEP_{hierarchy.department_code}_{hierarchy.department_name.upper()}")
            or (d.level == "subregional_pdet" and hierarchy.is_pdet)
        ]
        pilots_data.append({
            "divipola": code,
            "municipality_name": hierarchy.municipality_name,
            "department_code": hierarchy.department_code,
            "department_name": hierarchy.department_name,
            "is_pdet": hierarchy.is_pdet,
            "pdet_subregion": hierarchy.pdet_subregion_name,
            "applicable_instruments": [i.model_dump() for i in hierarchy.applicable_instruments],
            "quarantine_artifacts_count": len(available_docs),
            "quarantine_artifact_ids": available_docs,
        })

    return {
        "pilots_count": len(pilots_data),
        "pilots": pilots_data,
    }


@atlas_router.post(
    "/artifacts/{source_id}/extract-beliefs",
    response_model=TerritorialBeliefExtractionResult,
    summary="Extraer creencias territoriales eBDI con micro-LLM soberano local",
)
async def extract_beliefs(source_id: str, force_reextract: bool = False):
    """Ejecuta la extracción de creencias territoriales sobre un documento aprobado en cuarentena."""
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido.")

    try:
        return await belief_extractor.extract_beliefs_from_artifact(source_id, force_reextract=force_reextract)
    except ArtifactNotApprovedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except BeliefExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error durante extracción de creencias: {exc}")


@atlas_router.get(
    "/artifacts/{source_id}/beliefs",
    response_model=TerritorialBeliefExtractionResult,
    summary="Consultar creencias territoriales extraídas de un artefacto",
)
def get_artifact_beliefs(source_id: str):
    """Consulta el artefacto de creencias persistido para un documento en outputs/atlas/context/."""
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido.")

    belief_file = belief_extractor.context_output_dir / f"{source_id}_beliefs.json"
    if not belief_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No se han extraído creencias eBDI aún para el artefacto '{source_id}'.",
        )
    try:
        data = json.loads(belief_file.read_text(encoding="utf-8"))
        return TerritorialBeliefExtractionResult.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error leyendo creencias persistidas: {exc}")


@atlas_router.get(
    "/pilots/{divipola}/beliefs",
    response_model=PilotAggregatedBeliefs,
    summary="Consultar creencias eBDI consolidadas y heredadas para un municipio piloto",
)
def get_pilot_beliefs(divipola: str):
    """Agrega las creencias aplicables a un municipio piloto a través de la cascada de políticas aprobadas."""
    try:
        return belief_extractor.get_pilot_aggregated_beliefs(divipola)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error consolidando creencias piloto: {exc}")


@atlas_router.patch(
    "/artifacts/{source_id}/beliefs/{belief_id}",
    response_model=TerritorialBeliefItem,
    summary="Curar manualmente una creencia eBDI específica (admitir o descartar como ruido)",
)
def curate_artifact_belief(
    source_id: str,
    belief_id: str,
    request: BeliefCurationRequest,
):
    """Permite a un revisor humano admitir formalmente o descartar como ruido una creencia individual."""
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido.")
    if ".." in belief_id or "/" in belief_id or "\\" in belief_id:
        raise HTTPException(status_code=400, detail="Identificador de creencia no válido.")

    try:
        return belief_extractor.curate_belief(
            source_id=source_id,
            belief_id=belief_id,
            decision=request.decision,
            curator_id=request.curator_id,
            notes=request.notes,
        )
    except BeliefExtractionError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error curando creencia: {exc}")


@atlas_router.post(
    "/artifacts/{source_id}/ocr",
    summary="Ejecutar OCR soberano local (pdftoppm + Tesseract) sobre un artefacto escaneado",
)
def run_artifact_ocr(source_id: str, max_pages: int = 15):
    """Ejecuta OCR local soberano sin nube sobre un documento escaneado en cuarentena."""
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido.")

    manifest = manifest_manager.load_manifest()
    if source_id not in manifest.documents:
        raise HTTPException(status_code=404, detail=f"Artefacto '{source_id}' no encontrado.")

    doc = manifest.documents[source_id]
    pdf_path = (manifest_manager.base_dir / doc.content_path).resolve()
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"Archivo físico no encontrado: {pdf_path}")

    try:
        text = ocr_processor.extract_text_with_ocr(pdf_path, max_pages=max_pages)
        return {
            "source_id": source_id,
            "characters_extracted": len(text),
            "ocr_text_preview": text[:500],
            "status": "completed",
        }
    except OCRError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fallo en procesamiento OCR: {exc}")


@atlas_router.put(
    "/artifacts/{source_id}/beliefs/{belief_id}",
    response_model=TerritorialBeliefItem,
    summary="Editar campos de una creencia territorial (soporta modo amigable o programador)",
)
def update_artifact_belief(
    source_id: str,
    belief_id: str,
    request: BeliefEditRequest,
):
    """Permite al investigador corregir la condición, acción, efecto o cita textual de una creencia extraída."""
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido.")
    if ".." in belief_id or "/" in belief_id or "\\" in belief_id:
        raise HTTPException(status_code=400, detail="Identificador de creencia no válido.")

    try:
        return belief_extractor.update_belief_item(
            source_id=source_id,
            belief_id=belief_id,
            edit=request,
        )
    except BeliefExtractionError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error actualizando creencia: {exc}")


@atlas_router.post(
    "/artifacts/{source_id}/compile-yaml",
    summary="Compilar creencias admitidas de un artefacto a especificaciones GoalSpec y PlanSpec en YAML",
)
def compile_beliefs_to_yamls(source_id: str, only_admitted: bool = True):
    """Compila las creencias verificadas y admitidas a archivos GoalSpec y PlanSpec YAML conformes a EthosTerra."""
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido.")

    belief_file = belief_extractor.context_output_dir / f"{source_id}_beliefs.json"
    if not belief_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No se han extraído creencias para el artefacto '{source_id}'.",
        )

    try:
        data = json.loads(belief_file.read_text(encoding="utf-8"))
        res = TerritorialBeliefExtractionResult.model_validate(data)
        report = yaml_compiler.compile_and_save(
            beliefs=res.beliefs,
            document_id=res.source_id,
            document_hash=res.document_sha256,
            only_admitted=only_admitted,
        )
        return report
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error durante la compilación a YAML: {exc}")


@atlas_router.get(
    "/artifacts/{source_id}/compiled-yamls",
    summary="Listar archivos YAML compilados disponibles para un artefacto",
)
def get_compiled_yamls(source_id: str):
    """Consulta los archivos GoalSpec y PlanSpec YAML generados para este artefacto en outputs/atlas/yaml/."""
    if ".." in source_id or "/" in source_id or "\\" in source_id:
        raise HTTPException(status_code=400, detail="Identificador de fuente no válido.")

    goals = []
    for g_path in yaml_compiler.goals_dir.glob("*.yaml"):
        try:
            content = g_path.read_text(encoding="utf-8")
            if f"Documento de Origen: {source_id}" in content:
                goals.append({
                    "filename": g_path.name,
                    "type": "goal",
                    "rel_path": str(g_path.relative_to(Path.cwd())),
                    "content": content,
                })
        except Exception:
            continue

    plans = []
    for p_path in yaml_compiler.plans_dir.glob("*.yaml"):
        try:
            content = p_path.read_text(encoding="utf-8")
            if f"Documento de Origen: {source_id}" in content:
                plans.append({
                    "filename": p_path.name,
                    "type": "plan",
                    "rel_path": str(p_path.relative_to(Path.cwd())),
                    "content": content,
                })
        except Exception:
            continue

    return {
        "source_id": source_id,
        "total_yamls": len(goals) + len(plans),
        "goals": goals,
        "plans": plans,
    }

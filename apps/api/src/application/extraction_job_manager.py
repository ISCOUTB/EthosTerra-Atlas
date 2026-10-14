"""Gestor asíncrono en segundo plano para tareas de extracción semántica eBDI de artefactos."""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

from apps.atlas.extractors.belief_extractor import (
    ArtifactNotApprovedError,
    BeliefExtractionError,
    TerritorialBeliefExtractor,
)
from apps.atlas.schemas.context_schemas import TerritorialBeliefExtractionResult

logger = logging.getLogger("extraction_job_manager")


class ExtractionJobStatus(BaseModel):
    """Estado y telemetría de una tarea de extracción de creencias."""
    job_id: str = Field(..., description="Identificador único de la tarea")
    source_id: str = Field(..., description="Identificador del artefacto documental")
    status: Literal["idle", "processing", "completed", "failed"] = Field(
        default="idle",
        description="Estado del ciclo de vida del procesamiento"
    )
    total_chunks: int = Field(default=0, description="Total de fragmentos seleccionados para inferencia")
    current_chunk: int = Field(default=0, description="Fragmento actualmente en procesamiento")
    message: str = Field(default="", description="Mensaje legible de avance para el usuario")
    progress_percent: float = Field(default=0.0, description="Porcentaje de avance (0.0 a 100.0)")
    result: Optional[TerritorialBeliefExtractionResult] = Field(default=None, description="Resultado final estructurado")
    error: Optional[str] = Field(default=None, description="Mensaje de error en caso de fallo")
    created_at: str = Field(default="", description="Marca temporal ISO de inicio")
    updated_at: str = Field(default="", description="Marca temporal ISO de última actualización")


class ExtractionJobManager:
    """Administrador de tareas de inferencia pesada en segundo plano con protección contra duplicidad."""

    def __init__(self, extractor: TerritorialBeliefExtractor) -> None:
        self.extractor = extractor
        self._jobs: Dict[str, ExtractionJobStatus] = {}
        self._lock = asyncio.Lock()

    def get_job(self, source_id: str) -> Optional[ExtractionJobStatus]:
        """Obtiene el estado actual del job para un source_id dado."""
        return self._jobs.get(source_id)

    async def enqueue_extraction(
        self,
        source_id: str,
        force_reextract: bool = False,
    ) -> tuple[ExtractionJobStatus, bool]:
        """Encola una tarea de extracción si no está ya en ejecución.

        Retorna (job_status, is_new_task).
        """
        async with self._lock:
            existing = self._jobs.get(source_id)
            if existing and existing.status == "processing":
                logger.info(f"Tarea ya en curso para {source_id} (job {existing.job_id}). Reutilizando...")
                return existing, False

            job_id = f"job_extract_{source_id}_{uuid.uuid4().hex[:8]}"
            now_iso = datetime.now(timezone.utc).isoformat()

            new_job = ExtractionJobStatus(
                job_id=job_id,
                source_id=source_id,
                status="processing",
                total_chunks=0,
                current_chunk=0,
                message="Iniciando tarea de extracción soberana en segundo plano...",
                progress_percent=5.0,
                created_at=now_iso,
                updated_at=now_iso,
            )
            self._jobs[source_id] = new_job

            # Lanzar tarea asíncrona desacoplada de la conexión HTTP del cliente
            asyncio.create_task(self._execute_extraction(source_id, force_reextract, job_id))
            return new_job, True

    async def _execute_extraction(
        self,
        source_id: str,
        force_reextract: bool,
        job_id: str,
    ) -> None:
        """Bucle de ejecución asíncrono con captura de progreso y errores."""
        logger.info(f"Iniciando ejecución asíncrona de extracción para {source_id} (job {job_id})")

        def on_progress(current: int, total: int, msg: str) -> None:
            job = self._jobs.get(source_id)
            if not job or job.job_id != job_id:
                return
            pct = 10.0 + ((current / max(total, 1)) * 85.0)
            job.total_chunks = total
            job.current_chunk = current
            job.message = msg
            job.progress_percent = round(min(pct, 98.0), 1)
            job.updated_at = datetime.now(timezone.utc).isoformat()

        try:
            result = await self.extractor.extract_beliefs_from_artifact(
                source_id=source_id,
                force_reextract=force_reextract,
                progress_callback=on_progress,
            )

            job = self._jobs.get(source_id)
            if job and job.job_id == job_id:
                job.status = "completed"
                job.message = f"Extracción completada exitosamente ({len(result.beliefs)} proposiciones obtenidas)."
                job.progress_percent = 100.0
                job.result = result
                job.updated_at = datetime.now(timezone.utc).isoformat()
                logger.info(f"Extracción completada para {source_id}: {len(result.beliefs)} creencias")

        except ArtifactNotApprovedError as exc:
            logger.warning(f"Extracción rechazada para {source_id}: {exc}")
            job = self._jobs.get(source_id)
            if job and job.job_id == job_id:
                job.status = "failed"
                job.error = str(exc)
                job.message = "Artefacto no aprobado para extracción de contexto."
                job.updated_at = datetime.now(timezone.utc).isoformat()

        except BeliefExtractionError as exc:
            logger.error(f"Error de extracción en {source_id}: {exc}")
            job = self._jobs.get(source_id)
            if job and job.job_id == job_id:
                job.status = "failed"
                job.error = str(exc)
                job.message = f"Error en pipeline de extracción: {exc}"
                job.updated_at = datetime.now(timezone.utc).isoformat()

        except Exception as exc:
            logger.exception(f"Fallo inesperado durante extracción de {source_id}: {exc}")
            job = self._jobs.get(source_id)
            if job and job.job_id == job_id:
                job.status = "failed"
                job.error = f"Error inesperado: {exc}"
                job.message = "Fallo interno durante el procesamiento del documento."
                job.updated_at = datetime.now(timezone.utc).isoformat()

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal, Any
from uuid import UUID

class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    trace_id: UUID = Field(..., description="ID único para la traza de auditoría")
    model: str = Field(..., description="Nombre del modelo (ej. gemma-4-e4b)")
    latency_ms: float = Field(..., description="Latencia de la inferencia en milisegundos")
    prompt_digest: str = Field(..., description="Hash/Digest de las entradas para reproducibilidad")

class CasoPuro(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tipo: Literal["puro"] = "puro"
    clasificacion: str = Field(..., description="Categoría o acción propuesta directamente")
    confianza: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza del LLM")
    razonamiento: str = Field(..., description="Justificación breve para ser validada por eBDI")

class FuenteEnColision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    source_type: Literal["context_field", "document"] = Field(
        default="context_field", description="Distinción entre variable de contexto y norma documental"
    )
    source_id: str = Field(..., description="ID de la fuente, variable o regla")
    intencion: str = Field(default="", description="Intención activada por la fuente")
    efecto: str = Field(default="", description="Efecto esperado o consecuencia de la acción")
    evidence_ref: str = Field(default="", description="Referencia a la evidencia")
    value: Any = Field(default=None, description="Valor observado en el contexto si es context_field")
    source_path: str | None = Field(default=None, description="Ruta documental si aplica")
    text_quote: str | None = Field(default=None, description="Cita textual de la norma si aplica")
    source_hash: str | None = Field(default=None, description="Hash criptográfico si aplica")
    fuente_id: str | None = Field(default=None, description="Alias compatible de source_id")
    evidencia: str | None = Field(default=None, description="Alias compatible de evidence_ref")

    @model_validator(mode="before")
    @classmethod
    def reconcile_source_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values = dict(values)
            if "fuente_id" in values and "source_id" not in values:
                values["source_id"] = values["fuente_id"]
            elif "source_id" in values and "fuente_id" not in values:
                values["fuente_id"] = values["source_id"]
            if "evidencia" in values and "evidence_ref" not in values:
                values["evidence_ref"] = values["evidencia"]
            elif "evidence_ref" in values and "evidencia" not in values:
                values["evidencia"] = values["evidence_ref"]
        return values

class CasoConflictivo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tipo: Literal["conflicto"] = "conflicto"
    conflicto_detectado: str = Field(..., description="Descripción exacta de la contradicción en el contexto")
    opciones_resolucion: list[str] = Field(..., min_length=1, description="Cursos de acción alternativos")
    requiere_humano: bool = Field(default=True, description="Human-in-the-loop flag explícita")
    titulo_conflicto: str | None = Field(default=None, description="Título descriptivo del conflicto")
    descripcion_contradiccion: str | None = Field(default=None, description="Descripción detallada de la incompatibilidad")
    ubicacion: str | None = Field(default=None, description="Ubicación espacial, parcela o componente")
    ruta_archivo_colisionado: str | None = Field(default=None, description="Ruta de regla o fuente en colisión")
    fuentes_en_colision: list[FuenteEnColision] = Field(default_factory=list, description="Listado de fuentes normativas en colisión")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confianza en la detección del conflicto")
    razonamiento: str = Field(default="", description="Justificación eBDI del conflicto")

    @model_validator(mode="before")
    @classmethod
    def reconcile_conflict_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values = dict(values)
            if "descripcion_contradiccion" in values and "conflicto_detectado" not in values:
                values["conflicto_detectado"] = values["descripcion_contradiccion"]
            elif "conflicto_detectado" in values and "descripcion_contradiccion" not in values:
                values["descripcion_contradiccion"] = values["conflicto_detectado"]
            if "requires_human_review" in values:
                req = values.pop("requires_human_review")
                if "requiere_humano" not in values:
                    values["requiere_humano"] = req
        return values

class CasoAmbiguo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tipo: Literal["ambiguo"] = "ambiguo"
    conflicto_detectado: str = Field(..., description="Causa de la ambigüedad o falta de datos")
    opciones_resolucion: list[str] = Field(default_factory=list, description="Opciones")
    requiere_humano: bool = Field(default=True)

# Type Alias para la salida que evaluará el core lógico
ResultadoPropuesta = CasoPuro | CasoConflictivo | CasoAmbiguo
class PropuestaClasificacion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    contexto_id: str
    resultado: ResultadoPropuesta
    metadatos: Metadata

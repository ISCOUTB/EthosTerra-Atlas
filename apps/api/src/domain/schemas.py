from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
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

class CasoConflictivo(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tipo: Literal["conflicto"] = "conflicto"
    conflicto_detectado: str = Field(..., description="Descripción exacta de la contradicción en el contexto")
    opciones_resolucion: list[str] = Field(..., min_length=1, description="Cursos de acción alternativos")
    requiere_humano: bool = Field(default=True, description="Human-in-the-loop flag explícita")

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

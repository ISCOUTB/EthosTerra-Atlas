from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, List
from uuid import UUID
from datetime import datetime

class ProposeInputSchema(BaseModel):
    """
    Esquema de entrada para el endpoint /classifications:propose.
    Define estrictamente lo que el simulador BESA tiene permitido enviar.
    """
    simulator_id: str = Field(..., description="ID del agente o nodo en el simulador EthosTerra")
    timestamp: datetime = Field(..., description="Marca de tiempo de la simulación (ISO 8601)")
    context_data: Dict[str, Any] = Field(
        ..., 
        description="Variables sanitizadas del entorno (presión, temperatura, alarmas). No incluye rutas de archivos locales."
    )

class LLMMetadata(BaseModel):
    """Metadatos de auditoría para la inferencia del modelo."""
    model_name: str
    model_digest: str
    latency_ms: float
    tokens_used: int = Field(default=0, description="Cantidad de tokens (prompt + completion) procesados")

class ProposeOutputSchema(BaseModel):
    """
    Esquema exacto de la respuesta que devolverá el API, 
    garantizando un contrato fuerte para el orquestador BESA.
    """
    trace_id: UUID
    status: Literal["propuesta", "validada", "requires_review", "rejected"]
    case_type: Literal["pure", "conflict", "unclear"]
    data: Dict[str, Any] = Field(..., description="El payload estructurado propuesto por el LLM")
    validation_errors: List[str] = Field(default_factory=list, description="Errores semánticos detectados por las reglas deterministas")
    requires_human_review: bool
    metadata: LLMMetadata

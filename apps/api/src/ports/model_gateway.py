import abc
from typing import Dict, Any

class ModelGateway(abc.ABC):
    """
    Puerto de salida (Outbound Port) de la Arquitectura Hexagonal.
    Define el contrato estricto para solicitar generaciones estructuradas al micro-LLM.
    """

    @abc.abstractmethod
    async def generate_structured(
        self, 
        trace_id: str, 
        context: Dict[str, Any], 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envía un contexto al modelo de lenguaje y obliga a que la respuesta
        cumpla con un JSON Schema predefinido.

        Args:
            trace_id (str): Identificador único de auditoría para trazabilidad.
            context (Dict[str, Any]): Información provista por el simulador (BESA/EthosTerra).
            schema (Dict[str, Any]): Estructura JSON Schema (Draft 7) que el modelo debe obedecer.

        Returns:
            Dict[str, Any]: La respuesta del modelo, ya parseada como diccionario.
            
        Raises:
            ValueError: Si la validación semántica falla de manera irrecuperable.
            RuntimeError: Si ocurren fallos transitorios agotando los reintentos.
        """
        pass

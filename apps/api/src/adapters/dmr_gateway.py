import httpx
import asyncio
import logging
import json
import os
import hashlib
from typing import Dict, Any
from uuid import UUID

from src.domain.schemas import CasoPuro, CasoConflictivo, CasoAmbiguo, PropuestaClasificacion, Metadata, FuenteEnColision
logger = logging.getLogger("dmr_gateway")

class DMRGateway:
    def __init__(self, model_name: str = "ai/gemma4:E4B", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self._semaphore = asyncio.Semaphore(1)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)
        )
        
        pure_prompt_path = os.path.join(os.path.dirname(__file__), "../domain/prompts/case_pure_v1.txt")
        conflict_prompt_path = os.path.join(os.path.dirname(__file__), "../domain/prompts/case_conflict_v1.txt")
        try:
            with open(pure_prompt_path, "r", encoding="utf-8") as f:
                self.prompt_pure_template = f.read()
        except FileNotFoundError:
            self.prompt_pure_template = "Responde con JSON."

        try:
            with open(conflict_prompt_path, "r", encoding="utf-8") as f:
                self.prompt_conflict_template = f.read()
        except FileNotFoundError:
            self.prompt_conflict_template = self.prompt_pure_template

    async def propose_classification(self, trace_id: str, context_data: Dict[str, Any]) -> PropuestaClasificacion:
        async with self._semaphore:
            logger.info(f"[{trace_id}] Iniciando inferencia en DMRGateway para modelo {self.model_name}")
            
            from src.application.hooks import validate_invariants, should_use_conflict_prompt, extract_conflict_sources
            has_conflict, hook_msg = validate_invariants(context_data)
            
            if has_conflict:
                logger.info(f"[{trace_id}] Conflicto atrapado por hooks in-memory. Bypass LLM.")
                
                meta = Metadata(
                    trace_id=UUID(trace_id),
                    model=self.model_name + " (hook_bypass)",
                    latency_ms=5.0,
                    prompt_digest="deterministic_bypass"
                )
                
                if "Ambigüedad" in hook_msg:
                    resultado = CasoAmbiguo(
                        tipo="ambiguo",
                        conflicto_detectado=hook_msg,
                        opciones_resolucion=["Verificar sensores físicamente", "Reiniciar telemetría"],
                        requiere_humano=True
                    )
                else:
                    raw_sources = extract_conflict_sources(context_data, hook_msg)
                    fuentes = [FuenteEnColision(**s) for s in raw_sources]
                    resultado = CasoConflictivo(
                        tipo="conflicto",
                        conflicto_detectado=hook_msg,
                        titulo_conflicto="Conflicto detectado por reglas deterministas",
                        descripcion_contradiccion=hook_msg,
                        opciones_resolucion=["Aislamiento preventivo", "Revisión manual inmediata"],
                        fuentes_en_colision=fuentes,
                        requiere_humano=True,
                        confidence=1.0,
                        razonamiento="Invariante física o regla agronómica violada determinísticamente."
                    )
                    
                return PropuestaClasificacion(
                    contexto_id=context_data.get("id", "unknown"),
                    resultado=resultado,
                    metadatos=meta
                )
            
            # Selección condicional de prompt (S7-S8)
            use_conflict_prompt = should_use_conflict_prompt(context_data)
            selected_template = self.prompt_conflict_template if use_conflict_prompt else self.prompt_pure_template
            logger.info(f"[{trace_id}] Prompt seleccionado: {'case_conflict_v1' if use_conflict_prompt else 'case_pure_v1'}")

            # Enriquecemos el entorno (Environment -> Sensors)
            enriched_context = {
                "variables_sensadas": context_data,
                "resultado_herramientas_in_memory": {
                    "hay_conflicto_detectado_por_reglas": has_conflict,
                    "detalle_herramientas": hook_msg
                }
            }
            
            context_str = json.dumps(enriched_context, ensure_ascii=False)
            prompt = selected_template.replace("{{context_data}}", context_str)
            prompt_digest = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.0
            }
            
            url = f"{self.base_url}chat/completions"
            
            try:
                logger.info(f"[{trace_id}] Enviando solicitud a DMR OpenAI API...")
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                
                body = response.json()
                logger.debug(f"[{trace_id}] Respuesta exitosa de DMR.")
                
                latency_ms = body.get("timings", {}).get("predicted_ms", 0) + body.get("timings", {}).get("prompt_ms", 0)
                if not latency_ms:
                    latency_ms = response.elapsed.total_seconds() * 1000

                meta = Metadata(
                    trace_id=UUID(trace_id),
                    model=self.model_name,
                    latency_ms=latency_ms,
                    prompt_digest=prompt_digest
                )
                
                msg_content = body.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                parsed = json.loads(msg_content)
                
                if parsed.get("tipo") == "conflicto":
                    resultado = CasoConflictivo(**parsed)
                elif parsed.get("tipo") == "ambiguo":
                    resultado = CasoAmbiguo(**parsed)
                else:
                    if "tipo" not in parsed:
                        parsed["tipo"] = "puro"
                    resultado = CasoPuro(**parsed)
                
                return PropuestaClasificacion(
                    contexto_id=context_data.get("id", "unknown"),
                    resultado=resultado,
                    metadatos=meta
                )

            except httpx.HTTPStatusError as e:
                err_body = str(e.response.text)[:2000]
                logger.error(f"[{trace_id}] HTTPStatusError: {e.response.status_code}. Header: {e.response.headers}. Body: {err_body}")
                raise RuntimeError(f"DMR Status Error: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"[{trace_id}] RequestError: {str(e)[:2000]}", exc_info=True)
                raise RuntimeError(f"DMR Request Error: Conexion rechazada o fallida")
            except Exception as e:
                logger.error(f"[{trace_id}] Error Interno (Posible Fallo de Validación Pydantic): {str(e)[:2000]}", exc_info=True)
                raise RuntimeError(f"DMR Error Interno: {str(e)[:200]}")

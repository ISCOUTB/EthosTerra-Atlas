import httpx
import asyncio
import logging
import json
from typing import Dict, Any

logger = logging.getLogger("dmr_gateway")

class DMRGateway:
    def __init__(self, model_name: str = "ai/gemma4:E4B", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url if base_url.endswith('/') else base_url + '/'
        self._semaphore = asyncio.Semaphore(1)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)
        )

    async def propose_classification(self, trace_id: str, context_data: Dict[str, Any]) -> Any:
        async with self._semaphore:
            logger.info(f"[{trace_id}] Iniciando inferencia en DMRGateway para modelo {self.model_name}")
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un clasificador de eBDI. Analiza el JSON y responde estrictamente con JSON. Debes incluir las llaves: tipo (puro, conflictivo, ambiguo), clasificacion, confianza, requiere_humano."
                    },
                    {
                        "role": "user",
                        "content": f"Clasifica este contexto: {context_data}"
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0
            }
            
            # OpenAI compatible endpoint expuesto por Docker Model Runner
            url = f"{self.base_url}chat/completions"
            logger.debug(f"[{trace_id}] Endpoint: {url}")
            
            try:
                logger.info(f"[{trace_id}] Enviando solicitud a DMR OpenAI API...")
                response = await self.client.post(url, json=payload)
                response.raise_for_status()
                
                body = response.json()
                logger.debug(f"[{trace_id}] Respuesta exitosa de DMR.")
                
                class MockMetadata:
                    model = self.model_name
                    prompt_digest = body.get("system_fingerprint", "sha256:real")
                    latency_ms = body.get("timings", {}).get("predicted_ms", 0) + body.get("timings", {}).get("prompt_ms", 0)
                    if not latency_ms:
                        latency_ms = response.elapsed.total_seconds() * 1000

                class MockResult:
                    tipo = "pure"
                    clasificacion = "procesado"
                    confianza = 0.9
                    requiere_humano = False
                
                class MockRaw:
                    metadatos = MockMetadata()
                    resultado = MockResult()
                    
                    def __init__(self, raw_resp):
                        try:
                            msg_content = raw_resp.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                            parsed = json.loads(msg_content)
                            if parsed.get("tipo") == "conflictivo":
                                self.resultado.tipo = "conflict"
                            elif parsed.get("tipo") == "ambiguo":
                                self.resultado.tipo = "unclear"
                            self.resultado.clasificacion = parsed.get("clasificacion", "...")
                            self.resultado.requiere_humano = parsed.get("requiere_humano", False)
                        except Exception as e:
                            logger.error(f"[{trace_id}] Error parseando contenido: {e}")

                return MockRaw(body)

            except httpx.HTTPStatusError as e:
                err_body = str(e.response.text)[:2000]
                logger.error(f"[{trace_id}] HTTPStatusError: {e.response.status_code}. Header: {e.response.headers}. Body: {err_body}")
                raise RuntimeError(f"DMR Status Error: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error(f"[{trace_id}] RequestError: {str(e)[:2000]}", exc_info=True)
                raise RuntimeError(f"DMR Request Error: Conexion rechazada o fallida")
            except Exception as e:
                logger.error(f"[{trace_id}] Timeout/Exception: {str(e)[:2000]}", exc_info=True)
                raise RuntimeError(f"DMR Error Interno: {str(e)[:200]}")

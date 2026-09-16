from fastapi import FastAPI, HTTPException, Depends, Request
from uuid import uuid4
from typing import Dict, Any
import logging
import os
import traceback
import httpx

from src.domain.api_schemas import ProposeInputSchema, ProposeOutputSchema, LLMMetadata
from src.adapters.dmr_gateway import DMRGateway
from src.ports.model_gateway import ModelGateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("api")
logger.setLevel(logging.DEBUG)

app = FastAPI(title="Hybrid eBDI-LLM API", version="0.1.0")

def get_model_gateway() -> ModelGateway:
    model_url = os.environ.get("MODEL_BASE_URL", "http://host.docker.internal:11434/")
    if not model_url.endswith('/'): model_url += '/'
    model_name = os.environ.get("MODEL_NAME", "ai/gemma4:E4B")
    return DMRGateway(model_name=model_name, base_url=model_url)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/diagnostics/model")
async def diagnostics_model(gateway: DMRGateway = Depends(get_model_gateway)):
    url = f"{gateway.base_url}models"
    diag = {
        "status": "ok",
        "provider": "dmr",
        "model_base_url": gateway.base_url,
        "model_name": gateway.model_name,
        "connectivity": {
            "tags": "error",
            "show": "error",
            "chat_canary": "error"
        },
        "errors": []
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            diag["connectivity"]["tags"] = "ok"
        except Exception as e:
            diag["errors"].append(f"Models endpoint: {str(e)[:200]}")
            diag["status"] = "error"
            
        try:
            chat_payload = {
                "model": gateway.model_name,
                "messages": [{"role": "user", "content": "hello. Output JSON."}],
                "response_format": {"type": "json_object"}
            }
            r = await client.post(f"{gateway.base_url}chat/completions", json=chat_payload)
            r.raise_for_status()
            diag["connectivity"]["chat_canary"] = "ok"
        except Exception as e:
            diag["errors"].append(f"Chat canary ({type(e).__name__}): {str(e)[:200]}")
            diag["status"] = "error"
            
    return diag

@app.post("/classifications:propose", response_model=ProposeOutputSchema)
async def propose_classification(
    payload: ProposeInputSchema, 
    gateway: DMRGateway = Depends(get_model_gateway)
):
    trace_id = str(uuid4())
    logger.info(f"[{trace_id}] Solicitud entrante POST /classifications:propose")
    
    try:
        propuesta_cruda = await gateway.propose_classification(trace_id, payload.context_data)
        raw_type = getattr(propuesta_cruda.resultado, "tipo", "puro")
        case_type_map = {"puro": "pure", "conflicto": "conflict", "ambiguo": "unclear"}
        case_type = case_type_map.get(raw_type, "pure")
        
        logger.info(f"[{trace_id}] Clasificación exitosa: {case_type}")
        from uuid import UUID
        return ProposeOutputSchema(
            trace_id=UUID(trace_id),
            status="requires_review" if case_type != "pure" else "propuesta",
            case_type=case_type,
            data={"clasificacion": getattr(propuesta_cruda.resultado, "clasificacion", "N/A")},
            validation_errors=[],
            requires_human_review=getattr(propuesta_cruda.resultado, "requiere_humano", False),
            metadata=LLMMetadata(
                model_name=propuesta_cruda.metadatos.model,
                model_digest=propuesta_cruda.metadatos.prompt_digest,
                latency_ms=propuesta_cruda.metadatos.latency_ms,
                tokens_used=0
            )
        )
    except RuntimeError as re:
        logger.error(f"[{trace_id}] RuntimeError de gateway: {re}")
        raise HTTPException(status_code=503, detail=str(re))
    except Exception as e:
        full_trace = traceback.format_exc()
        logger.error(f"[{trace_id}] Excepción no manejada: {str(e)}\n{full_trace}")
        raise HTTPException(status_code=500, detail="Internal Application Error")

import httpx
import asyncio
import sys

API_URL = "http://localhost:8000"

async def test_diagnostics_and_canary():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n[Canary] Solicitando /diagnostics/model ...")
        res = await client.get(f"{API_URL}/diagnostics/model")
        if res.status_code != 200:
            print(f"Error en diagnostico: {res.text}")
            sys.exit(1)
        data = res.json()
        print(f"[Canary] Diagnóstico devuelto: {data}")
        
        if data["connectivity"]["chat_canary"] != "ok":
            print(f"Chat Canary falló internamente: {data.get('errors')}")
            sys.exit(1)
        
        print("\n[Canary] Inferencia de prueba (Caso Puro Dummy)...")
        payload = {
            "simulator_id": "test",
            "timestamp": "2026-09-08T00:00:00Z",
            "context_data": {"test": "ok"}
        }
        res2 = await client.post(f"{API_URL}/classifications:propose", json=payload, timeout=120.0)
        if res2.status_code != 200:
            print(f"Error en inferencia canaria: {res2.text}")
            sys.exit(1)
            
        data2 = res2.json()
        print(f"\n[Canary] ÉXITO. Trace ID: {data2.get('trace_id')}. Latencia: {data2.get('metadata', {}).get('latency_ms')}")

if __name__ == "__main__":
    asyncio.run(test_diagnostics_and_canary())

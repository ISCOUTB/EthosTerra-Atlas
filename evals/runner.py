import json
import httpx
import asyncio
from datetime import datetime, timezone
import sys

API_URL = "http://localhost:8000/classifications:propose"

async def run_evals():
    print("Iniciando evaluación...")
    try:
        with open("evals/datasets/test-cases.json", "r") as f:
            cases = json.load(f)
    except FileNotFoundError:
        print("ERROR: test-cases.json no encontrado.")
        return

    # Si hay argumento test-verbose o algo, leemos
    verbose = "--verbose" in sys.argv
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_name": "ai/gemma4:E4B",
        "model_digest": "sha256:real",
        "evaluation_mode": "real_model",
        "evaluation_status": "infrastructure_ready_inference_failed",
        "total_cases": len(cases),
        "attempted_cases": len(cases),
        "completed_cases": 0,
        "failed_requests": 0,
        "inference_availability": 0.0,
        "metrics": {
            "case_type_accuracy": None,
            "conflict_recall": None,
            "false_conflict_rate": None,
            "hallucination_rate": None,
            "human_review_alignment": None,
            "avg_latency_ms": None,
            "tokens_per_second": None
        },
        "failure_summary": {
            "http_500": 0,
            "connection_disconnected": 0
        },
        "failures": [],
        "note": "No se obtuvieron métricas completas."
    }

    correct_case_types = 0
    total_conflicts = sum(1 for c in cases if c["expected_case_type"] == "conflict")
    detected_conflicts = 0
    total_pures = sum(1 for c in cases if c["expected_case_type"] == "pure")
    false_conflicts = 0
    hallucinated_cases = 0
    human_aligned = 0
    completed = 0
    failed_500 = 0
    failed_conn = 0
    latencies = []

    async with httpx.AsyncClient(timeout=200.0) as client:
        for i, case in enumerate(cases):
            expected_type = case["expected_case_type"]
            is_conflict = expected_type == "conflict"
            
            if verbose: print(f"[{i+1}/{len(cases)}] Evaluando caso: {case['id']}...")
            
            try:
                res = await client.post(API_URL, json=case["input"])
                if res.status_code == 500 or res.status_code == 502 or res.status_code == 503:
                    failed_500 += 1
                    report["failures"].append({"case_id": case["id"], "error_type": f"HTTP {res.status_code}"})
                    continue
                    
                res.raise_for_status()
                data = res.json()
                completed += 1
                
                latency = data.get("metadata", {}).get("latency_ms", 0)
                if latency: latencies.append(latency)

                predicted_type = data.get("case_type", "unknown")
                predicted_review = data.get("requires_human_review", False)

                if predicted_type == expected_type: correct_case_types += 1
                if is_conflict and predicted_type == "conflict": detected_conflicts += 1
                if expected_type == "pure" and predicted_type == "conflict": false_conflicts += 1
                if predicted_review == case.get("invariants", {}).get("requires_human_review_expected"):
                    human_aligned += 1

                resp_str = json.dumps(data)
                hallucinated = False
                must_not = case.get("invariants", {}).get("must_not_contain")
                if must_not and must_not in resp_str:
                    hallucinated = True
                    hallucinated_cases += 1

                if predicted_type != expected_type or hallucinated:
                    report["failures"].append({
                        "case_id": case["id"],
                        "expected": expected_type,
                        "predicted": predicted_type,
                        "error_type": "HALLUCINATION" if hallucinated else "MISMATCH",
                        "trace_id": data.get("trace_id", "none")
                    })
            except httpx.RequestError as e:
                failed_conn += 1
                report["failures"].append({"case_id": case["id"], "error_type": f"Connection Error: {str(e)[:100]}"})
            except Exception as e:
                failed_conn += 1
                report["failures"].append({"case_id": case["id"], "error_type": f"Exception: {str(e)[:100]}"})

    report["completed_cases"] = completed
    report["failed_requests"] = failed_500 + failed_conn
    report["failure_summary"]["http_500"] = failed_500
    report["failure_summary"]["connection_disconnected"] = failed_conn
    report["inference_availability"] = completed / len(cases)

    if completed == len(cases):
        report["evaluation_status"] = "success"
        report["note"] = "Evaluación completada."
        report["metrics"] = {
            "case_type_accuracy": correct_case_types / completed if completed else 0,
            "conflict_recall": detected_conflicts / total_conflicts if total_conflicts else 0,
            "false_conflict_rate": false_conflicts / total_pures if total_pures else 0,
            "hallucination_rate": hallucinated_cases / completed if completed else 0,
            "human_review_alignment": human_aligned / completed if completed else 0,
            "avg_latency_ms": sum(latencies)/len(latencies) if latencies else 0,
            "tokens_per_second": None
        }

    # Custom serializer to handle None as null correctly in json.dumps
    with open("evals/report.json", "w") as f:
        # replace custom python 'null' constant using a dict conversion trick, or just standard json dump since None -> null
        pass
    
    # Redoing dict to avoid `null` python NameError
    # Replace the dict definition `null` with `None`
    for k in report["metrics"]:
        if report["metrics"][k] == "null":
            report["metrics"][k] = None

    with open("evals/report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\nReporte actualizado en evals/report.json")

if __name__ == "__main__":
    asyncio.run(run_evals())

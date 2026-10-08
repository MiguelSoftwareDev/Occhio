"""Verifica serviços reais. Não usa mocks nem gera análises artificiais."""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


# Executa os dois métodos e confirma o consumo || Exercise both methods and confirm consumption
def verify(base_url: str, output: Path) -> None:
    evidence = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "results": [],
    }
    with httpx.Client(base_url=base_url, timeout=660, trust_env=False) as client:
        health = client.get("/api/health")
        health.raise_for_status()
        evidence["health"] = health.json()
        if not evidence["health"]["ok"]:
            raise RuntimeError(
                "Pipeline incompleto: " + json.dumps(evidence["health"], ensure_ascii=False)
            )
        unary = client.post("/api/analyze/once")
        unary.raise_for_status()
        results = [unary.json()]
        completed = False
        with client.stream("POST", "/api/analyze/stream?count=2") as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if event["type"] == "error":
                    raise RuntimeError(event["detail"])
                if event["type"] == "result":
                    results.append(event["result"])
                if event["type"] == "complete":
                    completed = True
        if not completed or len(results) != 3:
            raise RuntimeError("Esperadas uma resposta unária e duas respostas de streaming")
        if len({item["analysis_id"] for item in results}) != 3:
            raise RuntimeError("IDs de análises repetidos")
        for result in results:
            deadline = time.monotonic() + 30
            while True:
                persisted = client.get(f"/api/history/{result['analysis_id']}")
                if persisted.status_code == 200:
                    record = persisted.json()
                    if (
                        not record.get("consumed_at")
                        or record["analysis_text"] != result["analysis_text"]
                    ):
                        raise RuntimeError("Registro persistido diverge da resposta gRPC")
                    evidence["results"].append(record)
                    break
                if persisted.status_code != 404:
                    persisted.raise_for_status()
                if time.monotonic() >= deadline:
                    raise RuntimeError("Consumidor não confirmou a gravação em 30 segundos")
                time.sleep(1)
    evidence["status"] = "passed"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"PASS: unary + streaming + broker + consumidor + persistência. Evidência: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=Path("evidence/e2e.json"))
    args = parser.parse_args()
    try:
        verify(args.base_url, args.output)
    except (httpx.HTTPError, RuntimeError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)

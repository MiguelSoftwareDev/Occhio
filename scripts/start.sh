#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo "Crie .venv e instale requirements.lock.txt antes de iniciar." >&2
  exit 1
fi
if [[ "${1:-}" == "--monitor-only" ]]; then
  exec .venv/bin/python -m uvicorn backend.api.gateway:app --host 127.0.0.1 --port 8000
fi
if [[ "${1:-}" != "--skip-broker" ]]; then
  command -v docker >/dev/null || { echo "Instale Docker com Compose, ou use --monitor-only para somente metricas." >&2; exit 1; }
  docker info >/dev/null || { echo "Inicie o daemon Docker ou abra Docker Desktop." >&2; exit 1; }
  docker compose up -d --wait rabbitmq
fi
.venv/bin/python -m backend.generate_proto
exec .venv/bin/python backend/run_all.py

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo "Crie .venv e instale requirements.lock.txt antes de iniciar." >&2
  exit 1
fi
docker compose up -d --wait rabbitmq
.venv/bin/python -m backend.generate_proto
exec .venv/bin/python backend/run_all.py

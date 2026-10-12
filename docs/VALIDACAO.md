# Validation

## Revision: 2026-10-12

Executed on Linux with Python 3.12:

- 26 Python tests passed. Real loopback gRPC tests now construct the actual prompt after deserializing process metrics, covering the uint64/string regression.
- Ruff checks and Python formatting passed.
- Frontend source passed Prettier, strict TypeScript checking and Vite 6.4.4 production build.
- npm audit reported zero known vulnerabilities after updating Vite from 6.4.1 to 6.4.4. This is a dependency advisory check, not a comprehensive security assessment.

## Boundaries

Ollama inference and RabbitMQ publication/consumption were isolated by test adapters. Real model performance and the full broker-to-consumer path were not exercised in this review. Run `python scripts/verify_e2e.py` with the local services active to validate the installation.

The Windows startup script was reviewed and simplified to use Compose healthchecks; it was not executed on Windows here. Native Windows and macOS application-icon extraction also requires verification on those platforms.

Prior browser checks covered desktop/mobile layouts and pipeline/report states. This revision preserves the interface and the supplied assets; it does not claim a fresh native-platform UI verification.

## Corrected failures

- Process `memory_bytes` retains its integer type inside `message_to_snapshot`, preventing a TypeError while constructing the Ollama prompt. Protobuf JSON responses may still represent uint64 as strings; frontend and persistence support that format.
- Windows broker startup waits for the Compose healthcheck instead of polling a native command whose stderr could interrupt Windows PowerShell.
- Inference/publication failures identify their stage; the gRPC terminal retains a traceback for diagnosis.
- Vite was updated within major version 6 to include development-server fixes. The production console is served by FastAPI.

Advisory reference: https://github.com/vitejs/vite/security/advisories/GHSA-fx2h-pf6j-xcff

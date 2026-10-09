# Validation — pixel interface release

Validated on Linux with Python 3.12 and Node.js. The release archive includes the compiled Vite frontend.

## Executed checks

- 26 Python tests covering validation, collection, persistence, API origin/host protection, real loopback gRPC, publisher confirmation, consumer acknowledgement, live progress, runtime identity, process sampling, secondary volumes and ordered bidirectional progress.
- TypeScript strict typecheck and Vite production build.
- Ruff checks for backend, tests and scripts; Prettier for frontend source.
- Browser checks at 1512 px desktop width and 390 px mobile width, using live Linux metrics/processes: no page overflow or JavaScript errors; search and navigation controls exercised.
- Controlled browser pipeline run: analysis disables the action while busy, the penguin walks/types without crossing station labels/bars, five confirmed stages reach 100%, history details open, and reduced motion disables sprite animation.
- Separate 18-second animation rendered from the same assets into MP4. Its progress is illustrative, not live telemetry.

## External-service limits

The gRPC transport tests use a real loopback server. Ollama inference and RabbitMQ adapters are isolated in tests; a complete run against an installed model and a real broker/consumer remains an environment-level check. Use `python scripts/verify_e2e.py` with those services running.

Windows executable-icon extraction and macOS bundle-icon extraction are implemented but were not executed on their native operating systems here. Missing icons or restricted executable access produce an empty placeholder; no application logos are generated. Linux process collection was exercised in the browser.

The standalone animation and any test adapter data are previews only. Test adapters are outside the application and are not included in the release archive.

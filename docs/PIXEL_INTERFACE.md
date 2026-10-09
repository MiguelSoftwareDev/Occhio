# Pixel interface

The interface uses a light canvas, navy borders, cyan progress indicators and a red analysis action. The action has its own compact container beside the process heading. The full-width process table offers search by name/PID, sorting and internal scrolling. Narrow screens scroll the table and the village independently instead of overlapping their contents.

## Assets and movement

- `frontend/src/assets/penguin-atlas.png`: 4 columns × 2 rows; artwork on row 1 supplies independently animated foot cutouts, and row 2 supplies typing frames.
- `frontend/src/assets/stations-atlas.png`: five stations, left to right: collection, gRPC, Ollama, RabbitMQ and SQLite.
- `frontend/src/components/Pipeline.tsx`: service state determines the character's destination. The path has a reserved height; the character never passes over station labels, bars or the process table.
- `frontend/src/styles.css`: stepped sprite animations and responsive layouts; `prefers-reduced-motion` stops movement while preserving stage information.
- Pixelify Sans is bundled under its SIL Open Font License; see `frontend/src/assets/FONT-LICENSE.txt`.

The supplied character reference was used to generate the walking/typing atlas. The houses were generated from the approved design. Application icons are separate: those come only from the operating system.

## Progress contract

`POST /api/analyze/live` receives a snapshot and exposes real stage events as NDJSON. `AnalyzeProgress` streams inference/publication events from the gRPC service. Existing unary and bidirectional methods remain available.

1. Collection completes after a real snapshot is captured.
2. gRPC completes after the service validates and receives the snapshot.
3. Ollama completes after inference returns.
4. RabbitMQ completes after publisher confirmation.
5. SQLite completes only when the independent consumer's result can be read.

The overall percentage is completed stages / 5. Active stages are indeterminate, not invented fractions of LLM execution. A delayed consumer leaves the pipeline at 80%; the console continues checking storage. The optional bidirectional streaming mode uses StreamProgress to report stages for each snapshot and verifies storage separately.

Cancellation stops the request. A message already published can still be consumed. Errors leave the failed operation visible and do not turn the whole route green.

## Native icons

The collector registers opaque IDs for executable paths it observed. HTTP callers cannot supply arbitrary local paths. Windows extraction uses `ExtractAssociatedIcon` in a bundled PowerShell script, with arguments passed separately and no shell interpolation. Extraction concurrency is limited and results are cached. Linux resolves installed desktop entries with PNG icons. macOS reads application bundles and converts their icon using `sips`. Missing/unreadable icons receive an empty placeholder.

Processes may have multiple entries with the same application icon because they have distinct PIDs. The UI does not pretend that browser worker processes are separate installed products.

## Updating an existing checkout

1. Stop the running Occhio services.
2. Extract the updated `Occhio` folder over the checkout. Keep your `.env`, `.venv`, `.git` and `data` folders.
3. Run `python -m backend.generate_proto` with the project environment activated, or use the startup script that already performs this step.
4. Restart the project. The ZIP includes `frontend/dist`; source changes require a new `npm run build`.

To monitor without the inference services, start only Uvicorn. Metrics and process icons remain available; the analysis button explains which services are missing.

import asyncio
import json
from contextlib import asynccontextmanager
from uuid import UUID

import grpc
import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.core.config import PROJECT_ROOT, SETTINGS
from backend.domain.contracts import result_to_dict, snapshot_to_message
from backend.domain.contracts import system_monitor_pb2_grpc as pb2_grpc
from backend.infrastructure.messaging import get_broker_status
from backend.infrastructure.storage import (
    count_results,
    find_result,
    initialize_database,
    read_results,
)
from backend.services.collector import collect_snapshot

FRONTEND_DIR = PROJECT_ROOT / "frontend" / "dist"


# Prepara recursos da aplicação || Prepare application resources
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    app.state.analysis_lock = asyncio.Lock()
    yield


app = FastAPI(title="Occhio API", version="2.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


# Restringe mutações ao console local || Restrict mutations to the local console
@app.middleware("http")
async def local_requests(request: Request, call_next):
    if request.method == "POST":
        origin = request.headers.get("origin")
        if origin and origin not in {
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        }:
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Origem não permitida"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
    )
    response.headers["Cache-Control"] = "no-store"
    return response


# Abre o console compilado || Serve the built console
@app.get("/", include_in_schema=False)
async def home():
    if not (FRONTEND_DIR / "index.html").exists():
        raise HTTPException(503, "Compile o frontend: cd frontend && npm ci && npm run build")
    return FileResponse(FRONTEND_DIR / "index.html")


# Verifica o modelo local || Check the local model
async def check_ollama():
    status = {"available": False, "model": SETTINGS.ollama_model, "model_available": False}
    try:
        async with httpx.AsyncClient(timeout=2, trust_env=False) as client:
            response = await client.get(SETTINGS.ollama_url + "/api/tags")
            response.raise_for_status()
            status.update(
                available=True,
                model_available=any(
                    item.get("name") == SETTINGS.ollama_model
                    for item in response.json().get("models", [])
                ),
            )
    except (httpx.HTTPError, ValueError, TypeError):
        pass
    return status


# Verifica o transporte gRPC || Check gRPC transport
async def check_grpc():
    try:
        async with grpc.aio.insecure_channel(SETTINGS.grpc_address) as channel:
            await asyncio.wait_for(channel.channel_ready(), timeout=2)
        return {"available": True}
    except (asyncio.TimeoutError, grpc.aio.AioRpcError):
        return {"available": False}


# Verifica o broker sem bloquear o loop || Check the broker outside the event loop
async def check_broker():
    try:
        return await asyncio.to_thread(get_broker_status)
    except Exception:
        return {"available": False, "consumers": 0, "queued_messages": 0, "failed_messages": 0}


# Consulta a prontidão do pipeline || Check pipeline readiness
@app.get("/api/health")
async def health():
    ollama, transport, broker = await asyncio.gather(check_ollama(), check_grpc(), check_broker())
    consumer = broker.get("consumers", 0) > 0
    return {
        "ok": ollama["model_available"]
        and transport["available"]
        and broker["available"]
        and consumer,
        "ollama": ollama,
        "grpc": transport,
        "rabbitmq": broker,
        "consumer": consumer,
    }


# Coleta métricas do host || Collect host metrics
@app.get("/api/metrics")
async def metrics():
    return await asyncio.to_thread(collect_snapshot)


# Solicita uma análise unária || Request a unary analysis
@app.post("/api/analyze/once")
async def analyze_once():
    lock = app.state.analysis_lock
    if lock.locked():
        raise HTTPException(409, "Já existe uma análise em andamento")
    async with lock:
        snapshot = await asyncio.to_thread(collect_snapshot)
        try:
            async with grpc.aio.insecure_channel(SETTINGS.grpc_address) as channel:
                result = await pb2_grpc.SystemAnalysisStub(channel).AnalyzeSnapshot(
                    snapshot_to_message(snapshot), timeout=SETTINGS.analysis_timeout_seconds + 15
                )
        except grpc.aio.AioRpcError as error:
            raise HTTPException(
                503, "Análise indisponível. Verifique Ollama, gRPC e RabbitMQ."
            ) from error
        return result_to_dict(result)


# Encaminha resultados à medida que chegam || Forward results as they arrive
@app.post("/api/analyze/stream")
async def analyze_stream(
    count: int = Query(default=3, ge=2, le=10),
    interval_seconds: float = Query(default=1, ge=0.5, le=5),
):
    lock = app.state.analysis_lock
    if lock.locked():
        raise HTTPException(409, "Já existe uma análise em andamento")
    await lock.acquire()

    # Produz coletas reais || Produce real snapshots
    async def snapshots():
        for index in range(count):
            yield snapshot_to_message(await asyncio.to_thread(collect_snapshot))
            if index + 1 < count:
                await asyncio.sleep(interval_seconds)

    # Emite NDJSON para o navegador || Emit NDJSON to the browser
    async def events():
        try:
            yield json.dumps({"type": "started", "count": count}) + "\n"
            async with grpc.aio.insecure_channel(SETTINGS.grpc_address) as channel:
                call = pb2_grpc.SystemAnalysisStub(channel).StreamSnapshots(
                    snapshots(),
                    timeout=count * (SETTINGS.analysis_timeout_seconds + interval_seconds + 15),
                )
                async for result in call:
                    yield (
                        json.dumps(
                            {"type": "result", "result": result_to_dict(result)}, ensure_ascii=False
                        )
                        + "\n"
                    )
            yield json.dumps({"type": "complete"}) + "\n"
        except grpc.aio.AioRpcError:
            yield (
                json.dumps(
                    {
                        "type": "error",
                        "detail": "Streaming interrompido. Confira os serviços; resultados anteriores permanecem na fila.",
                    }
                )
                + "\n"
            )
        finally:
            lock.release()

    return StreamingResponse(
        events(), media_type="application/x-ndjson", headers={"X-Accel-Buffering": "no"}
    )


# Lista resultados consumidos || List consumed results
@app.get("/api/history")
async def history(
    limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0)
):
    items, total = await asyncio.gather(
        asyncio.to_thread(read_results, limit, offset), asyncio.to_thread(count_results)
    )
    return {"items": items, "total": total, "offset": offset, "limit": limit}


# Confirma consumo pelo identificador || Confirm consumption by identifier
@app.get("/api/history/{analysis_id}")
async def history_item(analysis_id: UUID):
    result = await asyncio.to_thread(find_result, str(analysis_id))
    if result is None:
        raise HTTPException(404, "Resultado ainda não consumido")
    return result

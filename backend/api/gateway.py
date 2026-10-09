import asyncio
import json
import os
from contextlib import asynccontextmanager
from uuid import UUID

import grpc
import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.core.config import PROJECT_ROOT, SETTINGS
from backend.domain.contracts import result_to_dict, snapshot_to_message
from backend.domain.contracts import system_monitor_pb2_grpc as pb2_grpc
from backend.infrastructure.messaging import get_broker_status
from backend.infrastructure.process_icons import extract_icon
from backend.infrastructure.storage import (
    count_results,
    find_result,
    initialize_database,
    read_results,
)
from backend.services.collector import collect_snapshot
from backend.services.disks import collect_disks
from backend.services.processes import collect_processes, executable_for
from backend.services.runtime import runtime_info

FRONTEND_DIR = PROJECT_ROOT / "frontend" / "dist"


# Prepara recursos da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    app.state.analysis_lock = asyncio.Lock()
    app.state.icon_slots = asyncio.Semaphore(2)
    yield


app = FastAPI(title="Occhio API", version="2.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("OCCHIO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(","),
)
if (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


# Restringe mutações ao console local
@app.middleware("http")
async def local_requests(request: Request, call_next):
    if request.method == "POST":
        origin = request.headers.get("origin")
        allowed_origins = set(os.getenv("OCCHIO_ALLOWED_ORIGINS", "").split(",")) | {
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        }
        if origin and origin not in allowed_origins:
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


# Abre o console compilado
@app.get("/", include_in_schema=False)
async def home():
    if not (FRONTEND_DIR / "index.html").exists():
        raise HTTPException(503, "Compile o frontend: cd frontend && npm ci && npm run build")
    return FileResponse(FRONTEND_DIR / "index.html")


# Verifica o modelo local
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


# Verifica o transporte gRPC
async def check_grpc():
    try:
        async with grpc.aio.insecure_channel(SETTINGS.grpc_address) as channel:
            await asyncio.wait_for(channel.channel_ready(), timeout=2)
        return {"available": True}
    except (asyncio.TimeoutError, grpc.aio.AioRpcError):
        return {"available": False}


# Verifica o broker sem bloquear o loop
async def check_broker():
    try:
        return await asyncio.to_thread(get_broker_status)
    except Exception:
        return {"available": False, "consumers": 0, "queued_messages": 0, "failed_messages": 0}


# Consulta a prontidão do pipeline
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


# Coleta métricas do host
@app.get("/api/metrics")
async def metrics():
    return await asyncio.to_thread(collect_snapshot)


# Solicita uma análise unária
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


# Encaminha resultados à medida que chegam
@app.post("/api/analyze/stream")
async def analyze_stream(
    count: int = Query(default=3, ge=2, le=10),
    with_progress: bool = False,
    interval_seconds: float = Query(default=1, ge=0.5, le=5),
):
    lock = app.state.analysis_lock
    if lock.locked():
        raise HTTPException(409, "Já existe uma análise em andamento")
    await lock.acquire()

    # Produz coletas reais
    async def snapshots():
        for index in range(count):
            yield snapshot_to_message(await asyncio.to_thread(collect_snapshot))
            if index + 1 < count:
                await asyncio.sleep(interval_seconds)

    # Emite NDJSON para o navegador
    async def events():
        try:
            yield json.dumps({"type": "started", "count": count}) + "\n"
            async with grpc.aio.insecure_channel(SETTINGS.grpc_address) as channel:
                stub = pb2_grpc.SystemAnalysisStub(channel)
                method = stub.StreamProgress if with_progress else stub.StreamSnapshots
                call = method(
                    snapshots(),
                    timeout=count * (SETTINGS.analysis_timeout_seconds + interval_seconds + 15),
                )
                async for result in call:
                    if with_progress:
                        if not result.HasField("result"):
                            yield (
                                json.dumps(
                                    {
                                        "type": "progress",
                                        "stage": result.stage,
                                        "status": result.status,
                                    }
                                )
                                + "\n"
                            )
                            continue
                        result = result.result
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


# Lista resultados consumidos
@app.get("/api/history")
async def history(
    limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0)
):
    items, total = await asyncio.gather(
        asyncio.to_thread(read_results, limit, offset), asyncio.to_thread(count_results)
    )
    return {"items": items, "total": total, "offset": offset, "limit": limit}


# Confirma consumo pelo identificador
@app.get("/api/history/{analysis_id}")
async def history_item(analysis_id: UUID):
    result = await asyncio.to_thread(find_result, str(analysis_id))
    if result is None:
        raise HTTPException(404, "Resultado ainda não consumido")
    return result


@app.get("/api/runtime")
async def runtime():
    return await asyncio.to_thread(runtime_info)


@app.get("/api/processes")
async def processes():
    return await asyncio.to_thread(collect_processes)


@app.get("/api/process-icons/{icon_id}")
async def process_icon(icon_id: str):
    if len(icon_id) != 24 or any(c not in "0123456789abcdef" for c in icon_id):
        raise HTTPException(404, "Ícone indisponível")
    executable = executable_for(icon_id)
    async with app.state.icon_slots:
        data = await asyncio.to_thread(extract_icon, executable) if executable else None
    if data is None:
        return Response(status_code=204)
    return Response(data, media_type="image/png")


# Transmite etapas confirmadas e aguarda o consumidor
@app.post("/api/analyze/live")
async def analyze_live():
    lock = app.state.analysis_lock
    if lock.locked():
        raise HTTPException(409, "Já existe uma análise em andamento")
    await lock.acquire()

    def progress(stage, status):
        return json.dumps({"type": "progress", "stage": stage, "status": status}) + "\n"

    async def events():
        current = "collect"
        try:
            yield progress("collect", "running")
            snapshot = await asyncio.to_thread(collect_snapshot)
            yield progress("collect", "done")
            current = "grpc"
            yield progress(current, "running")
            result = None
            async with grpc.aio.insecure_channel(SETTINGS.grpc_address) as channel:
                call = pb2_grpc.SystemAnalysisStub(channel).AnalyzeProgress(
                    snapshot_to_message(snapshot), timeout=SETTINGS.analysis_timeout_seconds + 15
                )
                async for event in call:
                    if event.HasField("result"):
                        result = result_to_dict(event.result)
                        yield json.dumps({"type": "result", "result": result}) + "\n"
                    else:
                        current = event.stage
                        yield progress(event.stage, event.status)
            if result is None:
                raise RuntimeError("O serviço terminou sem resultado")
            current = "sqlite"
            yield progress(current, "running")
            for _ in range(20):
                saved = await asyncio.to_thread(find_result, result["analysis_id"])
                if saved:
                    yield progress(current, "done")
                    yield json.dumps({"type": "result", "result": saved}) + "\n"
                    break
                await asyncio.sleep(0.5)
            else:
                yield progress(current, "waiting")
            yield json.dumps({"type": "complete"}) + "\n"
        except (grpc.aio.AioRpcError, RuntimeError):
            yield progress(current, "error")
            yield (
                json.dumps(
                    {
                        "type": "error",
                        "detail": "Análise interrompida. Verifique os serviços na aba Pipeline.",
                    }
                )
                + "\n"
            )
        finally:
            lock.release()

    return StreamingResponse(
        events(), media_type="application/x-ndjson", headers={"X-Accel-Buffering": "no"}
    )


@app.get("/api/disks")
async def disks():
    return await asyncio.to_thread(collect_disks)

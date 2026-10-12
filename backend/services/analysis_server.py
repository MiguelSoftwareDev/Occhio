import asyncio
import logging
import time
import uuid
from contextlib import suppress
from datetime import datetime, timezone

import grpc
import httpx
from google.protobuf.json_format import MessageToDict
from pydantic import ValidationError

from backend.core.config import SETTINGS
from backend.domain.contracts import message_to_snapshot
from backend.domain.contracts import system_monitor_pb2 as pb2
from backend.domain.contracts import system_monitor_pb2_grpc as pb2_grpc
from backend.domain.models import Analysis, Snapshot
from backend.infrastructure.messaging import publish_result
from backend.infrastructure.ollama import PROMPT_VERSION, OllamaClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("occhio.analysis")


class SystemAnalysisService(pb2_grpc.SystemAnalysisServicer):
    # Prepara o serviço de análise
    def __init__(self) -> None:
        self.ollama = OllamaClient()

    # Analisa uma coleta
    async def AnalyzeSnapshot(self, request, context):
        return await self._analyze(request, context)

    # Analisa cada coleta do fluxo
    async def StreamSnapshots(self, request_iterator, context):
        async for request in request_iterator:
            yield await self._analyze(request, context)

    async def StreamProgress(self, request_iterator, context):
        async for request in request_iterator:
            yield pb2.ProgressEvent(stage="collect", status="done")
            yield pb2.ProgressEvent(stage="grpc", status="running")
            async for event in self.AnalyzeProgress(request, context):
                yield event

    # Emite eventos reais de inferência e publicação
    async def AnalyzeProgress(self, request, context):
        queue = asyncio.Queue()

        async def notify(stage, status):
            await queue.put(pb2.ProgressEvent(stage=stage, status=status))

        class ProgressFailure(Exception):
            def __init__(self, code, detail):
                self.code = code
                self.detail = detail

        class WorkerContext:
            async def abort(self, code, detail):
                raise ProgressFailure(code, detail)

        async def run():
            try:
                result = await self._analyze(request, WorkerContext(), notify)
                await queue.put(pb2.ProgressEvent(result=result))
            except ProgressFailure as error:
                await queue.put(error)
            except Exception:
                await queue.put(ProgressFailure(grpc.StatusCode.UNAVAILABLE, "Falha na análise"))
            finally:
                await queue.put(None)

        task = asyncio.create_task(run())
        try:
            while (event := await queue.get()) is not None:
                if isinstance(event, ProgressFailure):
                    await context.abort(event.code, event.detail)
                yield event
            await task
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    # Analisa e publica o resultado
    async def _analyze(self, request, context, notify=None):
        try:
            Snapshot.model_validate(message_to_snapshot(request))
        except ValidationError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Métricas inválidas")
        stage = "ollama"
        try:
            if notify:
                await notify("grpc", "done")
                await notify("ollama", "running")
            started = time.perf_counter()
            analysis_text = await self.ollama.analyze(message_to_snapshot(request))
            result = pb2.AnalysisResult(
                analysis_id=str(uuid.uuid4()),
                host_name=request.host_name,
                captured_at=request.captured_at,
                analyzed_at=datetime.now(timezone.utc).isoformat(),
                cpu_percent=request.cpu_percent,
                memory_percent=request.memory_percent,
                memory_used_bytes=request.memory_used_bytes,
                memory_total_bytes=request.memory_total_bytes,
                disk_percent=request.disk_percent,
                process_count=request.process_count,
                uptime_seconds=request.uptime_seconds,
                model=SETTINGS.ollama_model,
                analysis_text=analysis_text,
                inference_ms=(time.perf_counter() - started) * 1000,
                prompt_version=PROMPT_VERSION,
                top_processes=request.top_processes,
            )
            payload = MessageToDict(
                result, preserving_proto_field_name=True, always_print_fields_with_no_presence=True
            )
            Analysis.model_validate(payload)
            stage = "rabbitmq"
            if notify:
                await notify("ollama", "done")
                await notify("rabbitmq", "running")
            await asyncio.to_thread(publish_result, payload)
            if notify:
                await notify("rabbitmq", "done")
            logger.info("Resultado publicado: %s", result.analysis_id)
            return result
        except Exception as error:
            logger.exception("Falha na etapa %s", stage)
            if isinstance(error, httpx.TimeoutException):
                detail = (
                    "Ollama excedeu o tempo limite. Revise o modelo e ANALYSIS_TIMEOUT_SECONDS."
                )
            elif isinstance(error, httpx.ConnectError):
                detail = "Ollama indisponivel. Inicie o aplicativo ou execute ollama serve."
            elif isinstance(error, httpx.HTTPStatusError):
                detail = "Ollama recusou a solicitacao. Confira ollama list e OLLAMA_MODEL."
            else:
                detail = f"Falha na etapa {stage}. Consulte o terminal do servico gRPC."
            await context.abort(
                grpc.StatusCode.UNAVAILABLE,
                detail,
            )


# Inicia o servidor gRPC
async def serve() -> None:
    server = grpc.aio.server(maximum_concurrent_rpcs=2)
    pb2_grpc.add_SystemAnalysisServicer_to_server(SystemAnalysisService(), server)
    server.add_insecure_port(SETTINGS.grpc_address)
    await server.start()
    logger.info("gRPC ativo em %s", SETTINGS.grpc_address)
    try:
        await server.wait_for_termination()
    finally:
        await server.stop(grace=2)


if __name__ == "__main__":
    asyncio.run(serve())

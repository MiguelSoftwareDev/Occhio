import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone

import grpc
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
    # Prepara o serviço de análise || Set up the analysis service
    def __init__(self) -> None:
        self.ollama = OllamaClient()

    # Analisa uma coleta || Analyze one snapshot
    async def AnalyzeSnapshot(self, request, context):
        return await self._analyze(request, context)

    # Analisa cada coleta do fluxo || Analyze each streamed snapshot
    async def StreamSnapshots(self, request_iterator, context):
        async for request in request_iterator:
            yield await self._analyze(request, context)

    # Analisa e publica o resultado || Analyze and publish the result
    async def _analyze(self, request, context):
        try:
            Snapshot.model_validate(message_to_snapshot(request))
        except ValidationError:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Métricas inválidas")
        try:
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
            )
            payload = MessageToDict(
                result, preserving_proto_field_name=True, always_print_fields_with_no_presence=True
            )
            Analysis.model_validate(payload)
            await asyncio.to_thread(publish_result, payload)
            logger.info("Resultado publicado: %s", result.analysis_id)
            return result
        except Exception as error:
            logger.error("Falha na análise: %s", type(error).__name__)
            await context.abort(
                grpc.StatusCode.UNAVAILABLE,
                "Análise indisponível. Confira Ollama e RabbitMQ.",
            )


# Inicia o servidor gRPC || Start the gRPC server
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

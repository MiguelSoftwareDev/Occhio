import json
import sqlite3
from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest

from backend.domain.contracts import result_to_dict, snapshot_to_message
from backend.domain.contracts import system_monitor_pb2_grpc as rpc
from backend.infrastructure import messaging
from backend.services import analysis_server, consumer


# Exercita transporte gRPC real com integrações isoladas
@pytest.mark.asyncio
async def test_unary_stream_and_zero_values(snapshot, monkeypatch):
    published = []
    monkeypatch.setattr(
        analysis_server.OllamaClient, "analyze", AsyncMock(return_value="CPU em 0%.")
    )
    monkeypatch.setattr(analysis_server, "publish_result", published.append)
    server = grpc.aio.server()
    rpc.add_SystemAnalysisServicer_to_server(analysis_server.SystemAnalysisService(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    try:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
            stub = rpc.SystemAnalysisStub(channel)
            result = await stub.AnalyzeSnapshot(snapshot_to_message(snapshot), timeout=5)
            assert result_to_dict(result)["cpu_percent"] == 0

            # Produz duas amostras
            async def requests():
                for _ in range(2):
                    yield snapshot_to_message(snapshot)

            results = [item async for item in stub.StreamSnapshots(requests(), timeout=5)]
            assert len(results) == 2
            assert len(published) == 3
            assert len({item["analysis_id"] for item in published}) == 3
            with pytest.raises(grpc.aio.AioRpcError) as error:
                await stub.AnalyzeSnapshot(
                    snapshot_to_message({**snapshot, "cpu_percent": 200}), timeout=5
                )
            assert error.value.code() == grpc.StatusCode.INVALID_ARGUMENT
            assert len(published) == 3
    finally:
        await server.stop(0)


# Falha de publicação não retorna sucesso
@pytest.mark.asyncio
async def test_publish_failure(snapshot, monkeypatch):
    monkeypatch.setattr(analysis_server.OllamaClient, "analyze", AsyncMock(return_value="OK"))
    monkeypatch.setattr(
        analysis_server, "publish_result", MagicMock(side_effect=RuntimeError("broker"))
    )
    service = analysis_server.SystemAnalysisService()
    context = MagicMock()
    context.abort = AsyncMock(side_effect=RuntimeError("aborted"))
    with pytest.raises(RuntimeError, match="aborted"):
        await service.AnalyzeSnapshot(snapshot_to_message(snapshot), context)
    assert context.abort.call_args.args[0] == grpc.StatusCode.UNAVAILABLE


# Confirma depois de persistir
def test_consumer_ack(database, analysis):
    channel = MagicMock()
    method = MagicMock()
    props = MagicMock()
    consumer.handle_message(channel, method, props, json.dumps(analysis).encode())
    assert database.count_results() == 1
    channel.basic_ack.assert_called_once_with(delivery_tag=method.delivery_tag)
    channel.basic_nack.assert_not_called()


# Mensagem inválida segue para fila de falhas
def test_consumer_dead_letter():
    channel = MagicMock()
    method = MagicMock()
    consumer.handle_message(channel, method, MagicMock(), b"not-json")
    channel.basic_nack.assert_called_once_with(delivery_tag=method.delivery_tag, requeue=False)
    channel.basic_ack.assert_not_called()


# Falha no banco mantém mensagem sem ACK
def test_database_failure(monkeypatch, analysis):
    monkeypatch.setattr(
        consumer, "save_result", MagicMock(side_effect=sqlite3.OperationalError("locked"))
    )
    channel = MagicMock()
    with pytest.raises(sqlite3.OperationalError):
        consumer.handle_message(channel, MagicMock(), MagicMock(), json.dumps(analysis).encode())
    channel.basic_ack.assert_not_called()
    channel.basic_nack.assert_not_called()


# O retorno vazio do Pika não é falha
def test_publisher_confirmation(monkeypatch, analysis):
    connection = MagicMock()
    channel = connection.channel.return_value
    channel.basic_publish.return_value = None
    monkeypatch.setattr(messaging, "open_connection", lambda: connection)
    messaging.publish_result(analysis)
    channel.confirm_delivery.assert_called_once()
    assert channel.basic_publish.call_args.kwargs["mandatory"] is True
    assert channel.basic_publish.call_args.kwargs["properties"].delivery_mode == 2
    connection.close.assert_called_once()

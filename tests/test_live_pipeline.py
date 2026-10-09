import json
from unittest.mock import AsyncMock, MagicMock

import grpc
import pytest
from fastapi.testclient import TestClient

from backend.api import gateway
from backend.domain.contracts import snapshot_to_message
from backend.domain.contracts import system_monitor_pb2 as pb
from backend.domain.contracts import system_monitor_pb2_grpc as rpc
from backend.services import analysis_server


@pytest.mark.asyncio
@pytest.mark.parametrize("fail_publish", [False, True])
async def test_progress_requires_broker_confirmation(snapshot, monkeypatch, fail_publish):
    monkeypatch.setattr(
        analysis_server.OllamaClient, "analyze", AsyncMock(return_value="CPU estável")
    )
    publish = MagicMock(side_effect=RuntimeError("offline") if fail_publish else None)
    monkeypatch.setattr(analysis_server, "publish_result", publish)
    server = grpc.aio.server()
    rpc.add_SystemAnalysisServicer_to_server(analysis_server.SystemAnalysisService(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    events = []
    try:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
            try:
                async for event in rpc.SystemAnalysisStub(channel).AnalyzeProgress(
                    snapshot_to_message(snapshot), timeout=5
                ):
                    events.append(event)
            except grpc.aio.AioRpcError as error:
                assert fail_publish
                assert error.code() == grpc.StatusCode.UNAVAILABLE
        assert [(e.stage, e.status) for e in events[:4]] == [
            ("grpc", "done"),
            ("ollama", "running"),
            ("ollama", "done"),
            ("rabbitmq", "running"),
        ]
        if fail_publish:
            assert not any(e.HasField("result") for e in events)
            assert not any(e.stage == "rabbitmq" and e.status == "done" for e in events)
        else:
            assert events[-2].stage == "rabbitmq" and events[-2].status == "done"
            assert events[-1].HasField("result")
        publish.assert_called_once()
    finally:
        await server.stop(0)


def test_live_api_waits_for_storage(database, analysis, monkeypatch):
    class Stub:
        def __init__(self, channel):
            pass

        async def AnalyzeProgress(self, snapshot, timeout):
            for stage, status in [
                ("grpc", "done"),
                ("ollama", "running"),
                ("ollama", "done"),
                ("rabbitmq", "running"),
                ("rabbitmq", "done"),
            ]:
                yield pb.ProgressEvent(stage=stage, status=status)
            database.save_result(analysis)
            yield pb.ProgressEvent(result=pb.AnalysisResult(**analysis))

    monkeypatch.setattr(gateway.pb2_grpc, "SystemAnalysisStub", Stub)
    with TestClient(gateway.app) as client:
        response = client.post("/api/analyze/live")
        events = [json.loads(line) for line in response.text.splitlines()]
        assert events[0] == {"type": "progress", "stage": "collect", "status": "running"}
        assert events[-3] == {"type": "progress", "stage": "sqlite", "status": "done"}
        assert events[-2]["result"]["consumed_at"]
        assert events[-1] == {"type": "complete"}
        assert not gateway.app.state.analysis_lock.locked()
        client.portal.call(gateway.app.state.analysis_lock.acquire)
        try:
            assert client.post("/api/analyze/live").status_code == 409
        finally:
            gateway.app.state.analysis_lock.release()


@pytest.mark.asyncio
async def test_bidirectional_progress_preserves_snapshot_order(snapshot, monkeypatch):
    monkeypatch.setattr(
        analysis_server.OllamaClient, "analyze", AsyncMock(return_value="CPU estável")
    )
    publisher = MagicMock()
    monkeypatch.setattr(analysis_server, "publish_result", publisher)
    server = grpc.aio.server()
    rpc.add_SystemAnalysisServicer_to_server(analysis_server.SystemAnalysisService(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()

    async def inputs():
        for cpu in (20, 80):
            yield snapshot_to_message({**snapshot, "cpu_percent": cpu})

    try:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
            events = [
                event
                async for event in rpc.SystemAnalysisStub(channel).StreamProgress(
                    inputs(), timeout=5
                )
            ]
        results = [e.result for e in events if e.HasField("result")]
        assert [r.cpu_percent for r in results] == [20, 80]
        assert sum(e.stage == "collect" for e in events) == 2
        assert publisher.call_count == 2
        first_result = next(i for i, e in enumerate(events) if e.HasField("result"))
        assert events[first_result + 1].stage == "collect"
    finally:
        await server.stop(0)

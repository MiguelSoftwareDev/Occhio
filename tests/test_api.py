from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.api import gateway


# Valida histórico, limites e proteção de origem
def test_api(database, analysis):
    database.save_result(analysis)
    with TestClient(gateway.app) as client:
        assert client.get("/api/history").json()["total"] == 1
        assert client.get(f"/api/history/{analysis['analysis_id']}").json()["consumed_at"]
        assert client.get("/api/history?limit=101").status_code == 422
        assert client.post("/api/analyze/stream?count=1").status_code == 422
        assert (
            client.post(
                "/api/analyze/once", headers={"Origin": "https://external.example"}
            ).status_code
            == 403
        )
        assert client.get("/api/metrics", headers={"Host": "evil.example"}).status_code == 400
        assert client.get("/").status_code == 200
        assert client.get("/api/metrics").json()["memory_total_bytes"] > 0


# Verifica prontidão com modelo ausente
def test_missing_model(database, monkeypatch):
    monkeypatch.setattr(
        gateway,
        "check_ollama",
        AsyncMock(return_value={"available": True, "model_available": False}),
    )
    monkeypatch.setattr(gateway, "check_grpc", AsyncMock(return_value={"available": True}))
    monkeypatch.setattr(
        gateway, "check_broker", AsyncMock(return_value={"available": True, "consumers": 1})
    )
    with TestClient(gateway.app) as client:
        assert client.get("/api/health").json()["ok"] is False


# Impede inferências sobrepostas pelo console
def test_busy_pipeline(database):
    with TestClient(gateway.app) as client:
        client.portal.call(gateway.app.state.analysis_lock.acquire)
        try:
            assert client.post("/api/analyze/once").status_code == 409
            assert client.post("/api/analyze/stream").status_code == 409
        finally:
            gateway.app.state.analysis_lock.release()

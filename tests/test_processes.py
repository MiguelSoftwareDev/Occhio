from contextlib import nullcontext
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.api import gateway
from backend.services import processes, runtime


def test_sampling_primes_cpu_and_tracks_only_observed_executables(monkeypatch):
    class FakeProcess:
        pid = 42

        def oneshot(self):
            return nullcontext()

        def create_time(self):
            return 123.0

        def cpu_percent(self, interval):
            return 80.0

        def name(self):
            return "real-app.exe"

        def memory_info(self):
            return SimpleNamespace(rss=200)

        def exe(self):
            return "C:/Apps/real-app.exe"

    monkeypatch.setattr(processes, "_previous", set())
    monkeypatch.setattr(processes, "_cache", {})
    monkeypatch.setattr(processes, "_executables", {})
    monkeypatch.setattr(processes.psutil, "process_iter", lambda: [FakeProcess()])
    monkeypatch.setattr(processes.psutil, "cpu_count", lambda: 4)
    monkeypatch.setattr(processes.psutil, "virtual_memory", lambda: SimpleNamespace(total=1000))
    first = processes.collect_processes()["items"][0]
    assert first["cpu_percent"] is None
    monkeypatch.setattr(processes, "_sampled", -100)
    second = processes.collect_processes()["items"][0]
    assert second["cpu_percent"] == 20
    assert second["memory_percent"] == 20
    assert second["name"] == "real-app.exe"
    assert "C:/" not in str(second)
    assert processes.executable_for(second["icon_url"].split("/")[-1]) == "C:/Apps/real-app.exe"
    assert processes.executable_for("C:/Windows/secrets.txt") is None


def test_runtime_and_unknown_icon(database, monkeypatch):
    monkeypatch.setattr(runtime.socket, "gethostname", lambda: "monitor-server-02")
    monkeypatch.setenv("OCCHIO_ENVIRONMENT", "Servidor de testes")
    with TestClient(gateway.app) as client:
        result = client.get("/api/runtime").json()
        assert result["host_name"] == "monitor-server-02"
        assert result["environment"] == "Servidor de testes"
        assert client.get("/api/process-icons/not-a-valid-icon").status_code == 404
        assert client.get("/api/process-icons/000000000000000000000000").status_code == 204

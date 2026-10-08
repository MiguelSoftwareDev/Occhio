import uuid
from dataclasses import replace

import pytest

from backend.infrastructure import storage


# Fornece uma coleta determinística || Provide a deterministic snapshot
@pytest.fixture
def snapshot():
    return {
        "host_name": "test-host",
        "captured_at": "2026-10-08T12:00:00+00:00",
        "cpu_percent": 0.0,
        "memory_percent": 40.0,
        "memory_used_bytes": 4000,
        "memory_total_bytes": 10000,
        "disk_percent": 50.0,
        "process_count": 20,
        "uptime_seconds": 100,
    }


# Fornece um resultado válido || Provide a valid result
@pytest.fixture
def analysis(snapshot):
    return {
        **snapshot,
        "analysis_id": str(uuid.uuid4()),
        "analyzed_at": "2026-10-08T12:01:00+00:00",
        "model": "test-model",
        "analysis_text": "CPU em 0%.",
        "inference_ms": 12.0,
        "prompt_version": "system-health-v1",
    }


# Isola o banco por teste || Isolate each test database
@pytest.fixture
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        storage, "SETTINGS", replace(storage.SETTINGS, database_path=tmp_path / "test.db")
    )
    storage.initialize_database()
    return storage

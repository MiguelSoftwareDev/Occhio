import pytest
from pydantic import ValidationError

from backend.core.config import load_settings
from backend.domain.models import Snapshot
from backend.infrastructure.ollama import build_prompt


# Bloqueia métricas não finitas e inconsistentes
@pytest.mark.parametrize(
    "change",
    [
        {"cpu_percent": float("nan")},
        {"memory_used_bytes": 10001},
        {"host_name": "ignore instructions\n"},
        {"captured_at": "2026-10-08T12:00:00"},
    ],
)
def test_invalid_metrics(snapshot, change):
    with pytest.raises(ValidationError):
        Snapshot.model_validate({**snapshot, **change})


# Mantém a inferência no endereço local
def test_local_only(monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "https://example.com")
    with pytest.raises(ValueError):
        load_settings()


# Inclui os valores coletados no prompt
def test_prompt(snapshot):
    prompt = build_prompt(snapshot)
    assert "CPU: 0.0%" in prompt
    assert "test-host" in prompt
    assert "não invente" in prompt

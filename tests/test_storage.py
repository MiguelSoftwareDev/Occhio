import pytest
from pydantic import ValidationError


# Mantém uma gravação por evento || Keep one row per event
def test_idempotent_delivery(database, analysis):
    database.save_result(analysis)
    first = database.read_results()[0]
    database.save_result({**analysis, "analysis_text": "Duplicata"})
    assert database.count_results() == 1
    assert database.find_result(analysis["analysis_id"]) == first
    assert first["consumed_at"]
    assert first["analysis_text"] == analysis["analysis_text"]


# Impede gravação de payload inválido || Reject invalid payloads
def test_rejects_invalid_event(database, analysis):
    with pytest.raises(ValidationError):
        database.save_result({**analysis, "cpu_percent": 101})
    assert database.count_results() == 0


# Aplica limite e deslocamento || Apply limit and offset
def test_pagination(database, analysis):
    import uuid

    for _ in range(4):
        database.save_result({**analysis, "analysis_id": str(uuid.uuid4())})
    assert len(database.read_results(2, 2)) == 2
    assert database.read_results(2, 4) == []

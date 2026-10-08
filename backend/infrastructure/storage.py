import json
import sqlite3
from datetime import datetime, timezone

from backend.core.config import SETTINGS
from backend.domain.models import Analysis


# Abre o banco com espera por bloqueio || Open the database with a busy timeout
def connect():
    return sqlite3.connect(SETTINGS.database_path, timeout=10)


# Prepara a persistência local || Prepare local persistence
def initialize_database() -> None:
    SETTINGS.database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS analyses (analysis_id TEXT PRIMARY KEY, analyzed_at TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_time ON analyses(analyzed_at DESC)"
        )


# Persiste uma vez por identificador || Persist once per identifier
def save_result(result: dict) -> None:
    validated = Analysis.model_validate(result).model_dump(mode="json")
    validated["consumed_at"] = datetime.now(timezone.utc).isoformat()
    with connect() as connection:
        connection.execute(
            "INSERT INTO analyses (analysis_id, analyzed_at, payload) VALUES (?, ?, ?) ON CONFLICT(analysis_id) DO NOTHING",
            (
                validated["analysis_id"],
                validated["analyzed_at"],
                json.dumps(validated, ensure_ascii=False),
            ),
        )


# Lê o histórico com paginação || Read paginated history
def read_results(limit: int = 20, offset: int = 0) -> list[dict]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT payload FROM analyses ORDER BY analyzed_at DESC, analysis_id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [json.loads(row[0]) for row in rows]


# Localiza um resultado consumido || Find a consumed result
def find_result(analysis_id: str) -> dict | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT payload FROM analyses WHERE analysis_id = ?", (analysis_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


# Conta resultados persistidos || Count persisted results
def count_results() -> int:
    with connect() as connection:
        return connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]

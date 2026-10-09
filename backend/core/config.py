import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    ollama_url: str
    ollama_model: str
    grpc_address: str
    rabbitmq_url: str
    database_path: Path
    analysis_timeout_seconds: float


# Carrega as configurações locais
def load_settings() -> Settings:
    database_path = Path(os.getenv("DATABASE_PATH", "data/occhio.db")).expanduser()
    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path
    ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    if urlparse(ollama_url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("OLLAMA_URL deve apontar para este computador.")

    timeout = float(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "120"))
    if not 5 <= timeout <= 600:
        raise ValueError("ANALYSIS_TIMEOUT_SECONDS deve estar entre 5 e 600")
    return Settings(
        ollama_url=ollama_url,
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:1.7b"),
        grpc_address=os.getenv("GRPC_ADDRESS", "127.0.0.1:50051"),
        rabbitmq_url=os.getenv(
            "RABBITMQ_URL",
            "amqp://occhio:occhio_demo@127.0.0.1:5672/",
        ),
        database_path=database_path,
        analysis_timeout_seconds=timeout,
    )


SETTINGS = load_settings()

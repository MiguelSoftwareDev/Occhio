from urllib.parse import urlparse

import httpx

from backend.core.config import SETTINGS

PROMPT_VERSION = "system-health-v1"


# Monta o pedido de análise || Build the analysis prompt
def build_prompt(snapshot: dict) -> str:
    memory_gib = snapshot["memory_used_bytes"] / (1024**3)
    total_gib = snapshot["memory_total_bytes"] / (1024**3)
    return (
        "Analise os indicadores reais do computador abaixo e responda em português. "
        "Descreva o que está normal, o que merece atenção e uma ação simples se houver "
        "um risco claro. Use somente os valores fornecidos. Diferencie observação de "
        "hipótese e não invente a causa de um pico.\n\n"
        f"Computador: {snapshot['host_name']}\n"
        f"Coleta: {snapshot['captured_at']}\n"
        f"CPU: {snapshot['cpu_percent']:.1f}%\n"
        f"Memória: {snapshot['memory_percent']:.1f}% "
        f"({memory_gib:.2f} de {total_gib:.2f} GiB)\n"
        f"Disco: {snapshot['disk_percent']:.1f}%\n"
        f"Processos ativos: {snapshot['process_count']}\n"
        f"Tempo ligado: {snapshot['uptime_seconds']} segundos"
    )


class OllamaClient:
    # Valida o endereço local do Ollama || Validate the local Ollama address
    def __init__(self) -> None:
        hostname = urlparse(SETTINGS.ollama_url).hostname
        if hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("O Ollama deve usar um endereço local.")
        self.url = SETTINGS.ollama_url + "/api/generate"
        self.model = SETTINGS.ollama_model

    # Solicita a análise ao modelo local || Request analysis from the local model
    async def analyze(self, snapshot: dict) -> str:
        async with httpx.AsyncClient(
            timeout=SETTINGS.analysis_timeout_seconds, trust_env=False, follow_redirects=False
        ) as client:
            response = await client.post(
                self.url,
                json={
                    "model": self.model,
                    "prompt": build_prompt(snapshot),
                    "stream": False,
                    "think": False,
                    "options": {"temperature": 0.2, "num_predict": 700},
                },
            )
        response.raise_for_status()
        analysis = response.json().get("response", "").strip()
        if not analysis:
            raise RuntimeError("O Ollama retornou uma análise vazia.")
        return analysis

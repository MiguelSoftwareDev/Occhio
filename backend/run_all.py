import os
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
PROCESSES = [
    ("gRPC", [sys.executable, "-m", "backend.services.analysis_server"]),
    ("Consumidor", [sys.executable, "-m", "backend.services.consumer"]),
    (
        "Web",
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.api.gateway:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
    ),
]


# Exibe a saída de cada processo || Show each process output
def print_output(name: str, process: subprocess.Popen) -> None:
    for line in process.stdout:
        print(f"[{name}] {line}", end="", flush=True)


# Inicia os serviços locais || Start local services
def run() -> None:
    generated_dir = PROJECT_ROOT / "backend" / "generated"
    generated_files = [
        generated_dir / "system_monitor_pb2.py",
        generated_dir / "system_monitor_pb2_grpc.py",
    ]
    if not all(path.exists() for path in generated_files):
        from backend.generate_proto import generate

        generate()

    environment = os.environ.copy()
    environment["PYTHONUNBUFFERED"] = "1"
    children = []
    try:
        for name, command in PROCESSES:
            process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            children.append((name, process))
            threading.Thread(
                target=print_output,
                args=(name, process),
                daemon=True,
            ).start()

        print("Occhio ativo em http://127.0.0.1:8000. Pressione Ctrl+C para encerrar.")
        while True:
            for name, process in children:
                code = process.poll()
                if code is not None:
                    raise RuntimeError(f"O processo {name} encerrou com código {code}.")
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\nEncerrando os serviços.")
    finally:
        for _, process in children:
            if process.poll() is None:
                process.terminate()
        for _, process in children:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    run()

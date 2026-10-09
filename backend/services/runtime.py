import os
import platform
import socket
from pathlib import Path


# Identifica o ambiente do coletor
def runtime_info() -> dict:
    system = platform.system()
    release = platform.release()
    if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists():
        kind = "Contêiner"
    elif "microsoft" in release.lower() or os.getenv("WSL_DISTRO_NAME"):
        kind = "WSL"
    else:
        kind = system
    return {
        "host_name": socket.gethostname(),
        "os": system,
        "os_release": release,
        "environment": os.getenv("OCCHIO_ENVIRONMENT") or kind,
        "scope": "Métricas da máquina que executa o coletor",
    }

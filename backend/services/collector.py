import socket
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


# Coleta métricas reais do computador || Collect real computer metrics
def collect_snapshot() -> dict:
    memory = psutil.virtual_memory()
    disk_path = Path.home().anchor or "/"
    disk = psutil.disk_usage(disk_path)
    return {
        "host_name": socket.gethostname(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": memory.percent,
        "memory_used_bytes": memory.used,
        "memory_total_bytes": memory.total,
        "disk_percent": disk.percent,
        "process_count": len(psutil.pids()),
        "uptime_seconds": max(0, int(time.time() - psutil.boot_time())),
    }

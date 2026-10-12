import socket
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from backend.services.processes import collect_processes


# Coleta métricas reais do computador
def collect_snapshot() -> dict:
    memory = psutil.virtual_memory()
    disk_path = Path.home().anchor or "/"
    disk = psutil.disk_usage(disk_path)
    processes = collect_processes()["items"]
    leaders = sorted(processes, key=lambda p: p["memory_bytes"], reverse=True)[:5]
    for item in sorted(processes, key=lambda p: p["cpu_percent"] or 0, reverse=True)[:5]:
        if item not in leaders:
            leaders.append(item)
    return {
        "host_name": socket.gethostname(),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": memory.percent,
        "memory_used_bytes": memory.total - memory.available,
        "memory_total_bytes": memory.total,
        "disk_percent": disk.percent,
        "process_count": len(psutil.pids()),
        "uptime_seconds": max(0, int(time.time() - psutil.boot_time())),
        "top_processes": [
            {
                "pid": p["pid"],
                "name": p["name"][:512],
                "cpu_percent": p["cpu_percent"] or 0,
                "cpu_measured": p["cpu_percent"] is not None,
                "memory_bytes": p["memory_bytes"],
                "memory_percent": p["memory_percent"],
            }
            for p in leaders
        ],
    }

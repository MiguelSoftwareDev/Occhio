"""Process sampling and executable identities; paths never come from HTTP clients."""

import hashlib
import threading
import time
from datetime import datetime, timezone

import psutil

_lock = threading.Lock()
_previous: set[tuple[int, float]] = set()
_cache: dict = {}
_sampled = 0.0
_executables: dict[str, str] = {}


# Resolve apenas executáveis observados
def executable_for(icon_id: str) -> str | None:
    with _lock:
        return _executables.get(icon_id)


# Amostra CPU por intervalo e RSS real
def collect_processes() -> dict:
    global _previous, _cache, _sampled
    with _lock:
        now = time.monotonic()
        if _cache and now - _sampled < 2:
            return _cache
        seen = set()
        items = []
        denied = 0
        cores = psutil.cpu_count() or 1
        total = psutil.virtual_memory().total
        executables = {}
        for process in psutil.process_iter():
            try:
                with process.oneshot():
                    identity = (process.pid, process.create_time())
                    seen.add(identity)
                    cpu = process.cpu_percent(None)
                    name = process.name() or str(process.pid)
                    rss = process.memory_info().rss
                    try:
                        executable = process.exe()
                    except (psutil.AccessDenied, psutil.ZombieProcess):
                        executable = ""
                icon_id = (
                    hashlib.sha256(executable.encode()).hexdigest()[:24] if executable else None
                )
                if icon_id:
                    executables[icon_id] = executable
                items.append(
                    {
                        "pid": process.pid,
                        "name": name,
                        "started_at": identity[1],
                        "cpu_percent": min(100, round(cpu / cores, 1))
                        if identity in _previous
                        else None,
                        "memory_bytes": rss,
                        "memory_percent": round(rss / total * 100, 2),
                        "icon_url": f"/api/process-icons/{icon_id}" if icon_id else None,
                    }
                )
            except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.AccessDenied):
                denied += 1
        _previous = seen
        _executables.clear()
        _executables.update(executables)
        _sampled = now
        _cache = {
            "items": items,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "inaccessible": denied,
            "cpu_basis": "machine",
            "memory_basis": "rss",
        }
        return _cache

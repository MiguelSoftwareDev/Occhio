"""Mounted storage volumes visible to the collector, including secondary drives."""

import psutil


def collect_disks() -> dict:
    volumes = []
    seen = set()
    for partition in psutil.disk_partitions(all=False):
        if not partition.fstype or "cdrom" in partition.opts:
            continue
        key = (partition.device, partition.mountpoint)
        if key in seen:
            continue
        seen.add(key)
        volume = {
            "device": partition.device,
            "mountpoint": partition.mountpoint,
            "filesystem": partition.fstype,
            "available": False,
        }
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            volume.update(
                available=True,
                total_bytes=usage.total,
                used_bytes=usage.used,
                free_bytes=usage.free,
                percent=usage.percent,
            )
        except (OSError, PermissionError):
            volume["error"] = "Volume indisponível ou sem permissão de leitura"
        volumes.append(volume)
    return {"volumes": volumes}

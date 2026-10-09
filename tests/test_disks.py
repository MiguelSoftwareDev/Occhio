from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.api.gateway import app
from backend.services import disks


def test_secondary_volumes_and_unavailable_media(monkeypatch, database):
    partitions = [
        SimpleNamespace(device=d, mountpoint=m, fstype="NTFS", opts="rw")
        for d, m in [("disk0", "C:\\"), ("disk1", "D:\\"), ("disk2", "E:\\"), ("disk1", "D:\\")]
    ]
    monkeypatch.setattr(disks.psutil, "disk_partitions", lambda all: partitions)

    def usage(path):
        if path == "E:\\":
            raise PermissionError("denied")
        return SimpleNamespace(total=1000, used=400, free=600, percent=40)

    monkeypatch.setattr(disks.psutil, "disk_usage", usage)
    with TestClient(app) as client:
        data = client.get("/api/disks").json()["volumes"]
    assert len(data) == 3
    assert data[1]["mountpoint"] == "D:\\"
    assert data[1]["total_bytes"] == 1000
    assert data[2]["available"] is False
    assert "total_bytes" not in data[2]

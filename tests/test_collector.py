import unittest
from unittest.mock import patch

from backend.services.collector import collect_snapshot


class CollectorTests(unittest.TestCase):
    # Confere o formato das métricas coletadas || Check the collected metric format
    @patch("backend.services.collector.psutil.boot_time", return_value=1000)
    @patch("backend.services.collector.time.time", return_value=1600)
    @patch("backend.services.collector.psutil.pids", return_value=[1, 2, 3])
    @patch("backend.services.collector.psutil.disk_usage")
    @patch("backend.services.collector.psutil.cpu_percent", return_value=25.0)
    @patch("backend.services.collector.psutil.virtual_memory")
    def test_snapshot_has_metric_fields(
        self,
        memory,
        cpu,
        disk,
        pids,
        clock,
        boot_time,
    ):
        memory.return_value = type(
            "Memory",
            (),
            {"percent": 40.0, "used": 4_000, "total": 10_000},
        )()
        disk.return_value = type("Disk", (), {"percent": 55.0})()

        snapshot = collect_snapshot()

        self.assertEqual(snapshot["cpu_percent"], 25.0)
        self.assertEqual(snapshot["memory_percent"], 40.0)
        self.assertEqual(snapshot["disk_percent"], 55.0)
        self.assertEqual(snapshot["process_count"], 3)
        self.assertEqual(snapshot["uptime_seconds"], 600)
        self.assertTrue(snapshot["host_name"])
        self.assertTrue(snapshot["captured_at"])
        cpu.assert_called_once_with(interval=0.5)


if __name__ == "__main__":
    unittest.main()

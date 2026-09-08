from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil

from ..models import HostMetrics, SchemaError
from .base import ReadOnlyAdapter


def _get_loadavg() -> tuple[float, float, float]:
    if hasattr(os, "getloadavg"):
        return os.getloadavg()
    if hasattr(psutil, "getloadavg"):
        return psutil.getloadavg()
    raise RuntimeError("Host load average is unavailable on this platform")


class ProcessMetricsAdapter(ReadOnlyAdapter[HostMetrics]):
    """Read host metrics only; no hostname, command line, environment, or path is retained."""

    def __init__(self, disk_path: str | Path):
        self.disk_path = Path(disk_path)

    def read(self) -> HostMetrics:
        if not self.disk_path.exists():
            raise SchemaError("configured metrics path is unavailable")
        load = _get_loadavg()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.disk_path))
        raw = {
            "load_1m": float(load[0]), "load_5m": float(load[1]), "load_15m": float(load[2]),
            "memory_free_bytes": int(memory.available), "disk_free_bytes": int(disk.free),
            "cpu_count": int(psutil.cpu_count() or 0), "uptime_seconds": int(time.time() - psutil.boot_time()),
            "gpu_memory_used_bytes": None, "gpu_memory_total_bytes": None,
            "measurement_status": "measured", "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        return HostMetrics.from_dict(raw)


def configured_process_presence(public_id_to_pid: dict[str, int]) -> dict[str, bool]:
    """Report presence for explicitly configured PIDs without reading their command lines."""
    result = {}
    for public_id, pid in public_id_to_pid.items():
        if not isinstance(public_id, str) or isinstance(pid, bool) or not isinstance(pid, int) or pid < 1:
            raise SchemaError("invalid configured process observation")
        result[public_id] = psutil.pid_exists(pid)
    return result

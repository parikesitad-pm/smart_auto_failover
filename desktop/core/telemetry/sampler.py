"""
AutoFailover 3.0 Core - Telemetry Sampler (Passive 1 Hz)
Author: parikesitad-pm
© 2026
"""

import time
from typing import Optional
from ...models.telemetry import DeviceHealth


class TelemetrySampler:
    """
    Samples CPU and RAM passively at ~1 Hz.
    Uses psutil if installed, or native /proc parsing on Linux (zero dependency).
    MUST NOT independently trigger network failover.
    """

    def __init__(self):
        self._prev_cpu_total: Optional[float] = None
        self._prev_cpu_idle: Optional[float] = None

    def sample(self) -> DeviceHealth:
        # 1. Try psutil if available
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            pressure = "nominal"
            if cpu > 85.0 or mem.percent > 90.0:
                pressure = "critical"
            elif cpu > 60.0 or mem.percent > 75.0:
                pressure = "moderate"

            return DeviceHealth(
                cpu_percent=round(cpu, 1),
                ram_used_mb=round(mem.used / (1024 * 1024), 1),
                ram_total_mb=round(mem.total / (1024 * 1024), 1),
                ram_percent=round(mem.percent, 1),
                pressure=pressure,
                timestamp=time.time(),
            )
        except ImportError:
            pass

        # 2. Native Linux /proc fallback
        return self._sample_linux_proc()

    def _sample_linux_proc(self) -> DeviceHealth:
        cpu_pct = 0.0
        try:
            with open("/proc/stat", "r") as f:
                fields = f.readline().strip().split()[1:]
                vals = [float(v) for v in fields]
                idle = vals[3] + vals[4]
                total = sum(vals)

                if self._prev_cpu_total is not None:
                    d_total = total - self._prev_cpu_total
                    d_idle = idle - self._prev_cpu_idle
                    if d_total > 0:
                        cpu_pct = max(0.0, min(100.0, (1.0 - (d_idle / d_total)) * 100.0))

                self._prev_cpu_total = total
                self._prev_cpu_idle = idle
        except Exception:
            pass

        ram_total = 16384.0
        ram_avail = 8192.0
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        ram_total = float(line.split()[1]) / 1024.0  # MB
                    elif line.startswith("MemAvailable:"):
                        ram_avail = float(line.split()[1]) / 1024.0  # MB
        except Exception:
            pass

        ram_used = max(0.0, ram_total - ram_avail)
        ram_pct = (ram_used / ram_total) * 100.0 if ram_total > 0 else 0.0

        pressure = "nominal"
        if cpu_pct > 85.0 or ram_pct > 90.0:
            pressure = "critical"
        elif cpu_pct > 60.0 or ram_pct > 75.0:
            pressure = "moderate"

        return DeviceHealth(
            cpu_percent=round(cpu_pct, 1),
            ram_used_mb=round(ram_used, 1),
            ram_total_mb=round(ram_total, 1),
            ram_percent=round(ram_pct, 1),
            pressure=pressure,
            timestamp=time.time(),
        )

"""
AutoFailover 3.0 Core - Ookla Speedtest Provider Adapter
Author: parikesitad-pm
© 2026

Official Ookla CLI / Speedtest adapter.
"""

import time
import json
import shutil
import subprocess
from typing import Optional, Callable
from .base import BaseSpeedTestProvider, SpeedTestResult


class OoklaSpeedTestProvider(BaseSpeedTestProvider):
    """
    Ookla Speedtest Adapter using official Ookla CLI / speedtest-cli binaries.
    """

    @property
    def name(self) -> str:
        return "ookla"

    @property
    def display_name(self) -> str:
        return "Ookla Speedtest"

    def run_benchmark(
        self,
        interface: str = "default",
        source_ip: Optional[str] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> SpeedTestResult:
        t0 = time.time()
        res = SpeedTestResult(
            provider=self.name,
            interface=interface,
            timestamp=t0,
            status="RUNNING",
        )

        if cancel_check and cancel_check():
            res.status = "CANCELLED"
            res.duration = time.time() - t0
            return res

        # 1. Detect official Ookla CLI
        ookla_cli = shutil.which("speedtest")
        python_cli = shutil.which("speedtest-cli")

        if not ookla_cli and not python_cli:
            res.status = "UNAVAILABLE"
            res.error = "Official Ookla CLI not installed on host (install from speedtest.net/apps/cli)"
            res.duration = round(time.time() - t0, 2)
            return res

        try:
            if ookla_cli:
                cmd = [ookla_cli, "--format=json", "--accept-license", "--accept-gdpr"]
            else:
                cmd = [python_cli, "--json"]

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            while proc.poll() is None:
                if cancel_check and cancel_check():
                    proc.terminate()
                    res.status = "CANCELLED"
                    res.duration = time.time() - t0
                    return res
                time.sleep(0.2)

            stdout, stderr = proc.communicate(timeout=5.0)
            if proc.returncode != 0:
                raise RuntimeError(stderr.strip() or f"CLI exited with code {proc.returncode}")

            data = json.loads(stdout)
            if ookla_cli:
                # Official Ookla CLI format (bytes per second)
                dl_bps = data.get("download", {}).get("bandwidth", 0) * 8
                up_bps = data.get("upload", {}).get("bandwidth", 0) * 8
                res.download_mbps = round(dl_bps / 1_000_000.0, 1)
                res.upload_mbps = round(up_bps / 1_000_000.0, 1)
                res.ping_ms = round(data.get("ping", {}).get("latency", 0.0), 1)
                res.jitter_ms = round(data.get("ping", {}).get("jitter", 0.0), 2)
                server_info = data.get("server", {})
                res.metadata = {
                    "server": f"{server_info.get('name', 'Ookla')} ({server_info.get('location', '')})",
                    "isp": data.get("isp", ""),
                    "ip": data.get("interface", {}).get("externalIp", ""),
                    "endpoint": "https://speedtest.net",
                }
            else:
                # Python speedtest-cli format (bits per second)
                res.download_mbps = round(data.get("download", 0.0) / 1_000_000.0, 1)
                res.upload_mbps = round(data.get("upload", 0.0) / 1_000_000.0, 1)
                res.ping_ms = round(data.get("ping", 0.0), 1)
                res.metadata = {
                    "server": f"{data.get('server', {}).get('sponsor', 'Ookla')} ({data.get('server', {}).get('name', '')})",
                    "endpoint": "https://speedtest.net",
                }

            res.status = "SUCCESS"

        except Exception as e:
            res.status = "FAILED"
            res.error = str(e)

        res.duration = round(time.time() - t0, 2)
        return res

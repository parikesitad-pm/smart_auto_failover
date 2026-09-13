"""
AutoFailover 3.0 Core - nPerf Speed Test Provider Adapter
Author: parikesitad-pm
© 2026

Official nPerf Enterprise / SDK adapter.
"""

import os
import time
import shutil
import subprocess
from typing import Optional, Callable
from .base import BaseSpeedTestProvider, SpeedTestResult


class NPerfSpeedTestProvider(BaseSpeedTestProvider):
    """
    nPerf Speed Test Adapter.
    Adheres strictly to nPerf terms: requires official nPerf CLI or SDK license.
    """

    @property
    def name(self) -> str:
        return "nperf"

    @property
    def display_name(self) -> str:
        return "nPerf"

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

        # Check for local nPerf binary or API key
        nperf_cli = shutil.which("nperf") or shutil.which("nperf-cli")
        api_key = os.environ.get("NPERF_API_KEY")

        if not nperf_cli and not api_key:
            res.status = "UNAVAILABLE"
            res.error = "nPerf requires an official enterprise license or client (visit nperf.com)"
            res.duration = round(time.time() - t0, 2)
            return res

        # If official nperf binary is present
        if nperf_cli:
            try:
                proc = subprocess.Popen(
                    [nperf_cli, "--json"],
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
                if proc.returncode == 0:
                    res.status = "SUCCESS"
                    res.metadata = {"endpoint": "https://nperf.com"}
                else:
                    res.status = "FAILED"
                    res.error = stderr.strip() or f"nPerf exited with code {proc.returncode}"
            except Exception as e:
                res.status = "FAILED"
                res.error = str(e)
        else:
            res.status = "UNAVAILABLE"
            res.error = "nPerf SDK key detected, but native runner binary is not configured."

        res.duration = round(time.time() - t0, 2)
        return res

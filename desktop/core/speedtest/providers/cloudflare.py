"""
AutoFailover 3.0 Core - Cloudflare Speed Test Provider Adapter
Author: parikesitad-pm
© 2026

Official Cloudflare speed endpoint adapter.
"""

import time
import urllib.request
import urllib.error
from typing import Optional, Callable, List
from .base import BaseSpeedTestProvider, SpeedTestResult


class CloudflareSpeedTestProvider(BaseSpeedTestProvider):
    """
    Cloudflare Speed Test Adapter using official public endpoints:
    - https://speed.cloudflare.com/__down
    - https://speed.cloudflare.com/__up
    """

    @property
    def name(self) -> str:
        return "cloudflare"

    @property
    def display_name(self) -> str:
        return "Cloudflare"

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

        try:
            # 1. Measure Latency & RFC 3550 Jitter (3 samples)
            pings: List[float] = []
            for _ in range(3):
                if cancel_check and cancel_check():
                    res.status = "CANCELLED"
                    res.duration = time.time() - t0
                    return res

                s_time = time.monotonic()
                req = urllib.request.Request(
                    "https://speed.cloudflare.com/__down?bytes=0",
                    headers={"User-Agent": "AutoFailover/3.0", "Cache-Control": "no-cache"}
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    resp.read()
                elapsed_ms = (time.monotonic() - s_time) * 1000.0
                pings.append(elapsed_ms)

            avg_ping = sum(pings) / len(pings)
            jitter = 0.0
            if len(pings) >= 2:
                diffs = [abs(pings[i] - pings[i - 1]) for i in range(1, len(pings))]
                jitter = sum(diffs) / len(diffs)

            res.ping_ms = round(avg_ping, 1)
            res.jitter_ms = round(jitter, 2)

            if cancel_check and cancel_check():
                res.status = "CANCELLED"
                res.duration = time.time() - t0
                return res

            # 2. Measure Download Throughput (5MB chunk)
            dl_bytes = 5_000_000
            dl_req = urllib.request.Request(
                f"https://speed.cloudflare.com/__down?bytes={dl_bytes}",
                headers={"User-Agent": "AutoFailover/3.0", "Cache-Control": "no-cache"}
            )
            dl_start = time.monotonic()
            total_read = 0
            with urllib.request.urlopen(dl_req, timeout=8.0) as dl_resp:
                server_colo = dl_resp.headers.get("cf-ray", "").split("-")[-1] or "Edge"
                while True:
                    if cancel_check and cancel_check():
                        res.status = "CANCELLED"
                        res.duration = time.time() - t0
                        return res
                    chunk = dl_resp.read(65536)
                    if not chunk:
                        break
                    total_read += len(chunk)

            dl_duration = max(0.01, time.monotonic() - dl_start)
            dl_mbps = (total_read * 8.0) / (dl_duration * 1_000_000.0)
            res.download_mbps = round(dl_mbps, 1)

            if cancel_check and cancel_check():
                res.status = "CANCELLED"
                res.duration = time.time() - t0
                return res

            # 3. Measure Upload Throughput (1.5MB random bytes payload)
            up_bytes = 1_500_000
            payload = b"0" * up_bytes
            up_req = urllib.request.Request(
                "https://speed.cloudflare.com/__up",
                data=payload,
                headers={
                    "User-Agent": "AutoFailover/3.0",
                    "Content-Type": "application/octet-stream",
                    "Cache-Control": "no-cache",
                },
                method="POST"
            )
            up_start = time.monotonic()
            with urllib.request.urlopen(up_req, timeout=8.0) as up_resp:
                up_resp.read()
            up_duration = max(0.01, time.monotonic() - up_start)
            up_mbps = (up_bytes * 8.0) / (up_duration * 1_000_000.0)
            res.upload_mbps = round(up_mbps, 1)

            res.metadata = {
                "server": f"Cloudflare Edge ({server_colo})",
                "bytes_downloaded": total_read,
                "bytes_uploaded": up_bytes,
                "endpoint": "https://speed.cloudflare.com",
            }
            res.status = "SUCCESS"

        except urllib.error.URLError as e:
            res.status = "FAILED"
            res.error = f"Network connection failed: {e.reason}"
        except Exception as e:
            res.status = "FAILED"
            res.error = str(e)

        res.duration = round(time.time() - t0, 2)
        return res

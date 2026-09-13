"""
AutoFailover 3.0 Core - FAST.com Speed Test Provider Adapter
Author: parikesitad-pm
© 2026

FAST.com (Netflix Open Connect) adapter.
"""

import time
import json
import urllib.request
import urllib.error
from typing import Optional, Callable
from .base import BaseSpeedTestProvider, SpeedTestResult


class FastSpeedTestProvider(BaseSpeedTestProvider):
    """
    FAST.com Speed Test Adapter querying Netflix Open Connect endpoints.
    """

    @property
    def name(self) -> str:
        return "fast"

    @property
    def display_name(self) -> str:
        return "FAST.com"

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
            # 1. Query Fast.com API for available targets
            # Official Fast.com public web client token
            token = "YXNkZmFzZGxmbnNkYWZoYXNkZmhrYWxm"
            api_url = f"https://api.fast.com/netflix/speedtest/v2?https=true&token={token}&urlCount=3"
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "AutoFailover/3.0", "Accept": "application/json"}
            )

            p_start = time.monotonic()
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            ping_ms = (time.monotonic() - p_start) * 1000.0
            res.ping_ms = round(ping_ms, 1)

            targets = data.get("targets", [])
            client_info = data.get("client", {})
            if not targets:
                raise ValueError("No FAST.com test targets returned by Netflix API")

            target_url = targets[0].get("url")
            server_loc = targets[0].get("name", "Netflix Open Connect")

            if cancel_check and cancel_check():
                res.status = "CANCELLED"
                res.duration = time.time() - t0
                return res

            # 2. Download from Netflix Open Connect server (up to 4MB)
            dl_req = urllib.request.Request(
                f"{target_url}/range/0-4194304",
                headers={"User-Agent": "AutoFailover/3.0"}
            )
            dl_start = time.monotonic()
            total_read = 0
            with urllib.request.urlopen(dl_req, timeout=8.0) as dl_resp:
                while total_read < 4_194_304:
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

            res.metadata = {
                "server": server_loc,
                "client_ip": client_info.get("ip", "--"),
                "isp": client_info.get("asn", "--"),
                "bytes_downloaded": total_read,
                "endpoint": "https://fast.com",
            }
            res.status = "SUCCESS"

        except urllib.error.HTTPError as e:
            res.status = "FAILED"
            res.error = f"FAST.com HTTP error {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            res.status = "FAILED"
            res.error = f"FAST.com network error: {e.reason}"
        except Exception as e:
            res.status = "FAILED"
            res.error = str(e)

        res.duration = round(time.time() - t0, 2)
        return res

import os
import platform
import re
import subprocess
import time
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from .models import PingResult


IS_WINDOWS = (platform.system() == "Windows")
CREATE_NO_WINDOW = 0x08000000 if IS_WINDOWS else 0


class PingProbe:
    """Probes interface health using OS-specific ping bound to a specific source IPv4 address."""

    @staticmethod
    def ping_interface(
        source_ip: str,
        target: str = "1.1.1.1",
        timeout_ms: int = 800,
    ) -> PingResult:
        """
        Execute a single ICMP ping bound strictly to the given source IPv4 address.
        - Windows: ping -n 1 -w <timeout_ms> -S <source_ip> <target>
        - macOS:   ping -c 1 -W <timeout_ms> -S <source_ip> <target>
        """
        if not source_ip or source_ip.startswith("169.254."):
            return PingResult(
                success=False,
                latency_ms=0.0,
                error="No valid IPv4 address assigned to interface",
                target=target,
            )

        if IS_WINDOWS:
            cmd = [
                "ping",
                "-n", "1",
                "-w", str(timeout_ms),
                "-S", source_ip,
                target,
            ]
        else:
            # macOS / BSD ping
            cmd = [
                "ping",
                "-c", "1",
                "-W", str(timeout_ms),
                "-S", source_ip,
                target,
            ]

        t0 = time.perf_counter()
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=(timeout_ms / 1000.0) + 0.8,
                creationflags=CREATE_NO_WINDOW,
            )
            elapsed_total_ms = (time.perf_counter() - t0) * 1000.0
            stdout = res.stdout

            if res.returncode == 0:
                # Match: time=33ms, time=14.32 ms, time<1ms
                match = re.search(r"time[=<]([0-9.]+)\s*ms", stdout, re.IGNORECASE)
                if match:
                    latency = float(match.group(1))
                    return PingResult(
                        success=True,
                        latency_ms=latency,
                        error="",
                        target=target,
                    )
                elif "time<1ms" in stdout.lower():
                    return PingResult(
                        success=True,
                        latency_ms=0.5,
                        error="",
                        target=target,
                    )
                else:
                    return PingResult(
                        success=True,
                        latency_ms=round(elapsed_total_ms, 1),
                        error="",
                        target=target,
                    )

            # Check error patterns (Windows & macOS)
            lower_out = stdout.lower()
            if "timed out" in lower_out or "request timeout" in lower_out:
                return PingResult(success=False, latency_ms=0.0, error="Request timed out (RTO)", target=target)
            elif "unreachable" in lower_out:
                return PingResult(success=False, latency_ms=0.0, error="Destination unreachable", target=target)
            elif "general failure" in lower_out:
                return PingResult(success=False, latency_ms=0.0, error="General hardware/link failure", target=target)
            elif "cannot assign requested address" in lower_out or "invalid source" in lower_out:
                return PingResult(success=False, latency_ms=0.0, error="Source IP binding failed", target=target)
            else:
                last_line = stdout.strip().splitlines()[-1] if stdout.strip() else "Ping packet lost"
                return PingResult(
                    success=False,
                    latency_ms=0.0,
                    error=last_line,
                    target=target,
                )

        except subprocess.TimeoutExpired:
            return PingResult(
                success=False,
                latency_ms=0.0,
                error=f"Timeout exceeded (> {timeout_ms}ms)",
                target=target,
            )
        except Exception as e:
            return PingResult(
                success=False,
                latency_ms=0.0,
                error=f"Execution error: {e}",
                target=target,
            )


class ConcurrentPingManager:
    """Manages concurrent ICMP health checks across multiple interfaces."""

    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PingProbe")

    def probe_interface(self, source_ip: str, target: str, timeout_ms: int):
        return self.executor.submit(PingProbe.ping_interface, source_ip, target, timeout_ms)

    def shutdown(self):
        self.executor.shutdown(wait=False)

"""
AutoFailover 3.0 Core - Speedtest Runner (Modular 4-Provider Abstraction)
Author: parikesitad-pm
© 2026
"""

import time
import threading
from enum import Enum
from typing import List, Dict, Any, Optional, Callable

from .providers.base import SpeedTestResult, BaseSpeedTestProvider
from .providers.cloudflare import CloudflareSpeedTestProvider
from .providers.fast import FastSpeedTestProvider
from .providers.ookla import OoklaSpeedTestProvider
from .providers.nperf import NPerfSpeedTestProvider


class SpeedtestProvider(str, Enum):
    CLOUDFLARE = "cloudflare"
    FAST = "fast"
    OOKLA = "ookla"
    NPERF = "nperf"


class SpeedtestMode(str, Enum):
    CUSTOM = "custom"
    BULK = "bulk"


class SpeedtestRunner:
    """
    On-demand multi-provider speedtest execution queue.
    Providers: Cloudflare, FAST.com, Ookla Speedtest, nPerf.
    Modes: Single Test, Sequential Bulk Test.
    Rule: Never continuous. Never runs providers concurrently. Results MUST NOT directly trigger failover.
    """

    def __init__(self):
        self._is_running = False
        self._cancel_requested = False
        self._lock = threading.Lock()

        # Initialize isolated provider adapters
        self.providers: Dict[str, BaseSpeedTestProvider] = {
            "cloudflare": CloudflareSpeedTestProvider(),
            "fast": FastSpeedTestProvider(),
            "fast_com": FastSpeedTestProvider(),
            "ookla": OoklaSpeedTestProvider(),
            "nperf": NPerfSpeedTestProvider(),
        }

    @property
    def is_running(self) -> bool:
        return self._is_running

    def cancel(self):
        """Requests cancellation of ongoing single or bulk test."""
        self._cancel_requested = True

    def run_test(
        self,
        provider: SpeedtestProvider,
        interface_id: str = "default",
        source_ip: Optional[str] = None,
        callback: Optional[Callable[[SpeedTestResult], None]] = None,
    ) -> SpeedTestResult:
        """Execute an on-demand speedtest via specified provider."""
        return self.run_single_test(
            provider_name=provider.value if isinstance(provider, SpeedtestProvider) else str(provider),
            interface_id=interface_id,
            source_ip=source_ip,
            callback=callback,
        )

    def run_single_test(
        self,
        provider_name: str,
        interface_id: str = "default",
        source_ip: Optional[str] = None,
        callback: Optional[Callable[[SpeedTestResult], None]] = None,
    ) -> SpeedTestResult:
        """Execute a single on-demand test by provider name."""
        with self._lock:
            self._is_running = True
            self._cancel_requested = False

        try:
            key = str(provider_name).strip().lower()
            adapter = self.providers.get(key) or self.providers.get("cloudflare")

            def _is_cancelled():
                return self._cancel_requested

            res = adapter.run_benchmark(
                interface=interface_id,
                source_ip=source_ip,
                cancel_check=_is_cancelled,
            )

            if callback:
                callback(res)

            return res
        finally:
            with self._lock:
                self._is_running = False

    def run_bulk_tests(
        self,
        interface_id: str = "default",
        source_ip: Optional[str] = None,
        on_progress: Optional[Callable[[int, int, str, str, Optional[SpeedTestResult]], None]] = None,
    ) -> List[SpeedTestResult]:
        """
        Execute controlled sequential benchmark across all 4 providers.
        Never runs providers concurrently. Survives individual provider failures.
        """
        with self._lock:
            self._is_running = True
            self._cancel_requested = False

        results: List[SpeedTestResult] = []
        bulk_keys = ["cloudflare", "fast", "ookla", "nperf"]
        total = len(bulk_keys)

        def _is_cancelled():
            return self._cancel_requested

        try:
            for idx, key in enumerate(bulk_keys, start=1):
                if self._cancel_requested:
                    cancelled_res = SpeedTestResult(
                        provider=key,
                        interface=interface_id,
                        status="CANCELLED",
                        error="Bulk test was cancelled by user",
                    )
                    results.append(cancelled_res)
                    if on_progress:
                        on_progress(idx, total, key, "CANCELLED", cancelled_res)
                    continue

                adapter = self.providers.get(key)
                if not adapter:
                    continue

                if on_progress:
                    on_progress(idx, total, key, "RUNNING", None)

                # Execute sequential benchmark
                try:
                    res = adapter.run_benchmark(
                        interface=interface_id,
                        source_ip=source_ip,
                        cancel_check=_is_cancelled,
                    )
                except Exception as e:
                    res = SpeedTestResult(
                        provider=key,
                        interface=interface_id,
                        status="FAILED",
                        error=f"Unexpected adapter error: {e}",
                    )

                results.append(res)

                if on_progress:
                    on_progress(idx, total, key, res.status, res)

                # Small cooldown between providers to allow sockets to settle
                if idx < total and not self._cancel_requested:
                    time.sleep(0.3)

            return results
        finally:
            with self._lock:
                self._is_running = False


# Canonical stable aliases
SpeedtestResult = SpeedTestResult
SpeedTestRunner = SpeedtestRunner
SpeedTestProvider = SpeedtestProvider
SpeedTestMode = SpeedtestMode


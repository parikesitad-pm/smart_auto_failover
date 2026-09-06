import time
from typing import Dict, List, Optional
import psutil

from core.models import TrafficStats


class TrafficMonitor:
    """
    Tracks real-time per-adapter bandwidth consumption (Download / Upload kbps)
    and RFC 3550 statistical latency Jitter.
    """

    def __init__(self, history_len: int = 30):
        self.history_len = history_len
        self._last_snapshot_time: float = time.time()
        self._last_io: Dict[str, psutil._common.snetio] = {}
        self._last_latency: Dict[str, float] = {}
        self._jitter: Dict[str, float] = {}

        # History of download and upload kbps per interface for charting
        self.download_history: Dict[str, List[float]] = {}
        self.upload_history: Dict[str, List[float]] = {}

        # Initialize first snapshot
        try:
            self._last_io = psutil.net_io_counters(pernic=True)
        except Exception:
            self._last_io = {}

    def update(self) -> Dict[str, TrafficStats]:
        """Sample current IO counters and compute kbps and jitter."""
        now = time.time()
        elapsed = max(0.1, now - self._last_snapshot_time)
        self._last_snapshot_time = now

        try:
            current_io = psutil.net_io_counters(pernic=True)
        except Exception:
            current_io = {}

        stats_map: Dict[str, TrafficStats] = {}

        for alias, curr in current_io.items():
            prev = self._last_io.get(alias)
            if prev:
                # Handle possible counter wrap-around
                delta_sent = max(0, curr.bytes_sent - prev.bytes_sent)
                delta_recv = max(0, curr.bytes_recv - prev.bytes_recv)

                bytes_sent_sec = delta_sent / elapsed
                bytes_recv_sec = delta_recv / elapsed

                download_kbps = (bytes_recv_sec * 8.0) / 1000.0
                upload_kbps = (bytes_sent_sec * 8.0) / 1000.0
            else:
                bytes_sent_sec = 0.0
                bytes_recv_sec = 0.0
                download_kbps = 0.0
                upload_kbps = 0.0

            # Store in history
            if alias not in self.download_history:
                self.download_history[alias] = []
                self.upload_history[alias] = []

            self.download_history[alias].append(download_kbps)
            self.upload_history[alias].append(upload_kbps)

            if len(self.download_history[alias]) > self.history_len:
                self.download_history[alias].pop(0)
                self.upload_history[alias].pop(0)

            stats_map[alias] = TrafficStats(
                alias=alias,
                bytes_sent_sec=bytes_sent_sec,
                bytes_recv_sec=bytes_recv_sec,
                download_kbps=round(download_kbps, 1),
                upload_kbps=round(upload_kbps, 1),
                jitter_ms=round(self._jitter.get(alias, 0.0), 2),
            )

        self._last_io = current_io
        return stats_map

    def record_latency_sample(self, alias: str, latency_ms: float) -> float:
        """
        Record a new ICMP latency sample and compute RFC 3550 rolling jitter:
        J = J + (|D(i-1, i)| - J) / 16
        """
        if latency_ms <= 0:
            return self._jitter.get(alias, 0.0)

        prev = self._last_latency.get(alias)
        current_j = self._jitter.get(alias, 0.0)

        if prev is not None and prev > 0:
            d = abs(latency_ms - prev)
            new_j = current_j + (d - current_j) / 16.0
            self._jitter[alias] = new_j
        else:
            self._jitter[alias] = 0.0

        self._last_latency[alias] = latency_ms
        return self._jitter[alias]

    def get_stats(self, alias: str) -> TrafficStats:
        dl_list = self.download_history.get(alias, [0.0])
        up_list = self.upload_history.get(alias, [0.0])
        return TrafficStats(
            alias=alias,
            download_kbps=round(dl_list[-1] if dl_list else 0.0, 1),
            upload_kbps=round(up_list[-1] if up_list else 0.0, 1),
            jitter_ms=round(self._jitter.get(alias, 0.0), 2),
        )

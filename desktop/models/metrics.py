"""
AutoFailover 3.0 Models - Path Metrics & RFC 3550 Jitter Tracking
Author: parikesitad-pm
© 2026
"""

import time
from typing import List, Tuple
from pydantic import BaseModel, Field


class PathMetrics(BaseModel):
    """
    Live telemetry metrics for a network interface path.
    """
    latency_ms: float = 0.0
    jitter_ms: float = 0.0          # RFC 3550 statistical interarrival jitter
    packet_loss_pct: float = 0.0
    samples_count: int = 0
    last_probe_timestamp: float = Field(default_factory=time.time)
    health_index: int = 0           # Composite 0-100 score

    # Internal state for RFC 3550 calculation: (send_time, recv_time)
    _last_transit: float = 0.0

    def reset(self) -> None:
        """Reset metrics to zero when link drops."""
        self.latency_ms = 0.0
        self.jitter_ms = 0.0
        self.packet_loss_pct = 100.0
        self.samples_count = 0
        self.health_index = 0
        self.last_probe_timestamp = time.time()
